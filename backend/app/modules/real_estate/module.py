"""Módulo imobiliário v1.0 (Onda 2B, spec §7)."""

from decimal import Decimal

from app.core.calculations import CalculationBlockedError, _quantize, _require_decimal
from app.core.module_registry import ModuleRequirements
from app.modules.real_estate.checklist import REAL_ESTATE_MATRIX


REAL_ESTATE_SOURCES = [
    {"id": "cc", "organ": "Planalto",
     "url": "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm"},
    {"id": "lrp", "organ": "Planalto",
     "url": "https://www.planalto.gov.br/ccivil_03/leis/l6015consolidado.htm"},
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
    """Avalia tema imobiliário com gates §7 (sem titularidade/regularidade presumidas)."""
    dimension = next(d for d in REAL_ESTATE_MATRIX if d.key == dimension_key)
    facts = case_data.get("facts", []) or []
    known_sources = {s.get("id") for s in (case_data.get("sources") or []) if s.get("id")}
    matched = _matched_facts(facts, dimension.keywords)
    supporting = _resolve_sources(matched, known_sources)
    strong = [f for f in matched if f.get("epistemic_status") in _STRONG_EPISTEMIC]
    strong_supported = _resolve_sources(strong, known_sources)

    if dimension_key in ("imovel", "registro") and matched and not strong_supported:
        return {
            "issue_key": f"real_estate.{dimension.key}",
            "status": "partial",
            "conclusion": (
                f"{dimension.title}: matrícula antiga não prova titularidade atual; "
                "exigir certidão atualizada."
            ),
            "factual_refs": [f.get("id") for f in matched if f.get("id")],
            "supporting_source_refs": supporting,
            "adverse_source_refs": [],
            "missing_inputs": ["certidão atualizada da matrícula"],
            "related_claim_ids": [],
            "action_ids": [],
        }
    if dimension_key == "direito" and matched:
        haystack = " ".join(f.get("statement", "") for f in matched).casefold()
        if not any(w in haystack for w in ("posse", "domínio", "dominio", "obrigacional", "propriedade")):
            return {
                "issue_key": f"real_estate.{dimension.key}",
                "status": "partial",
                "conclusion": (
                    f"{dimension.title}: distinguir posse, domínio e direito "
                    "obrigacional antes de concluir."
                ),
                "factual_refs": [f.get("id") for f in matched if f.get("id")],
                "supporting_source_refs": supporting,
                "adverse_source_refs": [],
                "missing_inputs": ["natureza do direito invocado"],
                "related_claim_ids": [],
                "action_ids": [],
            }
    if dimension_key == "urbanismo" and matched and not strong_supported:
        return {
            "issue_key": f"real_estate.{dimension.key}",
            "status": "blocked",
            "conclusion": (
                f"{dimension.title}: regularidade urbanística exige consulta "
                "ao ente competente."
            ),
            "factual_refs": [f.get("id") for f in matched if f.get("id")],
            "supporting_source_refs": supporting,
            "adverse_source_refs": [],
            "missing_inputs": ["manifestação do ente competente"],
            "related_claim_ids": [],
            "action_ids": [],
        }
    if matched and strong_supported:
        return {
            "issue_key": f"real_estate.{dimension.key}",
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
            "issue_key": f"real_estate.{dimension.key}",
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
        "issue_key": f"real_estate.{dimension.key}",
        "status": "blocked",
        "conclusion": f"{dimension.title}: sem elementos nos autos.",
        "factual_refs": [],
        "supporting_source_refs": [],
        "adverse_source_refs": [],
        "missing_inputs": [dimension.items[0].question],
        "related_claim_ids": [],
        "action_ids": [],
    }


class RealEstateModule:
    module_id = "real_estate"
    version = "1.0.0"
    supported_areas = ("real_estate",)
    document_types = ("matricula", "escritura", "contrato", "certidao")

    def requirements(self) -> ModuleRequirements:
        return ModuleRequirements(
            required_sections=["parties", "events", "claims", "facts", "evidence"],
            issue_checklists=[d.key for d in REAL_ESTATE_MATRIX],
            calculation_rules=["parcelas_mora_rateio@1.0"],
            research_sources=[s["id"] for s in REAL_ESTATE_SOURCES],
            evaluation_cases=["real_estate_cases"],
        )

    def analyze(self, case_data: dict) -> dict:
        assessments = [assess_dimension(d.key, case_data or {}) for d in REAL_ESTATE_MATRIX]
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


def parcelas_mora_rateio(inputs: dict) -> Decimal:
    """Parcelas/mora/rateio com contrato, pagamentos e índices (§7)."""
    missing = [k for k in ("contrato", "parcelas", "pagamentos", "indice")
               if inputs.get(k) in (None, "")]
    if missing:
        raise CalculationBlockedError(
            "parcelas_mora_rateio: entradas faltantes: " + ", ".join(missing))
    total_parcelas = sum(
        (_require_decimal(p, "parcela") for p in (inputs.get("parcelas") or [])),
        Decimal("0"),
    )
    total_pagamentos = sum(
        (_require_decimal(p, "pagamento") for p in (inputs.get("pagamentos") or [])),
        Decimal("0"),
    )
    indice = _require_decimal(inputs["indice"], "indice")
    saldo = total_parcelas - total_pagamentos
    return _quantize(saldo * (Decimal(1) + indice / Decimal(100)))


def register_calculation_rules(registry) -> None:
    registry.register("parcelas_mora_rateio", "1.0", parcelas_mora_rateio)


DESCRIPTOR = {
    "module_id": "real_estate",
    "version": "1.0.0",
    "supported_areas": ["real_estate"],
    "document_types": ["matricula", "escritura", "contrato", "certidao"],
    "required_sections": ["parties", "events", "claims", "facts", "evidence"],
    "issue_checklists": [d.key for d in REAL_ESTATE_MATRIX],
    "calculation_rules": ["parcelas_mora_rateio@1.0"],
    "research_sources": [s["id"] for s in REAL_ESTATE_SOURCES],
    "evaluation_cases": ["real_estate_cases"],
}
