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


def _block_marker(block: dict) -> str:
    uid = block.get("id", "")
    page = block.get("page_number", 0)
    text = block.get("normalized_text") or block.get("original_text") or ""
    return f"[bloco {uid} p.{page}] {text}"


def _provider_usage(provider) -> dict:
    """Lê a telemetria acumulada do provedor, quando ele a expõe."""
    snapshot = getattr(provider, "usage_snapshot", None)
    if not callable(snapshot):
        return {}
    try:
        return dict(snapshot() or {})
    except Exception:  # telemetria nunca derruba a run
        return {}


def usage_and_cost(*providers) -> dict:
    """Tokens reais e custo estimado somados entre provedores.

    ``cost_known`` é falso quando algum modelo não está na tabela de preços:
    nesse caso o guarda **não bloqueia** (não se bloqueia o que não se mede)
    e a telemetria registra ``cost: "unavailable"``.
    """
    from app.core.costs import estimate_cost_usd

    calls = prompt_tokens = completion_tokens = 0
    cost_usd = 0.0
    cost_known = True
    models: list[str] = []
    for provider in providers:
        usage = _provider_usage(provider)
        if not usage:
            continue
        model = getattr(provider, "model", None)
        if model and model not in models:
            models.append(model)
        prompt = int(usage.get("prompt_tokens", 0) or 0)
        completion = int(usage.get("completion_tokens", 0) or 0)
        calls += int(usage.get("calls", 0) or 0)
        prompt_tokens += prompt
        completion_tokens += completion
        cost = estimate_cost_usd(model, prompt, completion)
        if cost is None:
            cost_known = False
        else:
            cost_usd += cost
    return {
        "calls": calls,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "tokens_total": prompt_tokens + completion_tokens,
        "cost_usd": round(cost_usd, 6) if cost_known else None,
        "cost_known": cost_known,
        "models": models,
    }


def _enforce_run_budget(
    *providers,
    max_usd: float | None,
    max_tokens: int | None = None,
    stage: str,
) -> dict:
    """Para a execução antes de estourar o teto de custo da run.

    Dois tetos: tokens (sempre vale, independe de preço) e USD (só quando o
    modelo é precificado). Sem o teto de tokens, um modelo fora da tabela
    deixaria o guarda inerte — exatamente o caso do modelo de produção.
    """
    from app.core.coverage_planner import BudgetExceededError

    status = usage_and_cost(*providers)
    if max_tokens is not None and status["tokens_total"] > max_tokens:
        raise BudgetExceededError(
            f"Orcamento de tokens excedido em {stage}: "
            f"{status['tokens_total']} > teto {max_tokens}."
        )
    if (
        max_usd is not None
        and status["cost_known"]
        and status["cost_usd"] is not None
        and status["cost_usd"] > max_usd
    ):
        raise BudgetExceededError(
            f"Orcamento excedido em {stage}: US$ {status['cost_usd']:.4f} > "
            f"teto US$ {max_usd:.2f}."
        )
    return status


