"""Módulo previdenciário v1.0 (Onda 1B, spec §8)."""

from decimal import Decimal

from app.core.calculations import CalculationBlockedError, _quantize, _require_decimal
from app.core.module_registry import ModuleRequirements
from app.modules.social_security.checklist import SOCIAL_SECURITY_MATRIX


SOCIAL_SECURITY_SOURCES = [
    {"id": "lei8213", "organ": "Planalto",
     "url": "https://www.planalto.gov.br/ccivil_03/leis/l8213compilado.htm"},
    {"id": "lei8212", "organ": "Planalto",
     "url": "https://planalto.gov.br/ccivil_03/leis/l8212compilado.htm"},
    {"id": "inss", "organ": "INSS",
     "url": "https://www.gov.br/inss/pt-br"},
]

_STRONG_EPISTEMIC = ("documented", "admitted")


def _norm(text: str | None) -> str:
    return (text or "").casefold()


def assess_dimension(dimension_key: str, case_data: dict) -> dict:
    """Avalia tema previdenciário com gates §8 (sem diagnóstico, sem presunção)."""
    dimension = next(d for d in SOCIAL_SECURITY_MATRIX if d.key == dimension_key)
    facts = case_data.get("facts", []) or []
    known_sources = {s.get("id") for s in (case_data.get("sources") or []) if s.get("id")}
    matched = [
        f for f in facts
        if any(kw in _norm(f"{f.get('statement', '')} {f.get('id', '')}")
               for kw in dimension.keywords)
    ]
    supporting = sorted({
        ref for f in matched for ref in (f.get("source_refs", []) or [])
        if ref in known_sources
    })
    strong = [
        f for f in matched
        if f.get("epistemic_status") in _STRONG_EPISTEMIC
        and any(ref in known_sources for ref in (f.get("source_refs", []) or []))
    ]
    if dimension_key == "incapacidade" and matched:
        conclusion_suffix = (
            "matriz documental, sem diagnóstico próprio; "
            if strong else
            "aguardando perícia; nenhum diagnóstico emitido pelo sistema; "
        )
        return {
            "issue_key": f"social_security.{dimension.key}",
            "status": "complete" if strong else "partial",
            "conclusion": f"{dimension.title}: {conclusion_suffix}".rstrip(),
            "factual_refs": [f.get("id") for f in matched if f.get("id")],
            "supporting_source_refs": supporting,
            "adverse_source_refs": [],
            "missing_inputs": [] if strong else ["laudo ou perícia com DII"],
            "related_claim_ids": [],
            "action_ids": [],
        }
    if matched and strong:
        return {
            "issue_key": f"social_security.{dimension.key}",
            "status": "complete",
            "conclusion": f"{dimension.title}: premissas sustentadas por fonte examinada.",
            "factual_refs": [f.get("id") for f in matched if f.get("id")],
            "supporting_source_refs": supporting,
            "adverse_source_refs": [],
            "missing_inputs": [],
            "related_claim_ids": [],
            "action_ids": [],
        }
    if matched:
        return {
            "issue_key": f"social_security.{dimension.key}",
            "status": "partial",
            "conclusion": (
                f"{dimension.title}: sem benefício ou retroativo presumido; "
                "aguardar documentos."
            ),
            "factual_refs": [f.get("id") for f in matched if f.get("id")],
            "supporting_source_refs": supporting,
            "adverse_source_refs": [],
            "missing_inputs": [dimension.items[0].expected_evidence[0]],
            "related_claim_ids": [],
            "action_ids": [],
        }
    return {
        "issue_key": f"social_security.{dimension.key}",
        "status": "blocked",
        "conclusion": f"{dimension.title}: sem elementos nos autos.",
        "factual_refs": [],
        "supporting_source_refs": [],
        "adverse_source_refs": [],
        "missing_inputs": [dimension.items[0].question],
        "related_claim_ids": [],
        "action_ids": [],
    }


class SocialSecurityModule:
    module_id = "social_security"
    version = "1.0.0"
    supported_areas = ("social_security",)
    document_types = ("requerimento", "recurso_administrativo", "peticao_inicial")

    def requirements(self) -> ModuleRequirements:
        return ModuleRequirements(
            required_sections=["parties", "events", "claims", "facts", "evidence"],
            issue_checklists=[d.key for d in SOCIAL_SECURITY_MATRIX],
            calculation_rules=["beneficio_cenario@1.0"],
            research_sources=[s["id"] for s in SOCIAL_SECURITY_SOURCES],
            evaluation_cases=["social_security_cases"],
        )

    def analyze(self, case_data: dict) -> dict:
        assessments = [assess_dimension(d.key, case_data or {}) for d in SOCIAL_SECURITY_MATRIX]
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


def beneficio_cenario(inputs: dict) -> Decimal:
    """Cenário de benefício: só com regime, espécie, datas, salários e regras."""
    missing = [k for k in ("regime", "especie", "salarios", "regras_temporais")
               if inputs.get(k) in (None, "")]
    if missing:
        raise CalculationBlockedError(
            "beneficio_cenario: entradas faltantes: " + ", ".join(missing)
        )
    total = Decimal("0.00")
    for raw in inputs.get("salarios", []):
        total += _require_decimal(raw, "salario")
    count = len(inputs.get("salarios", [])) or 1
    return _quantize(total / Decimal(count))


def register_calculation_rules(registry) -> None:
    registry.register("beneficio_cenario", "1.0", beneficio_cenario)


DESCRIPTOR = {
    "module_id": "social_security",
    "version": "1.0.0",
    "supported_areas": ["social_security"],
    "document_types": ["requerimento", "recurso_administrativo", "peticao_inicial"],
    "required_sections": ["parties", "events", "claims", "facts", "evidence"],
    "issue_checklists": [d.key for d in SOCIAL_SECURITY_MATRIX],
    "calculation_rules": ["beneficio_cenario@1.0"],
    "research_sources": [s["id"] for s in SOCIAL_SECURITY_SOURCES],
    "evaluation_cases": ["social_security_cases"],
}
