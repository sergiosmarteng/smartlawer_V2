"""Planejamento de cobertura integral sem corte fixo (V2 T05, §6.1).

Todos os blocos relevantes são atribuídos a lotes dentro do orçamento
de tokens do modelo efetivo; sobreposição por IDs permite deduplicação.
Quando o teto estoura, a parcialidade é explícita (``BUDGET_EXCEEDED``
+ blocos não processados) — nunca redução silenciosa (§17).
"""

import logging

from app.core.config import settings
from app.core.legal_chunker import estimate_tokens

logger = logging.getLogger(__name__)

BUDGET_EXCEEDED = "BUDGET_EXCEEDED"

OMISSION_MARKER = "\n\n[...trecho omitido por orcamento de contexto; ver cobertura...]\n\n"


class BudgetExceededError(Exception):
    """Teto de custo/lotes atingido — parcialidade explícita (V2 §7.1)."""

    code = BUDGET_EXCEEDED

    def __init__(self, message: str, *, unprocessed_block_ids: list[str] | None = None):
        super().__init__(message)
        self.unprocessed_block_ids = list(unprocessed_block_ids or [])


def _block_text(block: dict) -> str:
    return block.get("normalized_text") or block.get("original_text") or ""


def plan_batches(
    blocks: list[dict],
    *,
    max_batch_tokens: int | None = None,
    overlap_blocks: int | None = None,
) -> dict:
    """Atribui 100% dos blocos a lotes; overlap referencia IDs (§6.1)."""
    max_batch_tokens = max_batch_tokens or settings.COVERAGE_MAX_BATCH_TOKENS
    overlap_blocks = (
        settings.COVERAGE_OVERLAP_BLOCKS if overlap_blocks is None else overlap_blocks
    )
    batches: list[dict] = []
    current_ids: list[str] = []
    current_tokens = 0

    def flush() -> None:
        if current_ids:
            batches.append(
                {
                    "batch_index": len(batches),
                    "block_ids": list(current_ids),
                    "tokens": current_tokens,
                }
            )

    for block in blocks:
        block_id = block.get("id", "")
        tokens = estimate_tokens(_block_text(block))
        if current_ids and current_tokens + tokens > max_batch_tokens:
            flush()
            carry = current_ids[-overlap_blocks:] if overlap_blocks > 0 else []
            current_ids = list(carry)
            current_tokens = 0
        current_ids.append(block_id)
        current_tokens += tokens
    flush()

    assigned = [bid for batch in batches for bid in batch["block_ids"]]
    return {
        "batches": batches,
        "blocks_total": len(blocks),
        "batches_total": len(batches),
        "assigned_block_ids": assigned,
        "unprocessed_block_ids": [],
        "tokens_total": sum(b["tokens"] for b in batches),
    }


def check_budget(
    plan: dict,
    *,
    max_batches: int | None = None,
    max_tokens_total: int | None = None,
) -> dict:
    """Aplica o teto; estouro vira parcialidade explícita, nunca corte mudo."""
    max_batches = max_batches if max_batches is not None else settings.COVERAGE_MAX_BATCHES
    batches = plan.get("batches", [])
    if len(batches) > max_batches:
        kept = batches[:max_batches]
        kept_ids = {bid for batch in kept for bid in batch["block_ids"]}
        unprocessed = [
            bid for bid in plan.get("assigned_block_ids", []) if bid not in kept_ids
        ]
        raise BudgetExceededError(
            f"Orcamento excedido: {len(batches)} lotes > teto {max_batches}; "
            f"{len(unprocessed)} bloco(s) sem processar.",
            unprocessed_block_ids=unprocessed,
        )
    if max_tokens_total is not None and plan.get("tokens_total", 0) > max_tokens_total:
        raise BudgetExceededError(
            f"Orcamento excedido: {plan['tokens_total']} tokens > teto {max_tokens_total}.",
            unprocessed_block_ids=[],
        )
    return plan


def build_prompt_window(
    text: str,
    *,
    budget_tokens: int | None = None,
    head_ratio: float = 0.6,
) -> tuple[str, dict]:
    """Janela head+tail com cobertura registrada — fim do corte fixo.

    Texto dentro do orçamento passa intacto. Acima dele, preserva
    INÍCIO e FIM (onde vive o rol de pedidos) e registra o omitido.
    Cauda sempre incluída: pedidos finais nunca caem em silêncio (D02).
    """
    budget_tokens = budget_tokens or settings.PROMPT_BUDGET_TOKENS
    text = text or ""
    total_tokens = estimate_tokens(text)
    coverage = {
        "tokens_total": total_tokens,
        "budget_tokens": budget_tokens,
        "truncated": False,
        "tail_included": True,
        "omitted_chars": 0,
    }
    if total_tokens <= budget_tokens:
        return text, coverage

    approx_chars = budget_tokens * 4
    head_chars = int(approx_chars * head_ratio)
    tail_chars = approx_chars - head_chars
    head = text[:head_chars]
    tail = text[-tail_chars:] if tail_chars > 0 else ""
    omitted = max(0, len(text) - head_chars - len(tail))
    window = head + OMISSION_MARKER + tail
    coverage.update(
        {
            "truncated": True,
            "tail_included": True,
            "omitted_chars": omitted,
            "head_chars": head_chars,
            "tail_chars": len(tail),
        }
    )
    logger.warning(
        "Janela de prompt com omissao explícita: %s chars omitidos.", omitted
    )
    return window, coverage