def execute_real_stages(
    db: Session,
    *,
    run,
    struct_provider=None,
    analysis_provider=None,
    max_batch_tokens: int | None = None,
    max_batches: int | None = None,
) -> dict:
    """Executa os estágios V3 sobre os blocos reais da revisão (W-2).

    Lê ``SourceBlock`` da revisão mais recente, classifica, planeja
    lotes, extrai por lote (falha isolada por lote), reconcilia,
    analisa e monta fontes/coverage. Sem blocos retorna
    ``{"empty": True, ...}`` para decisão honesta do chamador.
    """
    import dataclasses

    from app.core.classification import classify_blocks
    from app.core.config import settings
    from app.core.coverage_planner import plan_revision_batches
    from app.core.legal_research import research_issues
    from app.core.reconciler import reconcile_extractions
    from app.core.structured_extractor import extract_batch
    from app.core.universal_legal_analyzer import (
        UniversalAnalysisError,
        analyze_universal_case,
    )
    from app.crud.extraction import (
        latest_revision_for_document,
        list_blocks_for_revision,
    )

    revision = latest_revision_for_document(
        db, document_id=run.document_id, user_id=run.user_id
    )
    if revision is None:
        return {"empty": True, "reason": "documento sem revisão extraída"}
    rows = list_blocks_for_revision(
        db, revision_id=revision.id, user_id=run.user_id
    )
    if not rows:
        return {"empty": True, "reason": "revisão sem blocos extraídos"}

    blocks = [{
        "id": row.block_uid,
        "revision_id": str(row.revision_id),
        "page_number": row.page_number,
        "normalized_text": row.normalized_text,
        "original_text": row.original_text,
        "block_type": row.block_type,
    } for row in rows]

    classification = classify_blocks([
        {"normalized_text": b.get("normalized_text"),
         "original_text": b.get("original_text")} for b in blocks
    ])
    # Onda A: o teto de lotes configurado passa a valer no caminho real.
    # Antes, ``max_batches=None`` desligava o teto e ``check_budget`` era
    # código morto — o plano podia crescer sem limite declarado.
    effective_max_batches = (
        settings.COVERAGE_MAX_BATCHES if max_batches is None else max_batches
    )
    plan = plan_revision_batches(
        blocks,
        max_batch_tokens=max_batch_tokens,
        max_batches=effective_max_batches,
    )

    if struct_provider is None:
        from app.core.llm_providers import LlmStructuredProvider

        struct_provider = LlmStructuredProvider()
    if analysis_provider is None:
        from app.core.llm_providers import LlmAnalysisProvider

        analysis_provider = LlmAnalysisProvider()

    by_id = {b["id"]: b for b in blocks}
    extractions: list[dict] = []
    failed_batches: list[dict] = []
    truncated_batches = 0
    omitted_chars = 0
    max_run_usd = getattr(settings, "MAX_RUN_USD", None)
    max_run_tokens = getattr(settings, "MAX_RUN_TOKENS", None)
    for index, batch in enumerate(plan.get("batches", [])):
        batch_blocks = [dict(by_id[bid]) for bid in batch.get("block_ids", []) if bid in by_id]
        for b in batch_blocks:
            marked = _block_marker(b)
            b["normalized_text"] = marked
            b["original_text"] = marked
        # Orçamento do extrator = limite do modelo (COVERAGE_MAX_BATCH_TOKENS),
        # não o alvo de agrupamento (max_batch_tokens): um bloco único maior
        # que o alvo continua precisando caber no contexto.
        try:
            result = extract_batch(
                {"batch_index": index, "block_ids": batch.get("block_ids", []),
                 "blocks": batch_blocks},
                provider=struct_provider,
            )
        except Exception as exc:
            failed_batches.append({
                "batch_index": index,
                "code": getattr(exc, "code", type(exc).__name__),
            })
            continue
        extractions.append(dataclasses.asdict(result))
        text_coverage = result.text_coverage or {}
        if text_coverage.get("truncated"):
            truncated_batches += 1
            omitted_chars += int(text_coverage.get("omitted_chars", 0) or 0)
        # Teto de custo checado a cada lote: para antes de gastar, não depois.
        _enforce_run_budget(
            struct_provider, max_usd=max_run_usd,
            max_tokens=max_run_tokens, stage=f"lote {index}",
        )

    reconciled = reconcile_extractions(extractions)
    known = {b["id"] for b in blocks}
    referenced: list[str] = []
    for item in (reconciled.get("claims", []) + reconciled.get("facts", [])):
        for ref in item.get("source_refs", []) or []:
            if ref in known and ref not in referenced:
                referenced.append(ref)
    sources = [{
        "id": ref,
        "kind": "document",
        "revision_id": str(revision.id),
        "page_number": by_id[ref].get("page_number"),
        "block_id": ref,
        "quote": (by_id[ref].get("normalized_text") or "")[:500],
        "verification_status": "unverified",
    } for ref in referenced]

    snapshot = dict(run.snapshot or {})
    try:
        analysis = analyze_universal_case(
            {"facts": reconciled.get("facts", []),
             "claims": reconciled.get("claims", []),
             "evidence": reconciled.get("evidence", []),
             "sources": [{"id": s["id"]} for s in sources]},
            modules=[],
            represented_side=snapshot.get("represented_side", "neutral"),
            objective=snapshot.get("objective"),
            reference_date=snapshot.get("reference_date"),
            provider=analysis_provider,
        )
    except UniversalAnalysisError as exc:
        analysis = {
            "procedural_issues": [], "theses": [], "risks": [],
            "actions": [], "questions": [],
            "limitations": [{"code": exc.code, "message": str(exc)}],
        }
    research = research_issues([], sources=[], reference_date=snapshot.get("reference_date"))

    usage = _enforce_run_budget(
        struct_provider, analysis_provider, max_usd=max_run_usd,
        max_tokens=max_run_tokens, stage="analise",
    )

    # Parcialidade explícita: nunca corte mudo (§17).
    limitations = analysis.setdefault("limitations", [])
    if plan.get("budget_exceeded"):
        logger.warning(
            "Plano parcial: %d lote(s) > teto %s; %d bloco(s) sem processar.",
            len(plan.get("batches", [])),
            effective_max_batches,
            len(plan.get("unprocessed_block_ids", [])),
        )
        limitations.append({
            "code": "BUDGET_EXCEEDED",
            "message": (
                f"Teto de {effective_max_batches} lotes atingido; "
                f"{len(plan.get('unprocessed_block_ids', []))} bloco(s) não processado(s)."
            ),
        })
    if truncated_batches:
        limitations.append({
            "code": "BATCH_TEXT_TRUNCATED",
            "message": (
                f"{truncated_batches} lote(s) excederam o orçamento de contexto; "
                f"{omitted_chars} caractere(s) omitido(s) com marcador explícito."
            ),
        })

    pages = sorted({b.get("page_number", 0) for b in blocks})
    coverage = {
        "pages_total": revision.pages_total or (max(pages) if pages else 0),
        "pages_extracted": revision.pages_total or (max(pages) if pages else 0),
        "unprocessed_block_ids": list(plan.get("unprocessed_block_ids", [])),
        "explicit_claims_found": len(reconciled.get("claims", [])),
        "budget_exceeded": bool(plan.get("budget_exceeded")),
        "batches_planned": len(plan.get("batches", [])),
        "batches_text_truncated": truncated_batches,
        "chars_omitted": omitted_chars,
    }
    batch_stats = {
        "batches_total": len(plan.get("batches", [])),
        "batches_failed": len(failed_batches),
        "failed_codes": sorted({fb.get("code", "?") for fb in failed_batches}),
        "claims_total": len(reconciled.get("claims", [])),
        "facts_total": len(reconciled.get("facts", [])),
        "sources_total": len(sources),
        "blocks_total": len(blocks),
    }
    logger.info(
        "Estágios reais: lotes=%(batches_total)d falhados=%(batches_failed)d "
        "claims=%(claims_total)d fatos=%(facts_total)d fontes=%(sources_total)d "
        "blocos=%(blocks_total)d.",
        batch_stats,
    )
    return {
        "empty": False,
        "reconciled": reconciled,
        "analysis": analysis,
        "coverage": coverage,
        "sources": sources,
        "visuals": [],
        "research": research,
        "calculations": [],
        "classification": classification,
        "failed_batches": failed_batches,
        "batch_stats": batch_stats,
        "unprocessed_block_ids": list(plan.get("unprocessed_block_ids", [])),
        "usage": usage,
    }


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


