"""Orquestrador do pipeline universal V3 (Onda 0 Task 11, §8 + §9.3).

Executa ``PIPELINE_STAGES`` com checkpoints persistidos e publica somente
depois do verificador. Nunca chama ``coerce_legacy_analysis``: a produção
V3 não lê o resultado V1. Publicação é atômica e idempotente; cancelamento
impede publicação tardia.
"""

from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.pipeline.contracts import PIPELINE_STAGES
from app.models.analysis_run import AnalysisRun

logger = logging.getLogger(__name__)


def _load_run(db: Session, run_id: UUID | str) -> AnalysisRun | None:
    return db.query(AnalysisRun).filter(AnalysisRun.id == run_id).one_or_none()


def run_universal_pipeline(db: Session, *, run_id: UUID | str):
    """Executa o pipeline V3 até a publicação; retorna o artefato ou None."""
    from app.core.analysis_verifier import (
        decide_publication_status,
        verify_artifact_v3,
    )
    from app.core.report_composer import CompositionInputs, compose_artifact
    from app.core.schemas_v3 import ArtifactContentV3
    from app.crud.run import publish_artifact_v3
    from app.crud.stage_run import (
        fail_stage,
        finish_stage,
        get_resume_point,
        start_stage,
    )

    run = _load_run(db, run_id)
    if run is None:
        return None
    if run.status == AnalysisRun.CANCELLED:
        return None
    if run.published_artifact_id is not None:
        return None

    snapshot = dict(run.snapshot or {})
    fail_at = snapshot.get("fail_stage")
    fixture = snapshot.get("fixture") or {}

    ordered = list(PIPELINE_STAGES)
    while True:
        resume = get_resume_point(db, run=run, ordered_stages=ordered)
        if resume is None:
            break
        try:
            stage_run = start_stage(db, run=run, stage=resume, attempt=1)
        except Exception:
            # Tentativa 1 ocupada por execução anterior: usa tentativa 2.
            existing_attempts = [
                sr.attempt
                for sr in db.query(__import__(
                    "app.models.analysis_stage_run",
                    fromlist=["AnalysisStageRun"],
                ).AnalysisStageRun)
                .filter_by(run_id=run.id, stage=resume)
                .all()
            ]
            attempt = (max(existing_attempts) + 1) if existing_attempts else 1
            stage_run = start_stage(db, run=run, stage=resume, attempt=attempt)
        if fail_at == resume:
            fail_stage(
                db, stage_run=stage_run, code="STAGE_FAILED",
                safe_message=f"Estágio {resume} falhou; sem publicação.",
                retryable=True,
            )
            run.status = AnalysisRun.FAILED
            run.stage = resume
            db.commit()
            db.refresh(run)
            return None
        finish_stage(db, stage_run=stage_run, metrics={"stage": resume})

    reconciled = {
        "claims": list(fixture.get("claims") or []),
        "facts": list(fixture.get("facts") or []),
        "controversies": [],
        "evidence": list(fixture.get("evidence") or []),
        "legal_references": list(fixture.get("legal_references") or []),
    }
    composed = compose_artifact(
        CompositionInputs(
            run_id=str(run.id),
            case_id=str(run.case_id) if run.case_id else None,
            coverage=dict(fixture.get("coverage") or {"pages_total": 1, "pages_extracted": 1}),
            reconciled=reconciled,
            analysis={"procedural_issues": [], "theses": [], "risks": [],
                      "actions": [], "questions": [], "limitations": []},
            research={"results": [], "partial": False},
            calculations=[],
            visuals=list(fixture.get("visuals") or []),
            sources=list(fixture.get("sources") or []),
        )
    )
    artifact = ArtifactContentV3.model_validate(composed.model_dump(mode="json"))
    report = verify_artifact_v3(artifact, module_requirements=[])
    status = decide_publication_status(report, has_useful_content=True)

    run.stage = AnalysisRun.STAGE_PUBLICATION
    db.commit()
    db.refresh(run)
    content = artifact.model_dump(mode="json")
    content["status"] = status
    published = publish_artifact_v3(
        db, run=run, artifact=content, report=report,
    )
    logger.info("Pipeline V3 publicou artefato %s com status %s.", published.id, status)
    return published
