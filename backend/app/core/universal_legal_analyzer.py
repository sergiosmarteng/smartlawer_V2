"""Análise jurídica universal bilateral (Onda 0 Task 8, §8.8).

Analisa questões transversais usando somente objetos reconciliados e
fontes registradas. Produz questões processuais, teses bilaterais,
riscos, ações, perguntas e limitações. Resposta vazia ou genérica do
provedor é rejeitada — nunca vira dossiê.
"""

from __future__ import annotations

from datetime import date
from typing import Protocol


class UniversalAnalysisError(Exception):
    """Análise universal inválida: código seguro, sem conteúdo do caso."""

    def __init__(self, code: str, safe_message: str):
        super().__init__(safe_message)
        self.code = code


class AnalysisProvider(Protocol):
    def analyze(self, payload: dict) -> dict: ...


# Frases genéricas banidas (legado FALLBACK_THESES, removido na Task 1).
_BANNED_GENERIC_FRAGMENTS = (
    "exigir comprovacao documental integral",
    "questionar o nexo entre os fatos narrados",
    "avaliar preliminares processuais e inconsistencias",
)


def _is_generic(text: str | None) -> bool:
    normalized = (text or "").lower()
    return any(fragment in normalized for fragment in _BANNED_GENERIC_FRAGMENTS)


def analyze_universal_case(
    data: dict,
    *,
    modules: list,
    represented_side: str,
    objective: str | None,
    reference_date,
    provider: AnalysisProvider,
) -> dict:
    """Executa análise universal bilateral com validação de IDs e refs."""
    fact_ids = {f.get("id") for f in (data.get("facts") or []) if f.get("id")}
    source_ids = {s.get("id") for s in (data.get("sources") or []) if s.get("id")}
    legal_ids = {r.get("id") for r in (data.get("legal_references") or []) if r.get("id")}
    valid_sides = {"claimant", "respondent", "third_party", "neutral"}
    if represented_side not in valid_sides:
        raise UniversalAnalysisError("INVALID_SIDE", "Polo representado inválido.")

    payload = {
        "facts": data.get("facts") or [],
        "claims": data.get("claims") or [],
        "evidence": data.get("evidence") or [],
        "represented_side": represented_side,
        "objective": objective,
        "reference_date": reference_date.isoformat() if isinstance(reference_date, date) else reference_date,
        "modules": [getattr(m, "module_id", m) for m in (modules or [])],
    }
    try:
        result = provider.analyze(payload)
    except UniversalAnalysisError:
        raise
    except Exception as exc:
        raise UniversalAnalysisError("UNIVERSAL_PROVIDER_FAILED", "Provedor de análise indisponível.") from exc
    if not isinstance(result, dict):
        raise UniversalAnalysisError("UNIVERSAL_INVALID_OUTPUT", "Saída da análise fora do schema.")
    theses = result.get("theses") or []
    has_input = bool(data.get("facts") or data.get("claims"))
    if not theses and has_input:
        raise UniversalAnalysisError("UNIVERSAL_EMPTY_THESES", "Análise sem teses; lote rejeitado.")
    for thesis in theses:
        if _is_generic(thesis.get("conclusion")) or _is_generic(thesis.get("issue")):
            raise UniversalAnalysisError("UNIVERSAL_GENERIC_THESIS", "Tese genérica rejeitada.")
        for premise in thesis.get("factual_premises") or []:
            if premise not in fact_ids:
                raise UniversalAnalysisError(
                    "UNIVERSAL_UNKNOWN_PREMISE", f"Premissa factual desconhecida: {premise}."
                )
        for premise in thesis.get("legal_premises") or []:
            if premise not in legal_ids:
                raise UniversalAnalysisError(
                    "UNIVERSAL_UNKNOWN_PREMISE", f"Premissa jurídica desconhecida: {premise}."
                )
        for ref in [*thesis.get("supporting_refs", []), *thesis.get("adverse_refs", [])]:
            if ref not in source_ids:
                raise UniversalAnalysisError(
                    "UNIVERSAL_UNKNOWN_SOURCE", f"Fonte desconhecida em tese: {ref}."
                )

    limitations = list(result.get("limitations") or [])
    if not fact_ids and not any(lim.get("code") == "SPECIALIZATION_UNAVAILABLE" for lim in limitations):
        limitations.append(
            {
                "code": "SPECIALIZATION_UNAVAILABLE",
                "message": (
                    "Assunto sem módulo especializado instalado; núcleo universal "
                    "produziu análise com limitação declarada."
                ),
            }
        )
    actions = list(result.get("actions") or [])
    questions = list(result.get("questions") or [])
    if reference_date is None:
        if not any("prescri" in str(a.get("description") or "").lower() for a in actions):
            actions.append(
                {
                    "id": "action-reference-date",
                    "description": (
                        "Informar a data jurídica de referência: sem ela, "
                        "prescrição e decadência ficam bloqueadas."
                    ),
                    "priority": "high",
                }
            )
        questions.append(
            {
                "id": "question-reference-date",
                "question": "Qual a data jurídica de referência para avaliar prazos?",
            }
        )
    return {
        "procedural_issues": list(result.get("procedural_issues") or []),
        "theses": [dict(t) for t in theses],
        "risks": list(result.get("risks") or []),
        "actions": actions,
        "questions": questions,
        "limitations": limitations,
    }
