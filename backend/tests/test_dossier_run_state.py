"""Onda 0 Task 3 — transições, progresso e publicação honestos.

6 invariantes (plano §3):
- estágio ``extraction`` nunca retorna 100%;
- progresso usa documentos/páginas/lotes/verificações concluídos;
- run cancelado rejeita retry tardio;
- run já publicado rejeita segunda publicação;
- ``completed`` exige ``stage == publication`` e relatório aprovado;
- artefato V3 salva ``schema_version == "3.0"``.
"""

import pytest

from app.crud import run as run_crud
from app.models.analysis_run import AnalysisRun
from app.models.document import Document


def _document(db_session, make_user, name="peca-t3.pdf"):
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


def _v3_artifact_dict(status="partial"):
    return {
        "schema_version": "3.0",
        "run_id": "run-t3",
        "status": status,
        "section_states": {},
        "claims": [],
        "facts": [],
        "evidence": [],
        "sources": [],
        "coverage": {"pages_total": 2, "pages_extracted": 2},
    }


def _approved_report():
    from app.core.analysis_verifier import VerificationReport

    return VerificationReport(passed=True, errors=[], warnings=[])


def _rejected_report():
    from app.core.analysis_verifier import VerificationReport

    return VerificationReport(
        passed=False,
        errors=["cobertura: 1 bloco(s) sem processar"],
        warnings=[],
        pending_actions=["Corrigir antes de aprovar: cobertura"],
    )


def test_extraction_stage_never_returns_100(db_session, make_user):
    """Estágio ``extraction`` nunca retorna 100%, mesmo com status ativo."""
    from app.core.pipeline.contracts import PIPELINE_STAGES, calculate_progress

    user, document = _document(db_session, make_user)
    run = run_crud.create_run(db_session, user_id=user.id, document_id=document.id)
    run_crud.transition_run(
        db_session, run=run, status=AnalysisRun.RUNNING, stage="extraction"
    )

    assert "extraction" in PIPELINE_STAGES
    snapshot = calculate_progress(run, [])
    assert snapshot.percent < 100, f"extraction retornou {snapshot.percent}%"


def test_progress_uses_completed_units(db_session, make_user):
    """Progresso deriva de estágios concluídos, não de porcentagem fictícia."""
    from app.core.pipeline.contracts import PIPELINE_STAGES, calculate_progress
    from app.crud.stage_run import finish_stage, start_stage

    user, document = _document(db_session, make_user)
    run = run_crud.create_run(db_session, user_id=user.id, document_id=document.id)
    run_crud.transition_run(
        db_session, run=run, status=AnalysisRun.RUNNING, stage="extraction"
    )

    # 3 de 12 estágios concluídos → ~25%, nunca 100.
    for stage in PIPELINE_STAGES[:3]:
        sr = start_stage(db_session, run=run, stage=stage, attempt=1)
        finish_stage(db_session, stage_run=sr)

    from app.models.analysis_stage_run import AnalysisStageRun

    stage_runs = (
        db_session.query(AnalysisStageRun)
        .filter(AnalysisStageRun.run_id == run.id)
        .all()
    )
    snapshot = calculate_progress(run, stage_runs)
    assert snapshot.completed_stages == 3
    assert snapshot.total_stages == len(PIPELINE_STAGES)
    assert 0 < snapshot.percent < 100

    # Mais estágios concluídos → progresso monotonicamente maior.
    for stage in PIPELINE_STAGES[3:6]:
        sr = start_stage(db_session, run=run, stage=stage, attempt=1)
        finish_stage(db_session, stage_run=sr)
    stage_runs = (
        db_session.query(AnalysisStageRun)
        .filter(AnalysisStageRun.run_id == run.id)
        .all()
    )
    later = calculate_progress(run, stage_runs)
    assert later.percent > snapshot.percent
    assert later.percent < 100


def test_cancelled_run_rejects_late_publish(db_session, make_user):
    """Run cancelado rejeita publicação tardia V3 (sem retry fantasma)."""
    from app.crud.run import publish_artifact_v3

    user, document = _document(db_session, make_user)
    run = run_crud.create_run(db_session, user_id=user.id, document_id=document.id)
    run_crud.cancel_run(db_session, run=run)

    with pytest.raises(run_crud.VersionConflictError):
        publish_artifact_v3(
            db_session,
            run=run,
            artifact=_v3_artifact_dict(status="partial"),
            report=_approved_report(),
        )


def test_double_publish_rejected(db_session, make_user):
    """Run já publicado rejeita segunda publicação V3."""
    from app.crud.run import publish_artifact_v3

    user, document = _document(db_session, make_user)
    run = run_crud.create_run(db_session, user_id=user.id, document_id=document.id)
    run_crud.transition_run(
        db_session, run=run, status=AnalysisRun.RUNNING, stage="publication"
    )
    publish_artifact_v3(
        db_session,
        run=run,
        artifact=_v3_artifact_dict(status="partial"),
        report=_approved_report(),
    )
    with pytest.raises(run_crud.VersionConflictError):
        publish_artifact_v3(
            db_session,
            run=run,
            artifact=_v3_artifact_dict(status="partial"),
            report=_approved_report(),
        )


def test_completed_requires_publication_stage_and_approved_report(
    db_session, make_user
):
    """``completed`` exige ``stage == publication`` E relatório aprovado."""
    from app.crud.run import publish_artifact_v3

    user, document = _document(db_session, make_user)

    # Caso 1: stage != publication → rejeita mesmo com relatório aprovado.
    run1 = run_crud.create_run(db_session, user_id=user.id, document_id=document.id)
    run_crud.transition_run(
        db_session, run=run1, status=AnalysisRun.RUNNING, stage="extraction"
    )
    with pytest.raises(run_crud.VersionConflictError):
        publish_artifact_v3(
            db_session,
            run=run1,
            artifact=_v3_artifact_dict(status="completed"),
            report=_approved_report(),
        )

    # Caso 2: stage == publication mas relatório reprovado → rejeita.
    run2 = run_crud.create_run(db_session, user_id=user.id, document_id=document.id)
    run_crud.transition_run(
        db_session, run=run2, status=AnalysisRun.RUNNING, stage="publication"
    )
    with pytest.raises(run_crud.VersionConflictError):
        publish_artifact_v3(
            db_session,
            run=run2,
            artifact=_v3_artifact_dict(status="completed"),
            report=_rejected_report(),
        )

    # Caso 3: stage == publication + relatório aprovado → publica.
    run3 = run_crud.create_run(db_session, user_id=user.id, document_id=document.id)
    run_crud.transition_run(
        db_session, run=run3, status=AnalysisRun.RUNNING, stage="publication"
    )
    artifact = publish_artifact_v3(
        db_session,
        run=run3,
        artifact=_v3_artifact_dict(status="completed"),
        report=_approved_report(),
    )
    assert artifact.status == "completed"
    assert run3.status == AnalysisRun.COMPLETED


def test_v3_artifact_saves_schema_30(db_session, make_user):
    """Artefato V3 persiste ``schema_version == '3.0'``."""
    from app.crud.run import publish_artifact_v3

    user, document = _document(db_session, make_user)
    run = run_crud.create_run(db_session, user_id=user.id, document_id=document.id)
    run_crud.transition_run(
        db_session, run=run, status=AnalysisRun.RUNNING, stage="publication"
    )
    artifact = publish_artifact_v3(
        db_session,
        run=run,
        artifact=_v3_artifact_dict(status="partial"),
        report=_approved_report(),
    )
    assert artifact.schema_version == "3.0"
    assert artifact.content["schema_version"] == "3.0"
