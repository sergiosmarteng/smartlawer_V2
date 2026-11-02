"""Estimativa de custo por tokens (Onda A — telemetria e teto de orçamento).

Isto **não é fatura**: é um teto de segurança para o guarda de orçamento.
Os preços abaixo são públicos e aproximados, por milhão de tokens
(entrada / saída), e podem ser sobrescritos por ``LLM_PRICES_JSON`` no
ambiente — formato ``{"modelo": [preco_entrada, preco_saida]}``.

Modelo desconhecido devolve ``None``: o guarda então **não bloqueia** e a
telemetria grava ``cost: "unavailable"``. Preferimos custo ausente a custo
inventado.
"""

from __future__ import annotations

import json
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# USD por 1M de tokens: (entrada, saída).
_DEFAULT_PRICES: dict[str, tuple[float, float]] = {
    # OpenAI
    "gpt-4-turbo": (10.0, 30.0),
    "gpt-4-turbo-preview": (10.0, 30.0),
    "gpt-4o": (2.5, 10.0),
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4.1": (2.0, 8.0),
    "gpt-4.1-mini": (0.40, 1.60),
    # OpenRouter / Anthropic (modelo pinado em ai_engine.resolve_chat_config)
    "anthropic/claude-3-opus": (15.0, 75.0),
    "claude-3-opus": (15.0, 75.0),
    "anthropic/claude-3.5-sonnet": (3.0, 15.0),
    "claude-3-5-sonnet": (3.0, 15.0),
    # Google
    "gemini-1.5-pro": (1.25, 5.0),
    "gemini-2.0-flash": (0.10, 0.40),
}


def _price_table() -> dict[str, tuple[float, float]]:
    table = dict(_DEFAULT_PRICES)
    raw = (getattr(settings, "LLM_PRICES_JSON", "") or "").strip()
    if raw:
        try:
            overrides = json.loads(raw)
            for model, pair in dict(overrides).items():
                table[str(model)] = (float(pair[0]), float(pair[1]))
        except Exception as exc:  # configuração inválida nunca derruba a run
            logger.warning("LLM_PRICES_JSON invalido (%s); usando tabela padrao.", exc)
    return table


def estimate_cost_usd(
    model: str | None,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
) -> float | None:
    """Custo estimado em USD, ou ``None`` quando o modelo não é precificado."""
    name = (model or "").strip()
    if not name:
        return None
    table = _price_table()
    price = table.get(name)
    if price is None:
        # Alias com sufixo de data/provider: casa pelo prefixo mais longo.
        matches = [k for k in table if name.startswith(k) or k in name]
        if not matches:
            return None
        price = table[max(matches, key=len)]
    prompt_price, completion_price = price
    cost = (prompt_tokens / 1_000_000) * prompt_price + (
        completion_tokens / 1_000_000
    ) * completion_price
    return round(cost, 6)
