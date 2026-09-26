"""Relatório V2 do artefato validado (T12, §13).

DOCX/PDF futuros geram do MESMO artefato; aqui, Markdown executivo e
completo com escopo, versão, pedidos, teses, memória, ações, limitações
e índice de fontes. Sem nova chamada livre à IA.
"""

MODE_EXECUTIVE = "executive"
MODE_COMPLETE = "complete"


def _claims_lines(claims: list[dict]) -> list[str]:
    lines = []
    for claim in claims or []:
        number = claim.get("original_number")
        title = claim.get("title", "?")
        amount = (claim.get("amount") or {})
        value = amount.get("value") if isinstance(amount, dict) else None
        prefix = f"{number}. " if number else "- "
        suffix = f" — {value} {amount.get('currency', '')}".rstrip() if value else ""
        lines.append(f"{prefix}{title}{suffix}")
    return lines or ["(nenhum pedido registrado)"]


def _sources_index(sources: list[dict]) -> list[str]:
    lines = []
    for source in sources or []:
        page = source.get("page_number")
        quote = (source.get("quote") or "")[:160]
        status = source.get("verification_status", "unverified")
        lines.append(f"- [{source.get('id')}] p.{page} ({status}): {quote}".rstrip())
    return lines or ["(nenhuma fonte)"]


def build_report(
    artifact_content: dict,
    *,
    mode: str = MODE_COMPLETE,
    sources: list[dict] | None = None,
    review_events: list[dict] | None = None,
    artifact_status: str = "partial",
    review_status: str = "pending",
) -> str:
    """Markdown do relatório; parcialidade identificada, nunca oculta."""
    content = artifact_content or {}
    scope = content.get("scope", {})
    coverage = content.get("coverage", {})
    claims = content.get("claims", [])
    limitations = content.get("limitations", [])

    lines = [
        f"# Relatório de análise — {scope.get('module', {}).get('id', 'geral') if isinstance(scope.get('module'), dict) else 'geral'}",
        "",
        f"Versão do esquema: {content.get('schema_version', '2.0')} · "
        f"Estado: {artifact_status} · Revisão humana: {review_status}",
        f"Páginas: {coverage.get('pages_extracted', 0)}/{coverage.get('pages_total', 0)}",
        "",
        "## Pedidos",
        *_claims_lines(claims),
        "",
        "## Limitações e alertas",
    ]
    limitation_lines = [
        f"- [{lim.get('code')}] {lim.get('message')}" for lim in limitations
    ] or ["(sem limitações registradas)"]
    lines.extend(limitation_lines)
    lines.extend(
        [
            "",
            "## Índice de fontes",
            *_sources_index(sources or []),
        ]
    )
    if mode == MODE_COMPLETE:
        thesis_lines = [
            f"- [{t.get('represented_side')}] {t.get('issue')}: {t.get('conclusion')}"
            for t in content.get("theses", [])
        ] or ["(nenhuma tese)"]
        calc_lines = [
            f"- {c.get('formula')} v{c.get('formula_version')}: {c.get('result')}"
            for c in content.get("calculations", [])
        ] or ["(nenhum cálculo)"]
        fact_lines = [
            f"- {f.get('statement')} [{f.get('epistemic_status')}]"
            for f in content.get("facts", [])
        ] or ["(nenhum fato)"]
        lines.extend(
            [
                "",
                "## Teses",
                *thesis_lines,
                "",
                "## Cálculos (memória)",
                *calc_lines,
                "",
                "## Fatos",
                *fact_lines,
            ]
        )
        if review_events:
            lines.extend(
                ["", "## Histórico de revisão"]
                + [f"- {e.get('target')}: {e.get('reason')}" for e in review_events]
            )
    lines.extend(
        [
            "",
            "_Minuta condicionada aos dados acima; lacunas marcadas como "
            "pendentes. Não substitui a responsabilidade profissional._",
        ]
    )
    return "\n".join(lines) + "\n"
