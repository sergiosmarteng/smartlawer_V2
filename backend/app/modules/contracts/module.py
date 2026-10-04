"""Módulo contratos v1.0 (Onda 2A, spec §4)."""

from decimal import Decimal

from app.core.calculations import CalculationBlockedError, _quantize, _require_decimal
from app.core.module_registry import ModuleRequirements
from app.modules.contracts.checklist import CONTRACTS_MATRIX


CONTRACTS_SOURCES = [
    {"id": "cc", "organ": "Planalto",
     "url": "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm"},
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


def diff_versions(old_clauses: list[dict], new_clauses: list[dict]) -> list[dict]:
    """Diff de cláusulas por id estável, preservando texto original e posição (§4)."""
    old_by_id = {c.get("id"): c for c in (old_clauses or []) if c.get("id")}
    new_by_id = {c.get("id"): c for c in (new_clauses or []) if c.get("id")}
    diff: list[dict] = []
    for cid, old in old_by_id.items():
        new = new_by_id.get(cid)
        if new is None:
            diff.append({"clause_id": cid, "change": "removed",
                         "old_text": old.get("text"), "new_text": None,
                         "position": old.get("position")})
        elif new.get("text") != old.get("text"):
            diff.append({"clause_id": cid, "change": "changed",
                         "old_text": old.get("text"), "new_text": new.get("text"),
                         "position": new.get("position", old.get("position"))})
    for cid, new in new_by_id.items():
        if cid not in old_by_id:
            diff.append({"clause_id": cid, "change": "added",
                         "old_text": None, "new_text": new.get("text"),
                         "position": new.get("position")})
    return diff


def assess_dimension(dimension_key: str, case_data: dict) -> dict:
    """Avalia tema contratual com gates §4 (sem conclusão em abstrato)."""
    dimension = next(d for d in CONTRACTS_MATRIX if d.key == dimension_key)
    facts = case_data.get("facts", []) or []
    known_sources = {s.get("id") for s in (case_data.get("sources") or []) if s.get("id")}
    matched = _matched_facts(facts, dimension.keywords)
    supporting = _resolve_sources(matched, known_sources)
    strong = [f for f in matched if f.get("epistemic_status") in _STRONG_EPISTEMIC]
    strong_supported = _resolve_sources(strong, known_sources)

    if dimension_key == "financeiro" and matched and not strong_supported:
        return {
            "issue_key": f"contracts.{dimension.key}",
            "status": "blocked",
            "conclusion": (
                f"{dimension.title}: reajuste/multa exigem cláusula vigente, "
                "base, índice, termo e período verificados."
            ),
            "factual_refs": [f.get("id") for f in matched if f.get("id")],
            "supporting_source_refs": supporting,
            "adverse_source_refs": [],
            "missing_inputs": ["cláusula vigente", "base", "índice", "termo", "período"],
            "related_claim_ids": [],
            "action_ids": [],
        }
    if matched and strong_supported:
        return {
            "issue_key": f"contracts.{dimension.key}",
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
            "issue_key": f"contracts.{dimension.key}",
            "status": "partial",
            "conclusion": (
                f"{dimension.title}: sem validade ou abusividade em abstrato; "
                "conclusão exige relação material, legislação e fatos."
            ),
            "factual_refs": [f.get("id") for f in matched if f.get("id")],
            "supporting_source_refs": supporting,
            "adverse_source_refs": [],
            "missing_inputs": [dimension.items[0].expected_evidence[0]],
            "related_claim_ids": [],
            "action_ids": [],
        }
    return {
        "issue_key": f"contracts.{dimension.key}",
        "status": "blocked",
        "conclusion": f"{dimension.title}: sem elementos nos autos.",
        "factual_refs": [],
        "supporting_source_refs": [],
        "adverse_source_refs": [],
        "missing_inputs": [dimension.items[0].question],
        "related_claim_ids": [],
        "action_ids": [],
    }


class ContractsModule:
    module_id = "contracts"
    version = "1.0.0"
    supported_areas = ("contracts",)
    document_types = ("contrato", "aditivo", "minuta", "notificacao")

    def requirements(self) -> ModuleRequirements:
        return ModuleRequirements(
            required_sections=["parties", "events", "claims", "facts", "evidence"],
            issue_checklists=[d.key for d in CONTRACTS_MATRIX],
            calculation_rules=["reajuste_contratual@1.0"],
            research_sources=[s["id"] for s in CONTRACTS_SOURCES],
            evaluation_cases=["contracts_cases"],
        )

    def analyze(self, case_data: dict) -> dict:
        assessments = [assess_dimension(d.key, case_data or {}) for d in CONTRACTS_MATRIX]
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


def reajuste_contratual(inputs: dict) -> Decimal:
    """Reajuste com cláusula vigente, base, índice, termo e período (§4)."""
    missing = [k for k in ("base", "indice_percentual", "termo", "periodo")
               if inputs.get(k) in (None, "")]
    if not inputs.get("clausula_vigente"):
        missing = ["clausula_vigente", *missing]
    if missing:
        raise CalculationBlockedError(
            f"reajuste_contratual: entradas faltantes: {', '.join(missing)}")
    base = _require_decimal(inputs["base"], "base")
    indice = _require_decimal(inputs["indice_percentual"], "indice_percentual")
    return _quantize(base * (Decimal(1) + indice / Decimal(100)))


def register_calculation_rules(registry) -> None:
    registry.register("reajuste_contratual", "1.0", reajuste_contratual)


DESCRIPTOR = {
    "module_id": "contracts",
    "version": "1.0.0",
    "supported_areas": ["contracts"],
    "document_types": ["contrato", "aditivo", "minuta", "notificacao"],
    "required_sections": ["parties", "events", "claims", "facts", "evidence"],
    "issue_checklists": [d.key for d in CONTRACTS_MATRIX],
    "calculation_rules": ["reajuste_contratual@1.0"],
    "research_sources": [s["id"] for s in CONTRACTS_SOURCES],
    "evaluation_cases": ["contracts_cases"],
}
