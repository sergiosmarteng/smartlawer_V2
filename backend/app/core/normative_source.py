"""Fonte normativa verificável (Onda 2A fundação, spec §8).

Cada regra aplicada registra instrumento, dispositivo, jurisdição,
vigência, data de consulta, URL oficial, hash/versão e trecho. Fonte
não recuperada, ambígua ou posterior ao fato nunca vira fundamento
histórico confirmado.
"""

from pydantic import BaseModel, Field


class NormativeSource(BaseModel):
    """Catálogo normativo autorizado por jurisdição e data."""

    instrument_id: str = Field(min_length=1)
    provision_id: str = Field(min_length=1)
    jurisdiction: str = Field(min_length=1)
    effective_from: str = Field(min_length=1)
    effective_to: str | None = None
    retrieved_at: str = Field(min_length=1)
    url: str = Field(min_length=1)
    hash: str | None = None
    version: str | None = None
    excerpt: str = Field(min_length=1)


def _is_official_url(url: str | None) -> bool:
    url = (url or "").strip().lower()
    return url.startswith("https://") and (
        "planalto.gov.br" in url or ".gov.br" in url or ".jus.br" in url
    )


def validate_normative_source(source: dict, *, reference_date=None) -> list[str]:
    """Violações de fonte normativa (vazio = válida).

    `reference_date` (date ou "YYYY-MM-DD") é a data dos fatos: norma com
    `effective_from` posterior a ela não fundamenta análise histórica.
    """
    violations: list[str] = []
    get = source.get if isinstance(source, dict) else (lambda k, d=None: d)
    url = get("url")
    if not url or not _is_official_url(url):
        violations.append("fonte sem URL oficial recuperada")
    if not get("retrieved_at"):
        violations.append("fonte sem data de consulta (retrieved_at)")
    if not (get("excerpt") or "").strip():
        violations.append("fonte sem trecho de suporte (ambígua)")
    if get("available") is False:
        violations.append("fonte não recuperada")
    effective_from = get("effective_from") or ""
    if reference_date is not None and effective_from:
        ref = reference_date.isoformat() if hasattr(reference_date, "isoformat") else str(reference_date)
        if effective_from > ref:
            violations.append(
                f"norma vigente desde {effective_from}, posterior à data "
                f"de referência {ref}: não fundamenta análise histórica"
            )
    return violations
