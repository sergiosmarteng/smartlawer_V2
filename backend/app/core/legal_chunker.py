"""Legal-aware text chunking for RAG ingestion.

Splits petition/contract text into retrieval units that respect Brazilian
legal structure: a chunk never starts in the middle of an article,
paragraph, inciso, súmula or section header. Units are greedily packed up
to ``max_tokens`` with a token overlap between consecutive chunks.

Token counting uses ``tiktoken`` when available, else a ``chars/4``
heuristic (close enough for Portuguese legal text budgeting).
"""

import logging
import re
from dataclasses import dataclass

logger = logging.getLogger(__name__)

DEFAULT_MAX_TOKENS = 1000
DEFAULT_OVERLAP_TOKENS = 150

# Lines that must always start a new retrieval unit. The header stays
# attached to the body that follows it.
HEADER_RE = re.compile(
    r"^(?:"
    r"Art\.\s*\d+|§\s*\d+|S[úu]mula\b|EMENTA\b|"
    r"(?:DOS?|DAS?)\s+[A-ZÃÕÇÉÍÚÂÊÔ]{3,}|"
    r"[IVX]+\s*[-–—.]|"
    r"\d+\.\s+[A-ZÃÕÇÉÍÚÂÊÔ]"
    r")",
    re.MULTILINE,
)


@dataclass
class LegalChunk:
    content: str
    chunk_index: int
    token_count: int


def estimate_tokens(text: str) -> int:
    """Token estimate: tiktoken cl100k when present, else chars/4."""
    try:
        import tiktoken

        return len(tiktoken.get_encoding("cl100k_base").encode(text))
    except Exception:
        return max(1, len(text) // 4)


def _split_units(text: str) -> list[str]:
    """Split text into indivisible units (paragraphs, headers+body)."""
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    units: list[str] = []
    for paragraph in paragraphs:
        parts = HEADER_RE.split(paragraph)
        if len(parts) <= 1:
            units.append(paragraph)
            continue
        headers = HEADER_RE.findall(paragraph)
        # Re-attach each header to the body that follows it.
        leading = parts[0].strip()
        if leading:
            units.append(leading)
        for header, body in zip(headers, parts[1:]):
            units.append(f"{header.strip()} {body.strip()}".strip())
    return [u for u in units if u]


def _overlap_tail(text: str, overlap_tokens: int) -> str:
    """Last ~overlap_tokens of text (char heuristic, word-safe)."""
    if overlap_tokens <= 0:
        return ""
    approx_chars = overlap_tokens * 4
    if len(text) <= approx_chars:
        return text
    cut = text[-approx_chars:]
    space = cut.find(" ")
    return cut[space + 1 :] if space != -1 else cut


def chunk_legal_text(
    text: str,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    overlap_tokens: int = DEFAULT_OVERLAP_TOKENS,
) -> list[LegalChunk]:
    """Chunk *text* into :class:`LegalChunk` units."""
    if not text or not text.strip():
        return []

    units = _split_units(text)
    chunks: list[LegalChunk] = []
    current: list[str] = []
    current_tokens = 0

    def flush() -> None:
        if not current:
            return
        content = "\n\n".join(current).strip()
        chunks.append(
            LegalChunk(
                content=content,
                chunk_index=len(chunks),
                token_count=estimate_tokens(content),
            )
        )

    for unit in units:
        unit_tokens = estimate_tokens(unit)
        if unit_tokens > max_tokens:
            # Oversized unit: hard-split on sentence boundaries as a
            # last resort (still never mid-word).
            flush()
            current, current_tokens = [], 0
            sentences = re.split(r"(?<=[.!?;])\s+", unit)
            buf, buf_tokens = [], 0
            for sentence in sentences:
                sent_tokens = estimate_tokens(sentence)
                if buf and buf_tokens + sent_tokens > max_tokens:
                    content = " ".join(buf).strip()
                    chunks.append(
                        LegalChunk(
                            content=content,
                            chunk_index=len(chunks),
                            token_count=estimate_tokens(content),
                        )
                    )
                    buf, buf_tokens = [], 0
                buf.append(sentence)
                buf_tokens += sent_tokens
            if buf:
                content = " ".join(buf).strip()
                chunks.append(
                    LegalChunk(
                        content=content,
                        chunk_index=len(chunks),
                        token_count=estimate_tokens(content),
                    )
                )
            continue
        if current and current_tokens + unit_tokens > max_tokens:
            flush()
            tail = _overlap_tail(chunks[-1].content, overlap_tokens)
            current = [tail] if tail else []
            current_tokens = estimate_tokens(tail) if tail else 0
        current.append(unit)
        current_tokens += unit_tokens
    flush()
    return chunks
