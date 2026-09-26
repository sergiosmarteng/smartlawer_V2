"""Plano de atuação: ordem de trabalho, não cópia das teses (V2 T12, D06).

Organiza prioridades e dependências a partir das teses e das lacunas;
rotulado como derivado — validar antes de protocolar.
"""

from typing import Any


def build_action_plan(analysis_dict: dict[str, Any]) -> str:
    """Gera plano de trabalho ordenado a partir da análise (sem LLM)."""
    theses = analysis_dict.get("defense_theses") or []
    requests = analysis_dict.get("requests") or []
    laws = analysis_dict.get("laws") or []
    steps: list[str] = []
    for index in range(len(theses)):
        steps.append(
            f"Avaliar tese {index + 1} contra provas e pressupostos; "
            f"registrar o que falta elucidar antes de adotá-la."
        )
    if requests:
        steps.append(
            f"Conferir os {len(requests)} pedido(s) um a um nas fontes "
            "e marcar relações de alternatividade/sobreposição."
        )
    if laws:
        steps.append(
            "Verificar vigência e pertinência de cada norma citada "
            "antes de usá-la como fundamento validado."
        )
    steps.append(
        "Produzir provas e diligências pendentes; nada se protocola "
        "automaticamente a partir deste plano."
    )
    header = "Plano de atuação (derivado das teses — validar com o advogado):"
    return header + "\n" + "\n".join(f"{i}. {step}" for i, step in enumerate(steps, start=1))
