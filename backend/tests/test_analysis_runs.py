"""V2 T02 — execuções e revisões versionadas (aceite do plano)."""

import pytest

from app.crud import run as run_crud
from app.models.analysis import Analysis
from app.models.analysis_run import AnalysisRun
from app.models.document import Document


def _document(db_session, make_user, name="peca.pdf"):
    user = make_user()
    document = Document(
        user_id=user.id,
        filename=name,
        file_path=f"/tmp/{name}",
        content_type="application/pdf",
        status=Document.STATUS_UPLOADED,
    )
    db_session.add(document)
    db_session.commit()
    db_session.refresh(document)
    return user, document


def test_two_reanalyses_coexist_with_own_artifacts(db_session, make_user):
    user, document = _document(db_session, make_user)
    first = run_crud.create_run(
        db_session, user_id=user.id, document_id=document.id,
        idempotency_key="run-1", snapshot={"rev": "r1"},
    )
    second = run_crud.create_run(
        db_session, user_id=user.id, document_id=document.id,
        idempotency_key="run-2", snapshot={"rev": "r2"},
    )
    assert first.id != second.id

    art1 = run_crud.publish_artifact(
        db_session, run=first, content={"schema_version": "2.0", "claims": []},
        status="partial",
    )
    art2 = run_crud.publish_artifact(
        db_session, run=second, content={"schema_version": "2.0", "claims": []},
        status="completed",
    )
    assert art1.id != art2.id

    runs = run_crud.list_runs_for_document(
        db_session, document_id=document.id, user_id=user.id
    )
    assert [str(r.id) for r in runs] == [str(first.id), str(second.id)]
    assert run_crud.get_published_artifact(db_session, run=first).id == art1.id
    assert run_crud.get_published_artifact(db_session, run=second).id == art2.id
    # Legado preservado: projeção 1:1 intocada.
    assert db_session.query(Analysis).count() == 0


def test_idempotent_create_returns_existing_run(db_session, make_user):
    user, document = _document(db_session, make_user)
    first = run_crud.create_run(
        db_session, user_id=user.id, document_id=document.id,
        idempotency_key="same-key",
    )
    second = run_crud.create_run(
        db_session, user_id=user.id, document_id=document.id,
        idempotency_key="same-key",
    )
    assert first.id == second.id
    assert (
        db_session.query(AnalysisRun)
        .filter_by(user_id=user.id, idempotency_key="same-key")
        .count()
        == 1
    )


def test_cancel_blocks_late_publication(db_session, make_user):
    user, document = _document(db_session, make_user)
    run = run_crud.create_run(db_session, user_id=user.id, document_id=document.id)
    run_crud.cancel_run(db_session, run=run)
    # Cancelamento idempotente.
    run_crud.cancel_run(db_session, run=run)
    assert run.status == AnalysisRun.CANCELLED
    with pytest.raises(run_crud.VersionConflictError):
        run_crud.publish_artifact(db_session, run=run, content={})
    assert run_crud.get_published_artifact(db_session, run=run) is None


def test_stale_version_and_double_publish_conflict(db_session, make_user):
    user, document = _document(db_session, make_user)
    run = run_crud.create_run(db_session, user_id=user.id, document_id=document.id)
    stale_version = run.version
    run_crud.publish_artifact(
        db_session, run=run, content={"v": 1}, expected_version=stale_version
    )
    assert run.version == stale_version + 1
    # Tentativa antiga com versão obsoleta não substitui a recente.
    with pytest.raises(run_crud.VersionConflictError):
        run_crud.publish_artifact(
            db_session, run=run, content={"v": 2}, expected_version=stale_version
        )
    # Segunda publicação do mesmo run também é bloqueada.
    with pytest.raises(run_crud.VersionConflictError):
        run_crud.publish_artifact(db_session, run=run, content={"v": 3})


def test_terminal_run_never_regresses_to_active(db_session, make_user):
    user, document = _document(db_session, make_user)
    run = run_crud.create_run(db_session, user_id=user.id, document_id=document.id)
    run_crud.transition_run(
        db_session, run=run, status=AnalysisRun.COMPLETED,
        stage=AnalysisRun.STAGE_COMPOSITION,
    )
    with pytest.raises(run_crud.VersionConflictError):
        run_crud.transition_run(db_session, run=run, status=AnalysisRun.RUNNING)


def test_tenant_isolation_and_review_trail(db_session, make_user):
    user, document = _document(db_session, make_user)
    intruder = make_user(email="intruder@example.com", username="intruder")
    run = run_crud.create_run(db_session, user_id=user.id, document_id=document.id)
    assert (
        run_crud.get_run_for_user(db_session, run_id=run.id, user_id=intruder.id)
        is None
    )
    artifact = run_crud.publish_artifact(db_session, run=run, content={"claims": []})
    ref = run_crud.add_source_reference(
        db_session, run=run, page_number=34, quote="Pensao mensal",
        verification_status="matched",
    )
    assert ref.run_id == run.id
    event = run_crud.add_review_event(
        db_session, artifact=artifact, reviewer_id=user.id,
        target="claims.claim-8", before={"a": 1}, after={"a": 2},
        reason="correcao do valor",
    )
    assert event.source_version == "2.0"
