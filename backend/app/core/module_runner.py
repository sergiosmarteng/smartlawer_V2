"""Runner de módulos especializados (Onda 1 fundação, spec §2 + §13.5).

Executa cada módulo resolvido sobre o caso reconciliado e produz
`module_results[module_id]`. Falha de um módulo vira `blocked` +
limitação declarada — nunca impede o dossiê universal nem muta o
núcleo (fatos, pedidos, fontes intactos).
"""

from __future__ import annotations

from typing import Protocol


class ModuleAnalyzer(Protocol):
    module_id: str
    version: str
    supported_areas: tuple[str, ...]

    def analyze(self, case_data: dict) -> dict: ...


def _blocked_result(module, reason: str) -> dict:
    return {
        "module_id": getattr(module, "module_id", "unknown"),
        "module_version": getattr(module, "version", "0.0.0"),
        "status": "blocked",
        "reason": reason,
        "issue_assessments": [],
        "calculation_ids": [],
        "limitations": [reason],
    }


def run_module_analyses(
    *,
    modules: list,
    case_data: dict,
) -> tuple[dict[str, dict], list[dict]]:
    """Roda módulos; retorna (module_results, limitations)."""
    results: dict[str, dict] = {}
    limitations: list[dict] = []
    for module in modules or []:
        module_id = getattr(module, "module_id", "unknown")
        if module_id == "universal":
            continue
        analyze = getattr(module, "analyze", None)
        if analyze is None:
            reason = (
                f"Módulo '{module_id}' sem analisador instalado; "
                "núcleo universal preservado."
            )
            results[module_id] = _blocked_result(module, reason)
            limitations.append({"code": "SPECIALIZATION_UNAVAILABLE", "message": reason})
            continue
        try:
            payload = analyze(dict(case_data or {}))
        except Exception as exc:
            reason = (
                f"Módulo '{module_id}' indisponível nesta execução "
                f"({type(exc).__name__}); núcleo universal preservado."
            )
            results[module_id] = _blocked_result(module, reason)
            limitations.append({"code": "SPECIALIZATION_UNAVAILABLE", "message": reason})
            continue
        if not isinstance(payload, dict):
            reason = f"Módulo '{module_id}' retornou saída fora do schema."
            results[module_id] = _blocked_result(module, reason)
            limitations.append({"code": "SPECIALIZATION_UNAVAILABLE", "message": reason})
            continue
        payload.setdefault("module_id", module_id)
        payload.setdefault("module_version", getattr(module, "version", "1.0.0"))
        payload.setdefault("status", "complete")
        payload.setdefault("reason", "")
        payload.setdefault("issue_assessments", [])
        payload.setdefault("calculation_ids", [])
        payload.setdefault("limitations", [])
        results[module_id] = payload
    return results, limitations
