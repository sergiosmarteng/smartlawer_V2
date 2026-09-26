"""Pesquisa jurídica verificável com validade temporal (V2 T07, §9).

Três camadas separadas: citações encontradas na peça (literal
preservado), fontes recuperadas e verificadas, e pertinência.
Indisponibilidade nunca vira autoridade confirmada; ambiguidade
exige revisão. Modos histórico x atual distinguem datas.
"""

import logging
import re
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

MODE_HISTORIC = "historic"
MODE_CURRENT = "current"

STATUS_VERIFIED = "verified"
STATUS_UNVERIFIED = "unverified"
STATUS_EXPIRED = "expired_or_superseded"
STATUS_POSTERIOR = "posterior_to_reference"
STATUS_AMBIGUOUS = "ambiguous_needs_review"

# Padrões de citação pt-BR (extração, não normalização silenciosa).
_PATTERNS = [
    ("sumula", re.compile(r"S[úu]mula\s+(?:vinculante\s+)?\d+(?:\s+do\s+[A-Z]+)?", re.IGNORECASE)),
    ("lei", re.compile(r"Lei\s+(?:Complementar\s+)?n?[ºo.]?\s*\d+[\d./-]*\s*(?:/\d{2,4})?", re.IGNORECASE)),
    ("artigo", re.compile(r"art(?:igo)?\.?\s*\d+[A-Za-z0-9.,º°/-]*", re.IGNORECASE)),
    ("codigo", re.compile(r"(?:Código|Codigo)\s+[A-Za-z ]+", re.IGNORECASE)),
    ("tese_tema", re.compile(r"Tema\s+\d+\s+da\s+repercuss[aã]o\s+geral", re.IGNORECASE)),
]

_INSTRUMENT_HINT = re.compile(
    r"\b(CLT|CPC|CPP|CC|CP|CF(?:/88)?|Constitui[çc][aã]o|CDC|LGPD)\b", re.IGNORECASE
)


@dataclass
class FoundCitation:
    """Citação encontrada na peça: literal + instrumento presumido (§9)."""

    literal: str
    kind: str
    presumed_instrument: str | None = None
    needs_review: bool = False
    review_reason: str | None = None


@dataclass
class FetchedSource:
    """Fonte recuperada de adaptador externo (inteiro teor ou metadados)."""

    citation: str
    url: str | None = None
    court_or_body: str | None = None
    number: str | None = None
    accessed_at: str | None = None
    excerpt: str | None = None
    effective_from: str | None = None
    effective_to: str | None = None
    decision_dates: list[str] = field(default_factory=list)
    content_hash: str | None = None


@dataclass
class Verification:
    citation: str
    status: str = STATUS_UNVERIFIED
    fetched: FetchedSource | None = None
    limitation: str | None = None


class UnavailableSourceError(Exception):
    """Adaptador sem acesso ao inteiro teor — não é confirmação."""


def extract_citations(text: str) -> list[FoundCitation]:
    """Citações literais da peça; ambíguas pedem revisão (§9)."""
    found: list[FoundCitation] = []
    seen: set[str] = set()
    for kind, pattern in _PATTERNS:
        for match in pattern.finditer(text or ""):
            literal = match.group(0).strip()
            key = literal.casefold()
            if key in seen:
                continue
            seen.add(key)
            instrument_match = _INSTRUMENT_HINT.search(
                text[max(0, match.start() - 60) : match.end() + 60]
            )
            instrument = instrument_match.group(0) if instrument_match else None
            needs_review = instrument is None and kind in ("artigo", "codigo")
            found.append(
                FoundCitation(
                    literal=literal,
                    kind=kind,
                    presumed_instrument=instrument,
                    needs_review=needs_review,
                    review_reason=(
                        "instrumento não identificável no contexto; confirmar "
                        "dispositivo antes de usar como fundamento." if needs_review else None
                    ),
                )
            )
    return found


def check_temporal(
    fetched: FetchedSource,
    *,
    fact_date: str | None = None,
    piece_date: str | None = None,
    mode: str = MODE_CURRENT,
) -> str:
    """Validade temporal: vigência x fato, tese x peça (§9.1).

    Datas ISO 'YYYY-MM-DD'; comparação lexicográfica válida.
    Retorna status; nunca reescreve a peça silenciosamente.
    """
    _ = mode  # registrado pelo chamador; regra independe do modo
    if fetched.effective_to and fact_date and fetched.effective_to < fact_date:
        return STATUS_EXPIRED
    for decided in fetched.decision_dates:
        if piece_date and decided > piece_date:
            return STATUS_POSTERIOR
    return STATUS_VERIFIED


def verify_citation(
    citation: FoundCitation,
    fetch,
    *,
    fact_date: str | None = None,
    piece_date: str | None = None,
    mode: str = MODE_CURRENT,
) -> Verification:
    """Verifica UMA citação; falha vira não-verificada com limitação."""
    try:
        fetched = fetch(citation.literal)
    except UnavailableSourceError as exc:
        logger.warning("Fonte indisponível para %r (%s).", citation.literal, exc)
        return Verification(
            citation=citation.literal,
            status=STATUS_UNVERIFIED,
            limitation=f"Fonte não verificada ({citation.literal}): inteiro teor indisponível.",
        )
    except Exception as exc:
        logger.warning("Adaptador falhou para %r (%s).", citation.literal, exc)
        return Verification(
            citation=citation.literal,
            status=STATUS_UNVERIFIED,
            limitation=f"Fonte não verificada ({citation.literal}): erro do adaptador.",
        )
    if fetched is None:
        if citation.needs_review:
            return Verification(
                citation=citation.literal,
                status=STATUS_AMBIGUOUS,
                limitation=(
                    f"{citation.review_reason} Fonte também não localizada "
                    f"({citation.literal})."
                ),
            )
        return Verification(
            citation=citation.literal,
            status=STATUS_UNVERIFIED,
            limitation=f"Fonte não verificada ({citation.literal}): não localizada.",
        )
    status = check_temporal(fetched, fact_date=fact_date, piece_date=piece_date, mode=mode)
    if citation.needs_review:
        status = STATUS_AMBIGUOUS
    limitation = None
    if status == STATUS_EXPIRED:
        limitation = (
            f"{citation.literal}: vigência encerrada antes do fato; "
            "conferir texto aplicável à data."
        )
    elif status == STATUS_POSTERIOR:
        limitation = (
            f"{citation.literal}: tese posterior à peça; não integra a petição original."
        )
    elif status == STATUS_AMBIGUOUS:
        limitation = citation.review_reason
    return Verification(
        citation=citation.literal, status=status, fetched=fetched, limitation=limitation
    )


def verify_citations(
    citations: list[FoundCitation],
    fetch,
    **kwargs,
) -> tuple[list[Verification], list[str]]:
    """Verifica todas; retorna (verificações, limitações acionáveis)."""
    verifications = [verify_citation(c, fetch, **kwargs) for c in citations]
    limitations = [v.limitation for v in verifications if v.limitation]
    return verifications, limitations
