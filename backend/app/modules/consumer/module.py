"""Módulo consumidor v1.0 (Onda 1B, spec §7)."""

from decimal import Decimal

from app.core.calculations import CalculationBlockedError, _quantize, _require_decimal
from app.core.module_registry import ModuleRequirements
from app.modules.consumer.checklist import CONSUMER_MATRIX


CONSUMER_SOURCES = [
    {"id": "cdc", "organ": "Planalto",
     "url": "https://planalto.gov.br/ccivil_03/leis/l8078compilado.htm"},
]

_STRONG_EPISTEMIC = ("documented", "admitted")


def _norm(text: str | None) -> str:
    return (text or "").casefold()


def assess_dimension(dimension_key: str, case_data: dict) -> dict:
    """Avalia tema de consumo com gate §7 (sem automatismos)."""
    dimension = next(d for d in CONSUMER_MATRIX if d.key == dimension_key)
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
    if dimension_key in ("relacao_consumo", "cobranca") and matched and not strong:
        auto = {
            "relacao_consumo": "solidariedade e inversão do ônus",
            "cobranca": "restituição em dobro e decadência",
        }[dimension_key]
        return {
            "issue_key": f"consumer.{dimension.key}",
            "status": "partial",
            "conclusion": (
                f"{dimension.title}: sem {auto} automáticos; "
                "exigem premissas e fonte jurídica verificadas."
            ),
            "factual_refs": [f.get("id") for f in matched if f.get("id")],
            "supporting_source_refs": supporting,
            "adverse_source_refs": [],
            "missing_inputs": [dimension.items[0].expected_evidence[0]],
            "related_claim_ids": [],
            "action_ids": [],
        }
    if matched and strong:
        return {
            "issue_key": f"consumer.{dimension.key}",
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
            "issue_key": f"consumer.{dimension.key}",
            "status": "partial",
            "conclusion": (
                f"{dimension.title}: print/conversa preserva metadados e contexto, "
                "mas não confirma sozinho titularidade ou integridade."
                if dimension_key in ("oferta_contrato", "dados_plataforma")
                else f"{dimension.title}: alegação registrada, condicionado a prova."
            ),
            "factual_refs": [f.get("id") for f in matched if f.get("id")],
            "supporting_source_refs": supporting,
            "adverse_source_refs": [],
            "missing_inputs": [dimension.items[0].expected_evidence[0]],
            "related_claim_ids": [],
            "action_ids": [],
        }
    return {
        "issue_key": f"consumer.{dimension.key}",
        "status": "blocked",
        "conclusion": f"{dimension.title}: sem elementos nos autos.",
        "factual_refs": [],
        "supporting_source_refs": [],
        "adverse_source_refs": [],
        "missing_inputs": [dimension.items[0].question],
        "related_claim_ids": [],
        "action_ids": [],
    }


class ConsumerModule:
    module_id = "consumer"
    version = "1.0.0"
    supported_areas = ("consumer",)
    document_types = ("peticao_inicial", "contestacao", "reclamacao")

    def requirements(self) -> ModuleRequirements:
        return ModuleRequirements(
            required_sections=["parties", "events", "claims", "facts", "evidence"],
            issue_checklists=[d.key for d in CONSUMER_MATRIX],
            calculation_rules=["restituicao_cobranca@1.0"],
            research_sources=[s["id"] for s in CONSUMER_SOURCES],
            evaluation_cases=["consumer_cases"],
        )

    def analyze(self, case_data: dict) -> dict:
        assessments = [assess_dimension(d.key, case_data or {}) for d in CONSUMER_MATRIX]
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


def restituicao_cobranca(inputs: dict) -> Decimal:
    """Diferença de cobrança: cobrado − pago − estornado, sob regra validada."""
    missing = [k for k in ("cobrado", "pago") if inputs.get(k) in (None, "")]
    if missing:
        raise CalculationBlockedError(
            "restituicao_cobranca: entradas faltantes: " + ", ".join(missing)
        )
    duplicadas = inputs.get("faturas_duplicadas") or []
    if duplicadas:
        raise CalculationBlockedError(
            "restituicao_cobranca: duplicidade a verificar: " + ", ".join(map(str, duplicadas))
        )
    total = (
        _require_decimal(inputs["cobrado"], "cobrado")
        - _require_decimal(inputs["pago"], "pago")
        - _require_decimal(inputs.get("estornado", "0"), "estornado")
    )
    return _quantize(total)


def register_calculation_rules(registry) -> None:
    registry.register("restituicao_cobranca", "1.0", restituicao_cobranca)


DESCRIPTOR = {
    "module_id": "consumer",
    "version": "1.0.0",
    "supported_areas": ["consumer"],
    "document_types": ["peticao_inicial", "contestacao", "reclamacao"],
    "required_sections": ["parties", "events", "claims", "facts", "evidence"],
    "issue_checklists": [d.key for d in CONSUMER_MATRIX],
    "calculation_rules": ["restituicao_cobranca@1.0"],
    "research_sources": [s["id"] for s in CONSUMER_SOURCES],
    "evaluation_cases": ["consumer_cases"],
}
