"""Classificação multirrótulo (Onda 0 Task 5, §8.3).

Determinística e normalizada: mesma entrada gera mesma saída. Erro do
modelo usa fallback ``general`` sem encerrar o pipeline. Override humano
prevalece e fica auditável em ``source="human_override"``.
"""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, Field


class ClassificationResult(BaseModel):
    primary_area: str = "general"
    related_areas: list[str] = Field(default_factory=list)
    document_types: list[str] = Field(default_factory=list)
    procedure: str | None = None
    phase: str | None = None
    source: Literal["model", "human_override", "fallback"] = "model"
    confidence: float | None = None


_AREA_KEYWORDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("family", ("guarda", "alimentos", "divorcio", "divórcio", "filho menor", "casamento", "herdeiro", "inventario", "inventário")),
    ("civil_procedure", ("rito", "procedimento comum", "juizado", "competencia", "competência", "tutela", "contestacao", "contestação")),
    ("contracts", ("contrato", "clausula", "cláusula", "prestacao de servicos", "prestação de serviços", "reajuste", "aditivo", "minuta")),
    ("tax", ("tribut", "imposto", "lancamento", "lançamento", "base de calculo", "base de cálculo", "aliquota", "alíquota", "fiscal")),
    ("labor", ("reclamacao trabalhista", "reclamação trabalhista", "vinculo de emprego", "vínculo de emprego", "verbas rescis", "FGTS", "aviso previo", "aviso prévio")),
    ("consumer", ("consumidor", "fornecedor", "vicio", "vício", "defeito do produto")),
    ("social_security", ("beneficio", "benefício", "aposentadoria", "INSS", "auxilio", "auxílio")),
)

_PROCEDURE_KEYWORDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("procedimento comum", ("procedimento comum", "rito ordinario", "rito ordinário")),
    ("juizado", ("juizado", "lei 9099", "lei 9.099")),
    ("execucao", ("execucao", "execução", "cumprimento de sentenca", "cumprimento de sentença")),
)


def _normalize(text: str) -> str:
    text = (text or "").lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def classify_blocks(
    blocks: list[dict],
    *,
    area_overrides: list[str] | None = None,
) -> ClassificationResult:
    """Classifica blocos estruturados; override humano prevalece."""
    if area_overrides:
        primary = area_overrides[0]
        return ClassificationResult(
            primary_area=primary,
            related_areas=list(area_overrides[1:]),
            source="human_override",
            confidence=None,
        )
    corpus = " ".join(
        _normalize(b.get("normalized_text") or b.get("original_text") or "")
        for b in (blocks or [])
    )
    if not corpus.strip():
        return ClassificationResult(primary_area="general", source="fallback", confidence=0.0)
    hits: list[tuple[str, int]] = []
    for area, keywords in _AREA_KEYWORDS:
        count = sum(1 for kw in keywords if kw in corpus)
        if count:
            hits.append((area, count))
    if not hits:
        return ClassificationResult(primary_area="general", source="fallback", confidence=0.0)
    hits.sort(key=lambda item: (-item[1], item[0]))
    primary, top = hits[0]
    related = [area for area, _ in hits[1:3]]
    procedure = None
    for proc, keywords in _PROCEDURE_KEYWORDS:
        if any(kw in corpus for kw in keywords):
            procedure = proc
            break
    document_types: list[str] = []
    if "peticao inicial" in corpus or "petição inicial" in corpus:
        document_types.append("peticao_inicial")
    if "contestacao" in corpus or "contestação" in corpus:
        document_types.append("contestacao")
    confidence = min(0.95, 0.45 + 0.1 * top)
    return ClassificationResult(
        primary_area=primary,
        related_areas=related,
        document_types=document_types,
        procedure=procedure,
        source="model",
        confidence=round(confidence, 2),
    )
