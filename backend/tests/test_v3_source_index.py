"""V3 source index — pipeline persiste SourceReference para cada fonte do artefato."""

from app.crud import run as run_crud
from app.models.analysis_run import AnalysisRun
from app.models.document import Document
from app.models.document_revision import DocumentRevision
from app.models.source_reference import SourceReference


def _document(db_session, make_user):
    user = make_user()
    document = Document(
        user_id=user.id, filename="p-si.pdf", file_path="/tmp/p-si.pdf",
        content_type="application/pdf", status="uploaded",
    )
    db_session.add(document)
    db_session.commit()
    db_session.refresh(document)
    return user, document


def _fixture_snapshot(doc, rev):
    return {
        "case_id": None,
        "document_ids": [str(doc.id)],
        "revision_ids": [str(rev.id)],
        "sha256": [rev.sha256],
        "fixture": {
            "claims": [{"id": "claim-1", "title": "Guarda",
                        "source_refs": ["src-1"]}],
            "facts": [{"id": "f1", "statement": "Genitores separados",
                       "asserted_by": "parte-A", "source_refs": ["src-1"]}],
            "evidence": [],
            "legal_references": [],
            "visuals": [],
            "sources": [{"id": "src-1", "page_number": 3,
                         "verification_status": "matched"}],
            "coverage": {"pages_total": 2, "pages_extracted": 2},
        },
    }


def _run_with_fixture(db_session, user, document):
    rev = DocumentRevision(
        document_id=document.id, user_id=user.id,
        sha256="sha-si", pages_total=2,
    )
    db_session.add(rev)
    db_session.commit()
    db_session.refresh(rev)
    run = AnalysisRun(
        user_id=user.id, document_id=document.id,
        status=AnalysisRun.RUNNING, snapshot=_fixture_snapshot(document, rev),
    )
    db_session.add(run)
    db_session.commit()
    db_session.refresh(run)
    return run


def test_pipeline_persists_source_rows(db_session, make_user):
    from app.core.pipeline.orchestrator import run_universal_pipeline

    user, document = _document(db_session, make_user)
    run, _ = _run_with_fixture(db_session, user, document), None
    artifact = run_universal_pipeline(db_session, run_id=run.id)
    assert artifact is not None
    rows = (db_session.query(SourceReference)
            .filter(SourceReference.run_id == run.id).all())
    assert len(rows) == 1
    ref = rows[0]
    assert ref.user_id == user.id
    assert ref.page_number == 3
    assert ref.block_id == "src-1"
    assert ref.verification_status == "matched"
    assert (ref.extra or {}).get("source_id") == "src-1"


def test_sources_endpoint_lists_indexed_rows(client, db_session, make_user, auth_headers_for):
    from app.core.pipeline.orchestrator import run_universal_pipeline

    user, document = _document(db_session, make_user)
    run, _ = _run_with_fixture(db_session, user, document), None
    artifact = run_universal_pipeline(db_session, run_id=run.id)
    assert artifact is not None
    headers = auth_headers_for(user)
    resp = client.get(f"/api/v2/analyses/{artifact.id}/sources", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]["page_number"] == 3
    assert body[0]["document_id"] == str(document.id)
    one = client.get(f"/api/v2/sources/{body[0]['id']}", headers=headers)
    assert one.status_code == 200
    assert one.json()["page_number"] == 3
