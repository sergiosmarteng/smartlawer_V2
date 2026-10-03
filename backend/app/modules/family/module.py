"""Módulo família e sucessões v1.0 (Onda 1A, spec §5)."""

from decimal import Decimal

from app.core.calculations import CalculationBlockedError, _quantize
from app.core.module_registry import ModuleRequirements
from app.modules.family.checklist import FAMILY_MATRIX


FAMILY_SOURCES = [
    {"id": "cc", "organ": "Planalto",
     "url": "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm"},
    {"id": "cpc", "organ": "Planalto",
     "url": "https://planalto.gov.br/ccivil_03/_ato2015-2018/2015/lei/l13105compilada.htm"},
    {"id": "eca", "organ": "Planalto",
     "url": "https://planalto.gov.br/ccivil_03/leis/l8069compilado.htm"},
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
    """Avalia uma dimensão: premissas, prova necessária, conclusão condicionada."""
    dimension = next(d for d in FAMILY_MATRIX if d.key == dimension_key)
    facts = case_data.get("facts", []) or []
    known_sources = {s.get("id") for s in (case_data.get("sources") or []) if s.get("id")}
    matched = _matched_facts(facts, dimension.keywords)
    supporting = _resolve_sources(matched, known_sources)
    strong = [f for f in matched if f.get("epistemic_status") in _STRONG_EPISTEMIC]
    strong_supported = _resolve_sources(strong, known_sources)

    if matched and strong_supported:
        return {
            "issue_key": f"family.{dimension.key}",
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
        # Gate §5: risco/capacidade sem suporte examinado nunca é complete.
        return {
            "issue_key": f"family.{dimension.key}",
            "status": "partial",
            "conclusion": (
                f"{dimension.title}: alegação registrada, condicionado a "
                "comprovação documental."
            ),
            "factual_refs": [f.get("id") for f in matched if f.get("id")],
            "supporting_source_refs": supporting,
            "adverse_source_refs": [],
            "missing_inputs": [item.expected_evidence[0] for item in dimension.items[:1]],
            "related_claim_ids": [],
            "action_ids": [],
        }
    return {
        "issue_key": f"family.{dimension.key}",
        "status": "blocked",
        "conclusion": f"{dimension.title}: sem elementos nos autos.",
        "factual_refs": [],
        "supporting_source_refs": [],
        "adverse_source_refs": [],
        "missing_inputs": [item.question for item in dimension.items[:1]],
        "related_claim_ids": [],
        "action_ids": [],
    }


class FamilyModule:
    module_id = "family"
    version = "1.0.0"
    supported_areas = ("family",)
    document_types = ("peticao_inicial", "contestacao", "acordo")

    def requirements(self) -> ModuleRequirements:
        return ModuleRequirements(
            required_sections=["parties", "events", "claims", "facts", "evidence"],
            issue_checklists=[d.key for d in FAMILY_MATRIX],
            calculation_rules=["alimentos_scenario@1.0"],
            research_sources=[s["id"] for s in FAMILY_SOURCES],
            evaluation_cases=["family_cases"],
        )

    def analyze(self, case_data: dict) -> dict:
        assessments = [assess_dimension(d.key, case_data or {}) for d in FAMILY_MATRIX]
        complete = [a for a in assessments if a["status"] == "complete"]
        status = "complete" if complete else "partial"
        return {
            "module_id": self.module_id,
            "module_version": self.version,
            "status": status,
            "reason": "Matriz aplicável examinada",
            "issue_assessments": assessments,
            "calculation_ids": [],
            "limitations": [],
        }


def alimentos_scenario(inputs: dict) -> Decimal:
    """Cenário de alimentos: base × percentual; nunca percentual presumido."""
    from app.core.calculations import _require_decimal

    base = inputs.get("base_renda")
    percentual = inputs.get("percentual")
    missing = [k for k, v in (("base_renda", base), ("percentual", percentual)) if v in (None, "")]
    if missing:
        raise CalculationBlockedError(f"alimentos_scenario: entradas faltantes: {', '.join(missing)}")
    return _quantize(_require_decimal(base, "base_renda") * _require_decimal(percentual, "percentual") / Decimal(100))


def register_calculation_rules(registry) -> None:
    registry.register("alimentos_scenario", "1.0", alimentos_scenario)


DESCRIPTOR = {
    "module_id": "family",
    "version": "1.0.0",
    "supported_areas": ["family"],
    "document_types": ["peticao_inicial", "contestacao", "acordo"],
    "required_sections": ["parties", "events", "claims", "facts", "evidence"],
    "issue_checklists": [d.key for d in FAMILY_MATRIX],
    "calculation_rules": ["alimentos_scenario@1.0"],
    "research_sources": [s["id"] for s in FAMILY_SOURCES],
    "evaluation_cases": ["family_cases"],
}
