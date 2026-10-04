"""Módulo empresarial e societário v1.0 (Onda 2A, spec §3)."""

from decimal import Decimal

from app.core.calculations import CalculationBlockedError, _quantize, _require_decimal
from app.core.module_registry import ModuleRequirements
from app.modules.corporate.checklist import CORPORATE_MATRIX


CORPORATE_SOURCES = [
    {"id": "cc", "organ": "Planalto",
     "url": "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm"},
    {"id": "lei6404", "organ": "Planalto",
     "url": "https://www.planalto.gov.br/ccivil_03/leis/l6404consol.htm"},
    {"id": "lei11101", "organ": "Planalto",
     "url": "https://www.planalto.gov.br/ccivil_03/_ato2004-2006/2005/lei/l11101compilado.htm"},
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
    """Avalia tema societário com gates §3 (sem responsabilidade por posição)."""
    dimension = next(d for d in CORPORATE_MATRIX if d.key == dimension_key)
    facts = case_data.get("facts", []) or []
    known_sources = {s.get("id") for s in (case_data.get("sources") or []) if s.get("id")}
    matched = _matched_facts(facts, dimension.keywords)
    supporting = _resolve_sources(matched, known_sources)
    strong = [f for f in matched if f.get("epistemic_status") in _STRONG_EPISTEMIC]
    strong_supported = _resolve_sources(strong, known_sources)

    if dimension_key in ("obrigacoes", "governanca") and matched and not strong_supported:
        return {
            "issue_key": f"corporate.{dimension.key}",
            "status": "partial",
            "conclusion": (
                f"{dimension.title}: responsabilidade não atribuída por posição "
                "societária; exige conduta e prova."
            ),
            "factual_refs": [f.get("id") for f in matched if f.get("id")],
            "supporting_source_refs": supporting,
            "adverse_source_refs": [],
            "missing_inputs": ["conduta documentada", "prova do ato"],
            "related_claim_ids": [],
            "action_ids": [],
        }
    if dimension_key == "crise" and matched:
        stages = {"pedido", "deferimento", "concessão", "concessao"}
        haystack = " ".join(f.get("statement", "") for f in matched).casefold()
        if not any(stage in haystack for stage in ("deferi", "concess", "concedi")):
            return {
                "issue_key": f"corporate.{dimension.key}",
                "status": "partial",
                "conclusion": (
                    f"{dimension.title}: pedido registrado; deferimento e "
                    "concessão ainda não distinguidos nos autos."
                ),
                "factual_refs": [f.get("id") for f in matched if f.get("id")],
                "supporting_source_refs": supporting,
                "adverse_source_refs": [],
                "missing_inputs": ["decisão de deferimento/concessão"],
                "related_claim_ids": [],
                "action_ids": [],
            }
    if matched and strong_supported:
        return {
            "issue_key": f"corporate.{dimension.key}",
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
            "issue_key": f"corporate.{dimension.key}",
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
        "issue_key": f"corporate.{dimension.key}",
        "status": "blocked",
        "conclusion": f"{dimension.title}: sem elementos nos autos.",
        "factual_refs": [],
        "supporting_source_refs": [],
        "adverse_source_refs": [],
        "missing_inputs": [dimension.items[0].question],
        "related_claim_ids": [],
        "action_ids": [],
    }


class CorporateModule:
    module_id = "corporate"
    version = "1.0.0"
    supported_areas = ("corporate",)
    document_types = ("contrato_social", "estatuto", "ata", "alteracao_contratual")

    def requirements(self) -> ModuleRequirements:
        return ModuleRequirements(
            required_sections=["parties", "events", "claims", "facts", "evidence"],
            issue_checklists=[d.key for d in CORPORATE_MATRIX],
            calculation_rules=["participacao_societaria@1.0", "rateio_cenario@1.0"],
            research_sources=[s["id"] for s in CORPORATE_SOURCES],
            evaluation_cases=["corporate_cases"],
        )

    def analyze(self, case_data: dict) -> dict:
        assessments = [assess_dimension(d.key, case_data or {}) for d in CORPORATE_MATRIX]
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


def participacao_societaria(inputs: dict) -> Decimal:
    """Participação por quotas documentadas (sem avaliação econômica inventada)."""
    quotas = inputs.get("quotas") or []
    if not quotas:
        raise CalculationBlockedError("participacao_societaria: quotas documentadas ausentes")
    missing = [str(q.get("socio", "?")) for q in quotas
               if q.get("quantidade") in (None, "") or not q.get("fonte")]
    if missing:
        raise CalculationBlockedError(
            "participacao_societaria: quotas sem quantidade ou fonte: " + ", ".join(missing))
    total = sum(_require_decimal(q["quantidade"], "quantidade") for q in quotas)
    if total == 0:
        raise CalculationBlockedError("participacao_societaria: total de quotas zerado")
    alvo = _require_decimal(inputs.get("socio_quantidade", "0"), "socio_quantidade")
    return _quantize(alvo * Decimal(100) / total)


def rateio_cenario(inputs: dict) -> Decimal:
    """Rateio parametrizado de cenário (sem valor de empresa inventado)."""
    missing = [k for k in ("montante", "criterio") if inputs.get(k) in (None, "")]
    if missing:
        raise CalculationBlockedError(
            "rateio_cenario: entradas faltantes: " + ", ".join(missing))
    montante = _require_decimal(inputs["montante"], "montante")
    fracao = _require_decimal(inputs.get("fracao_percentual", "100"), "fracao_percentual")
    return _quantize(montante * fracao / Decimal(100))


def register_calculation_rules(registry) -> None:
    registry.register("participacao_societaria", "1.0", participacao_societaria)
    registry.register("rateio_cenario", "1.0", rateio_cenario)


DESCRIPTOR = {
    "module_id": "corporate",
    "version": "1.0.0",
    "supported_areas": ["corporate"],
    "document_types": ["contrato_social", "estatuto", "ata", "alteracao_contratual"],
    "required_sections": ["parties", "events", "claims", "facts", "evidence"],
    "issue_checklists": [d.key for d in CORPORATE_MATRIX],
    "calculation_rules": ["participacao_societaria@1.0", "rateio_cenario@1.0"],
    "research_sources": [s["id"] for s in CORPORATE_SOURCES],
    "evaluation_cases": ["corporate_cases"],
}