def _run_modules(snapshot: dict, reconciled: dict, fixture: dict, classification=None):
    """Resolve, filtra por flag e executa módulos (Onda 1, spec §2 + §10)."""
    from app.core.classification import ClassificationResult
    from app.core.config import settings
    from app.core.module_runner import run_module_analyses

    if classification is None:
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
    pipeline_started = __import__("time").monotonic()
    usage_payload: dict | None = None

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

    if fixture:
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
        analysis_base = {"procedural_issues": [], "theses": [], "risks": [],
                         "actions": [], "questions": [],
                         "limitations": list(module_limitations)}
        coverage = dict(fixture.get("coverage") or {"pages_total": 1, "pages_extracted": 1})
        visuals = list(fixture.get("visuals") or [])
        sources = list(fixture.get("sources") or [])
        research = {"results": [], "partial": False}
        calculations = []
    else:
        # W-2: caminho real — estágios sobre os blocos da revisão.
        from app.core.ai_engine import ProviderUnavailableError
        from app.core.coverage_planner import BudgetExceededError
        from app.crud.run import transition_run

        try:
            real = execute_real_stages(db, run=run)
        except BudgetExceededError as exc:
            logger.warning("Teto de orcamento atingido na run %s: %s", run.id, exc)
            db.rollback()
            transition_run(
                db, run=run, status=AnalysisRun.FAILED,
                stage=AnalysisRun.STAGE_EXTRACTION,
                error_code=BudgetExceededError.code,
                error_message=str(exc),
            )
            return None
        except ProviderUnavailableError as exc:
            transition_run(
                db, run=run, status=AnalysisRun.FAILED,
                stage=AnalysisRun.STAGE_COMPOSITION,
                error_code="PROVIDER_UNAVAILABLE", error_message=str(exc),
            )
            return None
        if real.get("empty"):
            transition_run(
                db, run=run, status=AnalysisRun.FAILED,
                stage=AnalysisRun.STAGE_EXTRACTION,
                error_code="EMPTY_EXTRACTION",
                error_message=real.get("reason", "sem conteúdo extraído"),
            )
            return None
        reconciled = real["reconciled"]
        real_analysis = real["analysis"]
        real_usage = dict(real.get("usage") or {})
        usage_payload = {
            "source": "v3_pipeline",
            "models": list(real_usage.get("models") or []),
            "model": (real_usage.get("models") or [None])[0],
            "calls": real_usage.get("calls", 0),
            "prompt_tokens": real_usage.get("prompt_tokens", 0),
            "completion_tokens": real_usage.get("completion_tokens", 0),
            "tokens_total": real_usage.get("tokens_total", 0),
            "cost_usd": real_usage.get("cost_usd"),
            "cost": "estimated" if real_usage.get("cost_known") else "unavailable",
            "batches_planned": real["coverage"].get("batches_planned"),
            "batches_failed": len(real.get("failed_batches") or []),
            "chars_omitted": real["coverage"].get("chars_omitted"),
            "pages_total": real["coverage"].get("pages_total"),
            "duration_s": round(
                __import__("time").monotonic() - pipeline_started, 2
            ),
        }
        module_results, module_limitations, module_activations = _run_modules(
            snapshot, reconciled, {},
            classification=real["classification"],
        )
        analysis_base = {
            "procedural_issues": real_analysis.get("procedural_issues", []),
            "theses": real_analysis.get("theses", []),
            "risks": real_analysis.get("risks", []),
            "actions": real_analysis.get("actions", []),
            "questions": real_analysis.get("questions", []),
            "limitations": list(real_analysis.get("limitations", [])) + list(module_limitations),
        }
        coverage = real["coverage"]
        visuals = real["visuals"]
        sources = real["sources"]
        research = real["research"]
        calculations = real["calculations"]
    composed = compose_artifact(
        CompositionInputs(
            run_id=str(run.id),
            case_id=str(run.case_id) if run.case_id else None,
            coverage=coverage,
            reconciled=reconciled,
            analysis=analysis_base,
            research=research,
            calculations=calculations,
            visuals=visuals,
            sources=sources,
            module_activations=module_activations,
            module_results=module_results,
        )
    )
    artifact = ArtifactContentV3.model_validate(composed.model_dump(mode="json"))
    report = verify_artifact_v3(artifact, module_requirements=[])
    has_useful_content = bool(
        artifact.claims or artifact.facts or artifact.evidence
    )
    status = decide_publication_status(report, has_useful_content=has_useful_content)

    run.stage = AnalysisRun.STAGE_PUBLICATION
    db.commit()
    db.refresh(run)
    # Onda A: telemetria do caminho V3 (antes ficava sempre vazia — o bloco
    # de usage do legado só roda quando há artefato V2).
    if usage_payload is not None:
        run.usage = usage_payload
        db.commit()
        db.refresh(run)
    content = artifact.model_dump(mode="json")
    content["status"] = status
    published = publish_artifact_v3(
        db, run=run, artifact=content, report=report,
    )
    _index_artifact_sources(db, run=run, sources=content.get("sources") or [])
    logger.info("Pipeline V3 publicou artefato %s com status %s.", published.id, status)
    return published


