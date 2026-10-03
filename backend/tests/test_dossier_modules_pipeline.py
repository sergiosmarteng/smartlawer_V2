"""Onda 1 integração — módulos no pipeline atrás de flags."""

from app.crud import run as run_crud
from app.models.analysis_run import AnalysisRun
from app.models.document import Document
from app.models.document_revision import DocumentRevision


def _document(db_session, make_user):
    user = make_user()
    document = Document(
        user_id=user.id, filename="p1b.pdf", file_path="/tmp/p1b.pdf",
        content_type="application/pdf", status="uploaded",
    )
    db_session.add(document)
    db_session.commit()
    db_session.refresh(document)
    return user, document


def _run(db_session, user, document, areas):
    rev = DocumentRevision(
        document_id=document.id, user_id=user.id,
        sha256="sha-1b", pages_total=4,
    )
    db_session.add(rev)
    db_session.commit()
    db_session.refresh(rev)
    run = AnalysisRun(
        user_id=user.id, document_id=document.id,
        status=AnalysisRun.RUNNING,
        snapshot={
            "areas": areas,
            "document_ids": [str(document.id)],
            "revision_ids": [str(rev.id)],
            "fixture": {
                "claims": [
                    {"id": "claim-1", "title": "Guarda", "source_refs": ["src-1"]},
                    {"id": "claim-2", "title": "Cobrança", "source_refs": ["src-2"]},
                ],
                "facts": [
                    {"id": "f1", "statement": "Filho menor sob guarda",
                     "asserted_by": "parte-A", "epistemic_status": "documented",
                     "source_refs": ["src-1"]},
                    {"id": "f2", "statement": "Contrato com obrigação de pagamento",
                     "asserted_by": "parte-A", "epistemic_status": "documented",
                     "source_refs": ["src-2"]},
                ],
                "evidence": [{"id": "ev1", "presence_status": "examined"}],
                "legal_references": [],
                "visuals": [],
                "sources": [{"id": "src-1", "page_number": 1},
                            {"id": "src-2", "page_number": 2}],
                "coverage": {"pages_total": 4, "pages_extracted": 4},
            },
        },
    )
    db_session.add(run)
    db_session.commit()
    db_session.refresh(run)
    return run


def test_multiarea_modules_without_duplication(db_session, make_user, monkeypatch):
    from app.core.config import settings
    from app.core.pipeline.orchestrator import run_universal_pipeline

    for flag in ("DOSSIER_MODULE_FAMILY", "DOSSIER_MODULE_CIVIL_PROCEDURE"):
        monkeypatch.setattr(settings, flag, True)

    user, document = _document(db_session, make_user)
    run = _run(db_session, user, document, ["family", "civil_procedure"])
    artifact = run_universal_pipeline(db_session, run_id=run.id)
    assert artifact is not None
    content = artifact.content
    assert set(content["module_results"]) == {"family", "civil_procedure"}
    # Núcleo intacto: sem duplicação de pedidos/fatos.
    assert [c["id"] for c in content["claims"]] == ["claim-1", "claim-2"]
    assert [f["id"] for f in content["facts"]] == ["f1", "f2"]
    active = {a["module_id"] for a in content["module_activations"]
              if a["status"] == "active"}
    assert {"universal", "family", "civil_procedure"} <= active


def test_flags_off_keep_universal_intact(db_session, make_user):
    from app.core.pipeline.orchestrator import run_universal_pipeline

    user, document = _document(db_session, make_user)
    run = _run(db_session, user, document, ["family", "civil_procedure"])
    artifact = run_universal_pipeline(db_session, run_id=run.id)
    assert artifact is not None
    assert artifact.content["module_results"] == {}
    assert [c["id"] for c in artifact.content["claims"]] == ["claim-1", "claim-2"]
    db_session.refresh(run)
    assert run_crud.get_published_artifact(db_session, run=run) is not None
