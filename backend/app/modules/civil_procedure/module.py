"""Módulo cível e processo civil v1.0 (Onda 1A, spec §4)."""

from decimal import Decimal

from app.core.calculations import CalculationBlockedError, _quantize, _require_decimal
from app.core.module_registry import ModuleRequirements
from app.modules.civil_procedure.checklist import CIVIL_PROCEDURE_MATRIX


CIVIL_PROCEDURE_SOURCES = [
    {"id": "cc", "organ": "Planalto",
     "url": "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm"},
    {"id": "cpc", "organ": "Planalto",
     "url": "https://planalto.gov.br/ccivil_03/_ato2015-2018/2015/lei/l13105compilada.htm"},
    {"id": "juizados", "organ": "Planalto",
     "url": "https://www.planalto.gov.br/ccivil_03/leis/l9099.htm"},
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
    """Avalia tema cível com gates §4 (competência, prazo, petição≠prova)."""
    dimension = next(d for d in CIVIL_PROCEDURE_MATRIX if d.key == dimension_key)
    facts = case_data.get("facts", []) or []
    known_sources = {s.get("id") for s in (case_data.get("sources") or []) if s.get("id")}
    matched = _matched_facts(facts, dimension.keywords)
    supporting = _resolve_sources(matched, known_sources)
    strong = [f for f in matched if f.get("epistemic_status") in _STRONG_EPISTEMIC]
    strong_supported = _resolve_sources(strong, known_sources)

    if dimension_key == "rito_competencia" and matched and not strong_supported:
        return {
            "issue_key": f"civil_procedure.{dimension.key}",
            "status": "partial",
            "conclusion": (
                "Competência condicionada: valor isolado não basta; "
                "verificar natureza, partes e rito."
            ),
            "factual_refs": [f.get("id") for f in matched if f.get("id")],
            "supporting_source_refs": supporting,
            "adverse_source_refs": [],
            "missing_inputs": ["natureza da causa", "rito aplicável"],
            "related_claim_ids": [],
            "action_ids": [],
        }
    if dimension_key == "tempo" and matched and not strong_supported:
        return {
            "issue_key": f"civil_procedure.{dimension.key}",
            "status": "partial",
            "conclusion": (
                "Prazo condicionado: sem intimação/marco sustentado não há data final."
            ),
            "factual_refs": [f.get("id") for f in matched if f.get("id")],
            "supporting_source_refs": supporting,
            "adverse_source_refs": [],
            "missing_inputs": ["data de intimação", "marco inicial"],
            "related_claim_ids": [],
            "action_ids": [],
        }
    if matched and strong_supported:
        return {
            "issue_key": f"civil_procedure.{dimension.key}",
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
            "issue_key": f"civil_procedure.{dimension.key}",
            "status": "partial",
            "conclusion": f"{dimension.title}: alegação registrada, condicionado a prova.",
            "factual_refs": [f.get("id") for f in matched if f.get("id")],
            "supporting_source_refs": supporting,
            "adverse_source_refs": [],
            "missing_inputs": [dimension.items[0].expected_evidence[0]],
            "related_claim_ids": [],
            "action_ids": [],
        }
    first_item = dimension.items[0] if dimension.items else None
    missing = (
        list(first_item.expected_evidence[:1])
        if first_item and first_item.expected_evidence
        else [first_item.question if first_item else "elementos do tema"]
    )
    return {
        "issue_key": f"civil_procedure.{dimension.key}",
        "status": "blocked",
        "conclusion": f"{dimension.title}: sem elementos nos autos.",
        "factual_refs": [],
        "supporting_source_refs": [],
        "adverse_source_refs": [],
        "missing_inputs": missing,
        "related_claim_ids": [],
        "action_ids": [],
    }


class CivilProcedureModule:
    module_id = "civil_procedure"
    version = "1.0.0"
    supported_areas = ("civil_procedure",)
    document_types = ("peticao_inicial", "contestacao", "replica", "recurso")

    def requirements(self) -> ModuleRequirements:
        return ModuleRequirements(
            required_sections=["parties", "events", "claims", "facts", "evidence"],
            issue_checklists=[d.key for d in CIVIL_PROCEDURE_MATRIX],
            calculation_rules=["soma_parcelas_documentadas@1.0"],
            research_sources=[s["id"] for s in CIVIL_PROCEDURE_SOURCES],
            evaluation_cases=["civil_procedure_cases"],
        )

    def analyze(self, case_data: dict) -> dict:
        assessments = [assess_dimension(d.key, case_data or {}) for d in CIVIL_PROCEDURE_MATRIX]
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


def soma_parcelas_documentadas(inputs: dict) -> Decimal:
    """Soma parcelas com fonte; sem valor ou sem fonte, bloqueia listando."""
    parcels = inputs.get("parcels") or []
    if not parcels:
        raise CalculationBlockedError("soma_parcelas_documentadas: nenhuma parcela informada")
    missing = [
        str(p.get("label", "?")) for p in parcels
        if p.get("value") in (None, "") or not p.get("source_ref")
    ]
    if missing:
        raise CalculationBlockedError(
            "soma_parcelas_documentadas: parcelas sem valor ou fonte: " + ", ".join(missing)
        )
    total = Decimal("0.00")
    for parcel in parcels:
        total += _require_decimal(parcel["value"], str(parcel.get("label", "?")))
    return _quantize(total)


def register_calculation_rules(registry) -> None:
    registry.register("soma_parcelas_documentadas", "1.0", soma_parcelas_documentadas)


DESCRIPTOR = {
    "module_id": "civil_procedure",
    "version": "1.0.0",
    "supported_areas": ["civil_procedure"],
    "document_types": ["peticao_inicial", "contestacao", "replica", "recurso"],
    "required_sections": ["parties", "events", "claims", "facts", "evidence"],
    "issue_checklists": [d.key for d in CIVIL_PROCEDURE_MATRIX],
    "calculation_rules": ["soma_parcelas_documentadas@1.0"],
    "research_sources": [s["id"] for s in CIVIL_PROCEDURE_SOURCES],
    "evaluation_cases": ["civil_procedure_cases"],
}
