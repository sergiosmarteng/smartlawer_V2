"""Verificação antes da publicação + composição executiva (V2 T10, §5.1).

Erro material bloqueia completude e vira pendência acionável; uma
reparação limitada corrige falha estrutural derivável (nunca inventa
fontes, teses ou valores). Publicação usa o CRUD versionado (T02).
"""

import logging
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation

from app.core.schemas_v2 import ArtifactContent, validate_artifact

logger = logging.getLogger(__name__)

STATUS_COMPLETED = "completed"
STATUS_PARTIAL = "partial"
STATUS_FAILED = "failed"


@dataclass
class VerificationReport:
    passed: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    pending_actions: list[str] = field(default_factory=list)
    repairs: list[str] = field(default_factory=list)


def check_coverage(artifact: ArtifactContent) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    coverage = artifact.coverage
    if coverage.pages_total and coverage.pages_extracted < coverage.pages_total:
        errors.append(
            f"cobertura: {coverage.pages_extracted}/{coverage.pages_total} páginas extraídas"
        )
    if coverage.unprocessed_block_ids:
        errors.append(
            f"cobertura: {len(coverage.unprocessed_block_ids)} bloco(s) sem processar"
        )
    if not artifact.claims:
        errors.append("cobertura: nenhum pedido representado")
    return errors, warnings


def check_support(artifact: ArtifactContent) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for claim in artifact.claims:
        if not claim.source_refs:
            warnings.append(
                f"pedido {claim.id}: sem fonte localizada — hipótese a confirmar"
            )
    for thesis in artifact.theses:
        if not thesis.supporting_refs:
            warnings.append(
                f"tese {thesis.id}: sem fontes suficientes — hipótese para "
                "pesquisa, não tese validada"
            )
    for index, fact in enumerate(artifact.facts):
        if fact.epistemic_status in ("documented", "admitted") and not fact.source_refs:
            errors.append(f"fato[{index}]: status forte sem fonte")
    return errors, warnings


def check_calculations(records: list[dict]) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for record in records:
        rid = record.get("id", "?")
        if not record.get("formula") or not record.get("formula_version"):
            errors.append(f"cálculo {rid}: fórmula sem identificação/versão")
        result = record.get("result")
        if result is None:
            errors.append(f"cálculo {rid}: sem resultado reproduzível")
        else:
            try:
                Decimal(str(result))
            except (InvalidOperation, ValueError):
                errors.append(f"cálculo {rid}: resultado inválido {result!r}")
        if record.get("depends_on_pericia") and not record.get("assumptions"):
            warnings.append(f"cálculo {rid}: dependência de perícia sem premissa explícita")
    return errors, warnings


def verify(
    artifact: ArtifactContent,
    *,
    calculations: list[dict] | None = None,
    figures_state: str | None = None,
) -> VerificationReport:
    """Valida cobertura, suporte, referências e cálculos (§8.4/T10)."""
    errors = validate_artifact(artifact)
    warnings: list[str] = []
    pending: list[str] = []

    cov_errors, cov_warnings = check_coverage(artifact)
    errors.extend(cov_errors)
    warnings.extend(cov_warnings)

    sup_errors, sup_warnings = check_support(artifact)
    errors.extend(sup_errors)
    warnings.extend(sup_warnings)

    calc_errors, calc_warnings = check_calculations(calculations or [])
    errors.extend(calc_errors)
    warnings.extend(calc_warnings)

    if figures_state in ("failed", "figures_unresolved"):
        warnings.append(
            f"figuras: estado {figures_state} — não alegar ausência de imagens"
        )
        pending.append("Revisar extração de figuras e religar à revisão.")

    for error in errors:
        pending.append(f"Corrigir antes de aprovar: {error}")
    return VerificationReport(
        passed=not errors, errors=errors, warnings=warnings, pending_actions=pending
    )


def decide_status(report: VerificationReport, *, has_useful_content: bool = True) -> str:
    """completed só com invariantes OK; parcial com limitação; failed sem núcleo."""
    if report.passed:
        return STATUS_COMPLETED
    if has_useful_content:
        return STATUS_PARTIAL
    return STATUS_FAILED


def repair_once(artifact: ArtifactContent) -> tuple[ArtifactContent, list[str]]:
    """Uma reparação controlada por estágio: só estrutura derivável (§7.1)."""
    repairs: list[str] = []
    if artifact.coverage.explicit_claims_found != len(artifact.claims):
        artifact.coverage.explicit_claims_found = len(artifact.claims)
        repairs.append("coverage.explicit_claims_found sincronizado")
    for index, claim in enumerate(artifact.claims):
        if not claim.id:
            claim.id = f"claim-auto-{index}"
            repairs.append(f"id atribuído ao pedido {index}")
    if repairs:
        logger.info("Reparação estrutural aplicada: %s", repairs)
    return artifact, repairs


def compose_executive_summary(
    artifact: ArtifactContent, report: VerificationReport
) -> dict:
    """Visão executiva a partir de objetos validados (ReportComposer mínimo)."""
    values = [
        {"claim_id": c.id, "title": c.title, "amount": c.amount.value if c.amount else None}
        for c in artifact.claims
        if c.amount and c.amount.value
    ]
    return {
        "status": STATUS_COMPLETED if report.passed else STATUS_PARTIAL,
        "claims_total": len(artifact.claims),
        "values": values,
        "priority_issues": report.errors[:5],
        "pending_actions": report.pending_actions,
        "limitations": [lim.message for lim in artifact.limitations],
        "warnings": report.warnings,
    }