_V3_TO_TABLE_STATUS = {
    "matched": "matched",
    "insufficient": "insufficient",
    "contradictory": "contradictory",
}


def _index_artifact_sources(db: Session, *, run, sources: list) -> int:
    """Persiste o índice resolvível de fontes do artefato (bloco F do smoke).

    Sem ele, `GET .../sources` e `/sources/{id}` (lidos da tabela
    `source_references`) retornam vazio/404 para artefatos V3. Falha aqui
    não desfaz a publicação — mas é registrada com erro explícito.
    """
    from app.crud.run import add_source_reference

    indexed = 0
    for source in sources or []:
        if not isinstance(source, dict) or not source.get("id"):
            continue
        status = _V3_TO_TABLE_STATUS.get(
            source.get("verification_status"), "unverified")
        try:
            add_source_reference(
                db, run=run,
                kind=source.get("kind") or "document",
                revision_id=source.get("revision_id"),
                page_number=source.get("page_number"),
                block_id=source.get("block_id") or source.get("id"),
                quote=(source.get("quote") or "")[:2000] or None,
                url=source.get("url"),
                verification_status=status,
                extra={"source_id": source.get("id")},
            )
            indexed += 1
        except Exception as exc:
            logger.warning(
                "Índice de fonte %r não persistido na run %s (%s).",
                source.get("id"), run.id, exc,
            )
    return indexed
