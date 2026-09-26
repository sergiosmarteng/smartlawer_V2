"""V2 T13 — operação e proteção (aceite do plano)."""

import io

import app.tasks.document_tasks as tasks
from app.crud import run as run_crud
from app.models.analysis import Analysis
from app.models.analysis_artifact import AnalysisArtifact
from app.models.analysis_run import AnalysisRun
from app.models.audit_event import AuditEvent
from app.models.document import Document
from app.models.document_chunk import DocumentChunk


def _real_pdf(pages=1):
    import fitz

    doc = fitz.open()
    for i in range(pages):
        page = doc.new_page()
        page.insert_text((72, 72), f"Pagina {i} de conteudo.")
    buf = io.BytesIO()
    doc.save(buf)
    doc.close()
    return buf.getvalue()


def test_upload_rejects_oversize_and_overlong(
    client, make_user, auth_headers_for, monkeypatch
):
    from app.api.routes import documents

    user = make_user(email="lim@example.com", username="lim")
    headers = auth_headers_for(user)

    monkeypatch.setattr(documents.settings, "MAX_UPLOAD_MB", 0)
    big = client.post(
        "/api/v1/documents/upload", headers=headers,
        files={"file": ("p.pdf", _real_pdf(), "application/pdf")},
    )
    assert big.status_code == 413

    monkeypatch.setattr(documents.settings, "MAX_UPLOAD_MB", 50)
    monkeypatch.setattr(documents.settings, "MAX_PDF_PAGES", 1)
    long = client.post(
        "/api/v1/documents/upload", headers=headers,
        files={"file": ("p.pdf", _real_pdf(pages=2), "application/pdf")},
    )
    assert long.status_code == 413


def test_ops_summary_exposes_limits(client, db_session, make_user, auth_headers_for):
    admin = make_user(email="adm@example.com", username="adm")
    admin.role = "admin"
    db_session.commit()
    resp = client.get("/api/v1/ops/summary", headers=auth_headers_for(admin))
    assert resp.status_code == 200
    assert resp.json()["limits"]["max_upload_mb"] >= 0


def _seed_full_document(db_session, make_user, tmp_path):
    from app.crud import extraction as crud_extraction
    from app.models.document_figure import DocumentFigure
    from app.models.document_revision import DocumentRevision
    from app.models.generated_document import GeneratedDocument

    user = make_user()
    pdf = tmp_path / "full.pdf"
    pdf.write_bytes(_real_pdf())
    document = Document(
        user_id=user.id, filename="full.pdf", file_path=str(pdf),
        content_type="application/pdf", status="completed",
    )
    db_session.add(document)
    db_session.flush()
    analysis = Analysis(document_id=document.id, summary="s")
    db_session.add(analysis)
    db_session.flush()
    db_session.add(
        GeneratedDocument(user_id=user.id, document_id=document.id,
                          analysis_id=analysis.id, file_path=str(pdf), version=1)
    )
    db_session.add(
        DocumentChunk(document_id=document.id, user_id=user.id, chunk_index=0,
                      content="c", embedding=None)
    )
    fig_path = tmp_path / "fig.png"
    fig_path.write_bytes(b"png")
    db_session.add(
        DocumentFigure(document_id=document.id, user_id=user.id, file_path=str(fig_path))
    )
    revision, _ = crud_extraction.get_or_create_revision(
        db_session, document_id=document.id, user_id=user.id, file_sha256="abc"
    )
    crud_extraction.replace_source_blocks(
        db_session, revision=revision,
        pages=[{"page_number": 1, "method": "pymupdf",
                "blocks": [{"id": "b1", "type": "text", "reading_order": 0,
                            "original_text": "t", "normalized_text": "t"}]}],
    )
    run = run_crud.create_run(db_session, user_id=user.id, document_id=document.id)
    run_crud.publish_artifact(db_session, run=run, content={})
    run_crud.add_source_reference(db_session, run=run, page_number=1)
    db_session.commit()
    return user, document


