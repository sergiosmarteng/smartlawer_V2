"""Módulo administrativo v1.0 (Onda 2B, spec §6)."""

from decimal import Decimal

from app.core.calculations import CalculationBlockedError, _quantize, _require_decimal
from app.core.module_registry import ModuleRequirements
from app.modules.administrative.checklist import ADMINISTRATIVE_MATRIX


ADMINISTRATIVE_SOURCES = [
    {"id": "lei14133", "organ": "Planalto",
     "url": "https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2021/lei/l14133.htm"},
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
    """Avalia tema administrativo com gates §6 (sem sanção/nulidade presumidas)."""
    dimension = next(d for d in ADMINISTRATIVE_MATRIX if d.key == dimension_key)
    facts = case_data.get("facts", []) or []
    known_sources = {s.get("id") for s in (case_data.get("sources") or []) if s.get("id")}
    matched = _matched_facts(facts, dimension.keywords)
    supporting = _resolve_sources(matched, known_sources)
    strong = [f for f in matched if f.get("epistemic_status") in _STRONG_EPISTEMIC]
    strong_supported = _resolve_sources(strong, known_sources)

    if dimension_key == "responsabilizacao" and matched and not strong_supported:
        haystack = " ".join(f.get("statement", "") for f in matched).casefold()
        preliminary = any(w in haystack for w in ("notícia", "noticia", "denúncia", "denuncia", "relatório preliminar", "relatorio"))
        conclusion = (
            f"{dimension.title}: notícia/denúncia não é sanção final; "
            if preliminary else
            f"{dimension.title}: imputação exige prova e defesa; "
        ) + "questão bilateral condicionada."
        return {
            "issue_key": f"administrative.{dimension.key}",
            "status": "partial",
            "conclusion": conclusion,
            "factual_refs": [f.get("id") for f in matched if f.get("id")],
            "supporting_source_refs": supporting,
            "adverse_source_refs": [],
            "missing_inputs": ["decisão final", "prova da imputação"],
            "related_claim_ids": [],
            "action_ids": [],
        }
    if matched and strong_supported:
        return {
            "issue_key": f"administrative.{dimension.key}",
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
            "issue_key": f"administrative.{dimension.key}",
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
        "issue_key": f"administrative.{dimension.key}",
        "status": "blocked",
        "conclusion": f"{dimension.title}: sem elementos nos autos.",
        "factual_refs": [],
        "supporting_source_refs": [],
        "adverse_source_refs": [],
        "missing_inputs": [dimension.items[0].question],
        "related_claim_ids": [],
        "action_ids": [],
    }


class AdministrativeModule:
    module_id = "administrative"
    version = "1.0.0"
    supported_areas = ("administrative",)
    document_types = ("edital", "contrato_administrativo", "auto", "recurso")

    def requirements(self) -> ModuleRequirements:
        return ModuleRequirements(
            required_sections=["parties", "events", "claims", "facts", "evidence"],
            issue_checklists=[d.key for d in ADMINISTRATIVE_MATRIX],
            calculation_rules=["reajuste_contrato_publico@1.0"],
            research_sources=[s["id"] for s in ADMINISTRATIVE_SOURCES],
            evaluation_cases=["administrative_cases"],
        )

    def analyze(self, case_data: dict) -> dict:
        assessments = [assess_dimension(d.key, case_data or {}) for d in ADMINISTRATIVE_MATRIX]
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


def reajuste_contrato_publico(inputs: dict) -> Decimal:
    """Reajuste/reequilíbrio/multa com cláusula, fato, período e índice (§6)."""
    missing = [k for k in ("clausula", "fato", "periodo", "indice")
               if inputs.get(k) in (None, "")]
    if missing:
        raise CalculationBlockedError(
            "reajuste_contrato_publico: entradas faltantes: " + ", ".join(missing))
    base = _require_decimal(inputs.get("base", "0"), "base")
    indice = _require_decimal(inputs["indice"], "indice")
    return _quantize(base * (Decimal(1) + indice / Decimal(100)))


def register_calculation_rules(registry) -> None:
    registry.register("reajuste_contrato_publico", "1.0", reajuste_contrato_publico)


DESCRIPTOR = {
    "module_id": "administrative",
    "version": "1.0.0",
    "supported_areas": ["administrative"],
    "document_types": ["edital", "contrato_administrativo", "auto", "recurso"],
    "required_sections": ["parties", "events", "claims", "facts", "evidence"],
    "issue_checklists": [d.key for d in ADMINISTRATIVE_MATRIX],
    "calculation_rules": ["reajuste_contrato_publico@1.0"],
    "research_sources": [s["id"] for s in ADMINISTRATIVE_SOURCES],
    "evaluation_cases": ["administrative_cases"],
}
