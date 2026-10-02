"""Onda 0 Task 11 — pipeline universal em vez de coerção legada."""

import pytest

from app.crud import run as run_crud
from app.models.analysis_run import AnalysisRun
from app.models.document import Document
from app.models.document_revision import DocumentRevision


def _document(db_session, make_user):
    user = make_user()
    document = Document(
        user_id=user.id, filename="p11.pdf", file_path="/tmp/p11.pdf",
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
            "evidence": [{"id": "ev1", "presence_status": "examined",
                          "location_refs": ["src-1"]}],
            "legal_references": [{"id": "lr1", "literal_citation": "CC art. 1.584"}],
            "visuals": [{"id": "vis-1", "document_id": str(doc.id),
                         "revision_id": str(rev.id), "page_number": 1,
                         "source_ref": "src-1"}],
            "sources": [{"id": "src-1", "page_number": 1}],
            "coverage": {"pages_total": 2, "pages_extracted": 2},
        },
    }


def _run_with_fixture(db_session, user, document):
    rev = DocumentRevision(
        document_id=document.id, user_id=user.id,
        sha256="sha-p11", pages_total=2,
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
    return run, rev


def test_pipeline_publishes_v3_without_legacy_coercion(db_session, make_user, monkeypatch):
    """Pipeline V3 publica schema 3.0 com todas as seções — sem coerce."""
    import app.tasks.document_tasks as tasks

    def _boom(*args, **kwargs):
        raise AssertionError("coerce_legacy_analysis não pode rodar no caminho V3")

    monkeypatch.setattr(tasks, "coerce_legacy_analysis", _boom)

    from app.core.pipeline.orchestrator import run_universal_pipeline

    user, document = _document(db_session, make_user)
    run, _ = _run_with_fixture(db_session, user, document)
    artifact = run_universal_pipeline(db_session, run_id=run.id)
    assert artifact is not None
    assert artifact.schema_version == "3.0"
    content = artifact.content
    assert content["claims"] and content["facts"] and content["evidence"]
    assert content["legal_references"] and content["visuals"]
    assert content["coverage"]["pages_total"] > 0
    assert artifact.status in ("completed", "partial")


def test_pipeline_retries_from_first_incomplete_stage(db_session, make_user):
    from app.core.pipeline.orchestrator import run_universal_pipeline
    from app.crud.stage_run import start_stage

    user, document = _document(db_session, make_user)
    run, _ = _run_with_fixture(db_session, user, document)
    # Simula interrupção após ingestion.
    start_stage(db_session, run=run, stage="ingestion", attempt=1)
    from app.crud.stage_run import finish_stage
    from app.models.analysis_stage_run import AnalysisStageRun

    sr = (
        db_session.query(AnalysisStageRun)
        .filter(AnalysisStageRun.run_id == run.id, AnalysisStageRun.stage == "ingestion")
        .one()
    )
    finish_stage(db_session, stage_run=sr)
    artifact = run_universal_pipeline(db_session, run_id=run.id)
    assert artifact is not None
    assert artifact.schema_version == "3.0"


def test_pipeline_keeps_snapshot_revision_after_document_change(db_session, make_user):
    from app.core.pipeline.orchestrator import run_universal_pipeline

    user, document = _document(db_session, make_user)
    run, rev = _run_with_fixture(db_session, user, document)
    original = list(run.snapshot["revision_ids"])
    db_session.add(
        DocumentRevision(
            document_id=document.id, user_id=user.id,
            sha256="sha-nova", pages_total=3,
        )
    )
    db_session.commit()
    artifact = run_universal_pipeline(db_session, run_id=run.id)
    assert artifact is not None
    assert run.snapshot["revision_ids"] == original


def test_pipeline_cancelled_before_publication_publishes_nothing(db_session, make_user):
    from app.core.pipeline.orchestrator import run_universal_pipeline

    user, document = _document(db_session, make_user)
    run, _ = _run_with_fixture(db_session, user, document)
    run_crud.cancel_run(db_session, run=run)
    assert run_universal_pipeline(db_session, run_id=run.id) is None
    assert run_crud.get_published_artifact(db_session, run=run) is None


def test_pipeline_batch_failure_fails_run_without_artifact(db_session, make_user):
    from app.core.pipeline.orchestrator import run_universal_pipeline

    user, document = _document(db_session, make_user)
    run, _ = _run_with_fixture(db_session, user, document)
    snap = dict(run.snapshot)
    snap["fail_stage"] = "extraction"
    run.snapshot = snap
    db_session.commit()
    assert run_universal_pipeline(db_session, run_id=run.id) is None
    db_session.refresh(run)
    assert run.status == AnalysisRun.FAILED
    assert run_crud.get_published_artifact(db_session, run=run) is None
