"""Módulo tributário v1.0 (Onda 2B, spec §5)."""

from decimal import Decimal

from app.core.calculations import CalculationBlockedError, _quantize, _require_decimal
from app.core.module_registry import ModuleRequirements
from app.modules.tax.checklist import TAX_MATRIX


TAX_SOURCES = [
    {"id": "ctn", "organ": "Planalto",
     "url": "https://planalto.gov.br/ccivil_03/leis/l5172compilado.htm"},
]

_STRONG_EPISTEMIC = ("documented", "admitted")


def _norm(text: str | None) -> str:
    return (text or "").casefold()


def _matched_facts(facts: list[dict], keywords: tuple[str, ...]) -> list[dict]:
    out = []
    for fact in facts:
        haystack = f"{fact.get('statement', '')} {fact.get('id', '')}"
        if any(kw in _norm(haystack) for kw in keywords):
            out.append(fact)
    return out


def _resolve_sources(matched: list[dict], known_sources: set[str]) -> list[str]:
    refs: list[str] = []
    for fact in matched:
        for ref in fact.get("source_refs", []) or []:
            if ref in known_sources and ref not in refs:
                refs.append(ref)
    return refs


def assess_dimension(dimension_key: str, case_data: dict) -> dict:
    """Avalia tema tributário com gates §5 (sem crédito/alíquota/prazo inventados)."""
    dimension = next(d for d in TAX_MATRIX if d.key == dimension_key)
    facts = case_data.get("facts", []) or []
    known_sources = {s.get("id") for s in (case_data.get("sources") or []) if s.get("id")}
    matched = _matched_facts(facts, dimension.keywords)
    supporting = _resolve_sources(matched, known_sources)
    strong = [f for f in matched if f.get("epistemic_status") in _STRONG_EPISTEMIC]
    strong_supported = _resolve_sources(strong, known_sources)

    if dimension_key == "credito" and matched and not strong_supported:
        return {
            "issue_key": f"tax.{dimension.key}",
            "status": "partial",
            "conclusion": (
                f"{dimension.title}: auto isolado não gera crédito definitivo; "
                "exige apuração por competência."
            ),
            "factual_refs": [f.get("id") for f in matched if f.get("id")],
            "supporting_source_refs": supporting,
            "adverse_source_refs": [],
            "missing_inputs": ["apuração por competência", "pagamentos", "atualização"],
            "related_claim_ids": [],
            "action_ids": [],
        }
    if dimension_key == "tempo" and matched and not strong_supported:
        return {
            "issue_key": f"tax.{dimension.key}",
            "status": "blocked",
            "conclusion": (
                f"{dimension.title}: prescrição/decadência sem marco e causa "
                "suspensiva sustentados."
            ),
            "factual_refs": [f.get("id") for f in matched if f.get("id")],
            "supporting_source_refs": supporting,
            "adverse_source_refs": [],
            "missing_inputs": ["marco temporal", "causa suspensiva/interruptiva"],
            "related_claim_ids": [],
            "action_ids": [],
        }
    if matched and strong_supported:
        return {
            "issue_key": f"tax.{dimension.key}",
            "status": "complete",
            "conclusion": f"{dimension.title}: premissas sustentadas por fonte examinada.",
            "factual_refs": [f.get("id") for f in matched if f.get("id")],
            "supporting_source_refs": strong_supported,
            "adverse_source_refs": [],
            "missing_inputs": [],
            "related_claim_ids": [],
            "action_ids": [],
        }
    if matched:
        return {
            "issue_key": f"tax.{dimension.key}",
            "status": "partial",
            "conclusion": f"{dimension.title}: alegação registrada, condicionado a prova.",
            "factual_refs": [f.get("id") for f in matched if f.get("id")],
            "supporting_source_refs": supporting,
            "adverse_source_refs": [],
            "missing_inputs": [dimension.items[0].expected_evidence[0]],
            "related_claim_ids": [],
            "action_ids": [],
        }
    return {
        "issue_key": f"tax.{dimension.key}",
        "status": "blocked",
        "conclusion": f"{dimension.title}: sem elementos nos autos.",
        "factual_refs": [],
        "supporting_source_refs": [],
        "adverse_source_refs": [],
        "missing_inputs": [dimension.items[0].question],
        "related_claim_ids": [],
        "action_ids": [],
    }


class TaxModule:
    module_id = "tax"
    version = "1.0.0"
    supported_areas = ("tax",)
    document_types = ("auto_infracao", "declaracao", "notificacao", "impugnacao")

    def requirements(self) -> ModuleRequirements:
        return ModuleRequirements(
            required_sections=["parties", "events", "claims", "facts", "evidence"],
            issue_checklists=[d.key for d in TAX_MATRIX],
            calculation_rules=["tributo_competencia@1.0"],
            research_sources=[s["id"] for s in TAX_SOURCES],
            evaluation_cases=["tax_cases"],
        )

    def analyze(self, case_data: dict) -> dict:
        assessments = [assess_dimension(d.key, case_data or {}) for d in TAX_MATRIX]
        status = "complete" if any(a["status"] == "complete" for a in assessments) else "partial"
        return {
            "module_id": self.module_id,
            "module_version": self.version,
            "status": status,
            "reason": "Matriz aplicável examinada",
            "issue_assessments": assessments,
            "calculation_ids": [],
            "limitations": [],
        }


def tributo_competencia(inputs: dict) -> Decimal:
    """Crédito por competência: base, alíquota, deduções, pagamentos, atualização."""
    missing = [k for k in ("base", "aliquota", "competencia", "fonte_ente")
               if inputs.get(k) in (None, "")]
    if missing:
        raise CalculationBlockedError(
            "tributo_competencia: entradas faltantes: " + ", ".join(missing))
    base = _require_decimal(inputs["base"], "base")
    aliquota = _require_decimal(inputs["aliquota"], "aliquota")
    bruto = base * aliquota / Decimal(100)
    deducoes = _require_decimal(inputs.get("deducoes", "0"), "deducoes")
    pagamentos = _require_decimal(inputs.get("pagamentos", "0"), "pagamentos")
    atualizacao = _require_decimal(inputs.get("atualizacao", "0"), "atualizacao")
    return _quantize(bruto - deducoes - pagamentos + atualizacao)


def register_calculation_rules(registry) -> None:
    registry.register("tributo_competencia", "1.0", tributo_competencia)


DESCRIPTOR = {
    "module_id": "tax",
    "version": "1.0.0",
    "supported_areas": ["tax"],
    "document_types": ["auto_infracao", "declaracao", "notificacao", "impugnacao"],
    "required_sections": ["parties", "events", "claims", "facts", "evidence"],
    "issue_checklists": [d.key for d in TAX_MATRIX],
    "calculation_rules": ["tributo_competencia@1.0"],
    "research_sources": [s["id"] for s in TAX_SOURCES],
    "evaluation_cases": ["tax_cases"],
}