def test_delete_cascades_everything_with_audit(
    client, db_session, make_user, auth_headers_for, tmp_path
):
    user, document = _seed_full_document(db_session, make_user, tmp_path)
    headers = auth_headers_for(user)
    resp = client.delete(f"/api/v1/documents/{document.id}", headers=headers)
    assert resp.status_code == 204
    assert db_session.query(Document).count() == 0
    assert db_session.query(Analysis).count() == 0
    assert db_session.query(DocumentChunk).count() == 0
    assert db_session.query(AnalysisRun).count() == 0
    assert db_session.query(AnalysisArtifact).count() == 0
    assert not (tmp_path / "full.pdf").exists()
    audit = (
        db_session.query(AuditEvent)
        .filter_by(event_type=AuditEvent.DOCUMENT_DELETED)
        .one()
    )
    assert audit.meta["chunks"] == 1


def test_delete_blocks_cross_user(client, db_session, make_user, auth_headers_for, tmp_path):
    user, document = _seed_full_document(db_session, make_user, tmp_path)
    intruder = make_user(email="del-int@example.com", username="del-int")
    resp = client.delete(
        f"/api/v1/documents/{document.id}", headers=auth_headers_for(intruder)
    )
    assert resp.status_code == 404
    assert db_session.query(Document).count() == 1


def _run_task(document_id, pdf_path):
    target = getattr(tasks.process_pdf_task, "func", None)
    if target is not None:

        class _FakeTask:
            max_retries = 3

            def __init__(self):
                self.request = type("Req", (), {"retries": 0})()
                self.retried = False

            def retry(self, exc=None, countdown=None):
                self.retried = True
                raise RuntimeError("retry")

        task = _FakeTask()
        try:
            target(task, str(document_id), pdf_path)
        except RuntimeError:
            pass
        return task
    try:
        # Celery real: .run é bound; retry re-levanta a original.
        tasks.process_pdf_task.run(str(document_id), pdf_path)
    except Exception:
        pass
    return None


def test_transient_failure_retries_without_error_state(
    monkeypatch, db_session, make_user, tmp_path
):
    user = make_user()
    pdf = tmp_path / "t.pdf"
    pdf.write_bytes(b"%PDF-1.4 stub")
    document = Document(
        user_id=user.id, filename="t.pdf", file_path=str(pdf),
        content_type="application/pdf", status="uploaded",
    )
    db_session.add(document)
    db_session.commit()

    monkeypatch.setattr(
        "app.tasks.document_tasks.PDFExtractor.extract_text",
        staticmethod(lambda file_path: (_ for _ in ()).throw(RuntimeError("transient"))),
    )
    task = _run_task(document.id, str(pdf))
    db_session.refresh(document)
    assert document.status == Document.STATUS_PROCESSING
    assert task is None or getattr(task, "retried", True)


def test_duplicate_delivery_is_idempotent(monkeypatch, db_session, make_user, tmp_path):
    user = make_user()
    pdf = tmp_path / "d.pdf"
    pdf.write_bytes(b"%PDF-1.4 stub")
    document = Document(
        user_id=user.id, filename="d.pdf", file_path=str(pdf),
        content_type="application/pdf", status="uploaded",
    )
    db_session.add(document)
    db_session.commit()

    monkeypatch.setattr(
        tasks.PDFExtractor, "extract_text", staticmethod(lambda file_path: "TEXTO")
    )
    monkeypatch.setattr(tasks.settings, "DOCLING_ENABLED", False)

    def fake_analyze(self, text, strategy_prompt=None):
        return {"summary": "resumo", "requests": ["p1"]}

    monkeypatch.setattr(
        "app.core.ai_engine.LegalAnalyzer.analyze_petition", fake_analyze
    )
    _run_task(document.id, str(pdf))
    _run_task(document.id, str(pdf))
    db_session.refresh(document)
    assert document.status == Document.STATUS_COMPLETED
    assert db_session.query(Analysis).filter_by(document_id=document.id).count() == 1
    runs = (
        db_session.query(AnalysisRun).filter_by(document_id=document.id).all()
    )
    assert len(runs) == 1
    assert (
        db_session.query(AnalysisArtifact).filter_by(run_id=runs[0].id).count() == 1
    )
