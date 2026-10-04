"""Onda 2A integração — par coeso contracts+corporate atrás de flags."""

from app.crud import run as run_crud
from app.models.analysis_run import AnalysisRun
from app.models.document import Document
from app.models.document_revision import DocumentRevision


def _document(db_session, make_user):
    user = make_user()
    document = Document(
        user_id=user.id, filename="p2a.pdf", file_path="/tmp/p2a.pdf",
        content_type="application/pdf", status="uploaded",
    )
    db_session.add(document)
    db_session.commit()
    db_session.refresh(document)
    return user, document


def _run(db_session, user, document):
    rev = DocumentRevision(
        document_id=document.id, user_id=user.id,
        sha256="sha-2a", pages_total=6,
    )
    db_session.add(rev)
    db_session.commit()
    db_session.refresh(rev)
    run = AnalysisRun(
        user_id=user.id, document_id=document.id,
        status=AnalysisRun.RUNNING,
        snapshot={
            "areas": ["contracts", "corporate"],
            "document_ids": [str(document.id)],
            "revision_ids": [str(rev.id)],
            "fixture": {
                "claims": [
                    {"id": "claim-1", "title": "Reajuste do contrato social",
                     "source_refs": ["src-1"]},
                ],
                "facts": [
                    {"id": "f1", "statement": "Aditivo com cláusula de reajuste",
                     "asserted_by": "parte-A", "epistemic_status": "documented",
                     "source_refs": ["src-1"]},
                    {"id": "f2", "statement": "Assembleia aprovou quotas",
                     "asserted_by": "parte-A", "epistemic_status": "documented",
                     "source_refs": ["src-2"]},
                ],
                "evidence": [{"id": "ev1", "presence_status": "examined"}],
                "legal_references": [],
                "visuals": [],
                "sources": [{"id": "src-1", "page_number": 1},
                            {"id": "src-2", "page_number": 2}],
                "coverage": {"pages_total": 6, "pages_extracted": 6},
            },
        },
    )
    db_session.add(run)
    db_session.commit()
    db_session.refresh(run)
    return run


def _enable_2a(monkeypatch):
    from app.core.config import settings

    for flag in ("DOSSIER_MODULE_CONTRACTS", "DOSSIER_MODULE_CORPORATE"):
        monkeypatch.setattr(settings, flag, True)


def test_pair_shares_entities_without_duplication(db_session, make_user, monkeypatch):
    from app.core.pipeline.orchestrator import run_universal_pipeline

    _enable_2a(monkeypatch)
    user, document = _document(db_session, make_user)
    run = _run(db_session, user, document)
    artifact = run_universal_pipeline(db_session, run_id=run.id)
    assert artifact is not None
    content = artifact.content
    assert set(content["module_results"]) == {"contracts", "corporate"}
    assert [c["id"] for c in content["claims"]] == ["claim-1"]
    assert [f["id"] for f in content["facts"]] == ["f1", "f2"]
    active = {a["module_id"] for a in content["module_activations"]
              if a["status"] == "active"}
    assert {"universal", "contracts", "corporate"} <= active


def test_flags_off_keep_universal_intact(db_session, make_user):
    from app.core.pipeline.orchestrator import run_universal_pipeline

    user, document = _document(db_session, make_user)
    run = _run(db_session, user, document)
    artifact = run_universal_pipeline(db_session, run_id=run.id)
    assert artifact is not None
    assert artifact.content["module_results"] == {}
    assert [c["id"] for c in artifact.content["claims"]] == ["claim-1"]
    db_session.refresh(run)
    assert run_crud.get_published_artifact(db_session, run=run) is not None


def test_failing_pair_module_does_not_sink_other(db_session, make_user, monkeypatch):
    from app.core.pipeline.orchestrator import run_universal_pipeline
    from app.modules.contracts import ContractsModule

    def _boom(self, case_data):
        raise RuntimeError("provedor do módulo caiu")

    monkeypatch.setattr(ContractsModule, "analyze", _boom)
    _enable_2a(monkeypatch)
    user, document = _document(db_session, make_user)
    run = _run(db_session, user, document)
    artifact = run_universal_pipeline(db_session, run_id=run.id)
    assert artifact is not None
    content = artifact.content
    assert content["module_results"]["contracts"]["status"] == "blocked"
    assert content["module_results"]["corporate"]["status"] in ("complete", "partial")
    assert [c["id"] for c in content["claims"]] == ["claim-1"]
