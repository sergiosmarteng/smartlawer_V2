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


_MODULE_FLAGS = {
    "civil_procedure": "DOSSIER_MODULE_CIVIL_PROCEDURE",
    "family": "DOSSIER_MODULE_FAMILY",
    "labor": "DOSSIER_MODULE_LABOR",
    "consumer": "DOSSIER_MODULE_CONSUMER",
    "social_security": "DOSSIER_MODULE_SOCIAL_SECURITY",
    # Onda 2A: par coeso contracts+corporate (spec §10); off por padrão.
    "contracts": "DOSSIER_MODULE_CONTRACTS",
    "corporate": "DOSSIER_MODULE_CORPORATE",
    # Onda 2B: tax/administrative/real_estate (spec §10); off por padrão.
    "tax": "DOSSIER_MODULE_TAX",
    "administrative": "DOSSIER_MODULE_ADMINISTRATIVE",
    "real_estate": "DOSSIER_MODULE_REAL_ESTATE",
}


def _module_registry():
    """Registry com os 5 módulos da Onda 1 (import tardio, sem ciclo)."""
    from app.core.module_registry import LegalModuleRegistry
    from app.modules.administrative import AdministrativeModule
    from app.modules.civil_procedure import CivilProcedureModule
    from app.modules.consumer import ConsumerModule
    from app.modules.contracts import ContractsModule
    from app.modules.corporate import CorporateModule
    from app.modules.family import FamilyModule
    from app.modules.labor.module import LaborModule
    from app.modules.real_estate import RealEstateModule
    from app.modules.social_security import SocialSecurityModule
    from app.modules.tax import TaxModule

    registry = LegalModuleRegistry.with_defaults()
    for module in (
        CivilProcedureModule(), FamilyModule(), LaborModule(),
        ConsumerModule(), SocialSecurityModule(),
        ContractsModule(), CorporateModule(),
        TaxModule(), AdministrativeModule(), RealEstateModule(),
    ):
        registry.register(module)
    return registry


def _run_modules(snapshot: dict, reconciled: dict, fixture: dict):
    """Resolve, filtra por flag e executa módulos (Onda 1, spec §2 + §10)."""
    from app.core.classification import ClassificationResult
    from app.core.config import settings
    from app.core.module_runner import run_module_analyses

    areas = list(snapshot.get("areas") or [])
    if areas:
        classification = ClassificationResult(
            primary_area=areas[0], related_areas=areas[1:], source="model")
    else:
        classification = ClassificationResult(primary_area="general", source="fallback")
    registry = _module_registry()
    enabled = {"universal"} | {
        module_id for module_id, flag in _MODULE_FLAGS.items()
        if bool(getattr(settings, flag, False))
    }
    resolved = registry.resolve(classification, enabled=enabled)
    case_data = {
        "claims": reconciled.get("claims") or [],
        "facts": reconciled.get("facts") or [],
        "evidence": reconciled.get("evidence") or [],
        "sources": list(fixture.get("sources") or []),
        "visuals": list(fixture.get("visuals") or []),
    }
    results, limitations = run_module_analyses(modules=resolved, case_data=case_data)
    activations = [{
        "module_id": "universal",
        "module_version": "1.0",
        "status": "active",
        "reason": "Núcleo universal obrigatório",
    }]
    for module in resolved:
        if module.module_id == "universal":
            continue
        status = results.get(module.module_id, {}).get("status", "active")
        activations.append({
            "module_id": module.module_id,
            "module_version": getattr(module, "version", "1.0.0"),
            # Ativação registra se o módulo rodou (active) ou travou
            # (blocked); "partial" é estado do resultado, não da ativação.
            "status": "blocked" if status == "blocked" else "active",
            "reason": "Matriz aplicável examinada",
        })
    seen = {a["module_id"] for a in activations}
    for record in registry.activations(classification):
        if record.module_id not in seen and record.status == "fallback":
            activations.append(record.model_dump())
            seen.add(record.module_id)
    return results, limitations, activations


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
    # Onda 1: módulos especializados atrás de flags individuais.
    module_results, module_limitations, module_activations = _run_modules(
        snapshot, reconciled, fixture
    )
    composed = compose_artifact(
        CompositionInputs(
            run_id=str(run.id),
            case_id=str(run.case_id) if run.case_id else None,
            coverage=dict(fixture.get("coverage") or {"pages_total": 1, "pages_extracted": 1}),
            reconciled=reconciled,
            analysis={"procedural_issues": [], "theses": [], "risks": [],
                      "actions": [], "questions": [],
                      "limitations": list(module_limitations)},
            research={"results": [], "partial": False},
            calculations=[],
            visuals=list(fixture.get("visuals") or []),
            sources=list(fixture.get("sources") or []),
            module_activations=module_activations,
            module_results=module_results,
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
