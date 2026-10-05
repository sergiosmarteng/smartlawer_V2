"""W-3 — reanalyze despacha trabalho; reprocessamento cria nova run."""

from types import SimpleNamespace

from app.crud import run as run_crud
from app.models.analysis_run import AnalysisRun
from app.models.document import Document


def _document(db_session, make_user):
    user = make_user()
    document = Document(
        user_id=user.id, filename="p-rd.pdf", file_path="/tmp/p-rd.pdf",
        content_type="application/pdf", status="uploaded",
    )
    db_session.add(document)
    db_session.commit()
    db_session.refresh(document)
    return user, document


def _seed_run_artifact(db_session, user, document):
    run = run_crud.create_run(
        db_session, user_id=user.id, document_id=document.id,
        idempotency_key="rd-seed-1", snapshot={"module_id": "labor"},
    )
    artifact = run_crud.publish_artifact(
        db_session, run=run,
        content={"schema_version": "2.0", "claims": [{"id": "c1"}],
                 "sources": [], "limitations": []},
        status="completed",
    )
    return run, artifact


def test_reanalyze_dispatches_task_and_preserves_original(
    client, db_session, make_user, auth_headers_for, monkeypatch
):
    import app.api.routes.analysis_v2 as routes_v2

    calls = []
    monkeypatch.setattr(
        routes_v2.process_run_task, "delay",
        lambda run_id: calls.append(run_id),
    )
    user, document = _document(db_session, make_user)
    _, artifact = _seed_run_artifact(db_session, user, document)
    before = dict(artifact.content or {})
    resp = client.post(f"/api/v2/analyses/{artifact.id}/reanalyze",
                       headers=auth_headers_for(user))
    assert resp.status_code == 202
    new_run_id = resp.json()["run_id"]
    assert new_run_id != str(artifact.run_id)
    assert calls == [new_run_id]
    db_session.refresh(artifact)
    assert dict(artifact.content or {}) == before


def test_process_run_task_missing_run_is_safe(db_session):
    from app.tasks.document_tasks import process_run_task

    assert process_run_task.run("00000000-0000-0000-0000-000000000000") is None


def test_process_run_task_cancelled_run_does_nothing(db_session, make_user, monkeypatch):
    import app.tasks.document_tasks as tasks

    def _boom(*args, **kwargs):
        raise AssertionError("pipeline não pode rodar em run cancelada")

    monkeypatch.setattr(
        "app.core.pipeline.orchestrator.run_universal_pipeline", _boom)
    user, document = _document(db_session, make_user)
    run = run_crud.create_run(db_session, user_id=user.id, document_id=document.id)
    run_crud.cancel_run(db_session, run=run)
    assert tasks.process_run_task.run(str(run.id)) is None


def test_process_run_task_happy_path_completes_document(
    db_session, make_user, monkeypatch
):
    import app.tasks.document_tasks as tasks

    fake_artifact = SimpleNamespace(id="art-nova")
    monkeypatch.setattr(
        "app.core.pipeline.orchestrator.run_universal_pipeline",
        lambda db, run_id: fake_artifact,
    )
    user, document = _document(db_session, make_user)
    run = run_crud.create_run(db_session, user_id=user.id, document_id=document.id)
    out = tasks.process_run_task.run(str(run.id))
    assert out is not None
    db_session.refresh(document)
    assert document.status == Document.STATUS_COMPLETED


def test_process_run_task_failed_pipeline_marks_error(
    db_session, make_user, monkeypatch
):
    import app.tasks.document_tasks as tasks

    monkeypatch.setattr(
        "app.core.pipeline.orchestrator.run_universal_pipeline",
        lambda db, run_id: None,
    )
    user, document = _document(db_session, make_user)
    run = run_crud.create_run(db_session, user_id=user.id, document_id=document.id)
    run_crud.transition_run(db_session, run=run, status=AnalysisRun.FAILED)
    assert tasks.process_run_task.run(str(run.id)) is None
    db_session.refresh(document)
    assert document.status == Document.STATUS_ERROR
