"""CRUD de checkpoints de estágio (Onda 0 Task 2, §8.2).

``(run_id, stage, attempt)`` é único. ``finish_stage`` e ``fail_stage``
marcam o desfecho e métricas. ``get_resume_point`` lê a sequência ordenada
para retomar o pipeline V3 do ponto em que parou.
"""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.analysis_run import AnalysisRun
from app.models.analysis_stage_run import AnalysisStageRun


class StageAttemptConflictError(Exception):
    """Tentativa de iniciar estágio com (run, stage, attempt) já registrado."""

    code = "STAGE_ATTEMPT_CONFLICT"


def start_stage(
    db: Session,
    *,
    run: AnalysisRun,
    stage: str,
    attempt: int = 1,
) -> AnalysisStageRun:
    """Registra o início de um estágio; rejeita colisão (run, stage, attempt)."""
    existing = (
        db.query(AnalysisStageRun)
        .filter(
            AnalysisStageRun.run_id == run.id,
            AnalysisStageRun.stage == stage,
            AnalysisStageRun.attempt == attempt,
        )
        .one_or_none()
    )
    if existing is not None:
        raise StageAttemptConflictError(
            f"estágio {stage} attempt {attempt} já existe no run {run.id}"
        )

    stage_run = AnalysisStageRun(
        run_id=run.id,
        stage=stage,
        attempt=attempt,
        status=AnalysisStageRun.STATUS_RUNNING,
    )
    db.add(stage_run)
    db.commit()
    db.refresh(stage_run)
    return stage_run


def finish_stage(
    db: Session,
    *,
    stage_run: AnalysisStageRun,
    metrics: dict | None = None,
) -> AnalysisStageRun:
    """Marca o estágio como concluído."""
    stage_run.status = AnalysisStageRun.STATUS_COMPLETED
    stage_run.finished_at = datetime.now(timezone.utc)
    if metrics is not None:
        stage_run.metrics = metrics
    db.commit()
    db.refresh(stage_run)
    return stage_run


def fail_stage(
    db: Session,
    *,
    stage_run: AnalysisStageRun,
    code: str,
    safe_message: str,
    retryable: bool,
) -> AnalysisStageRun:
    """Marca o estágio como falho, sem vazar prompt/segredo."""
    stage_run.status = AnalysisStageRun.STATUS_FAILED
    stage_run.finished_at = datetime.now(timezone.utc)
    stage_run.error_code = code
    stage_run.error_message = safe_message
    stage_run.retryable = 1 if retryable else 0
    db.commit()
    db.refresh(stage_run)
    return stage_run


def get_resume_point(
    db: Session,
    *,
    run: AnalysisRun,
    ordered_stages: list[str],
) -> str | None:
    """Retorna o primeiro estágio em ``ordered_stages`` sem conclusão.

    Estágios que falharam (``STATUS_FAILED``) são considerados não-concluídos
    e geram retomada neles. ``None`` quando todos os estágios estão completos.
    """
    completed = {
        sr.stage
        for sr in db.query(AnalysisStageRun)
        .filter(
            AnalysisStageRun.run_id == run.id,
            AnalysisStageRun.status == AnalysisStageRun.STATUS_COMPLETED,
        )
        .all()
    }
    for stage in ordered_stages:
        if stage not in completed:
            return stage
    return None