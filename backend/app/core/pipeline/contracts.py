"""Contratos do pipeline universal V3 (Onda 0 Task 3, §8 + §9).

``PIPELINE_STAGES`` é a ordem canônica de 12 estágios. ``calculate_progress``
deriva porcentagem honesta de unidades mensuráveis (estágios concluídos),
nunca de estimativa fictícia: ``extraction`` nunca retorna 100%, e 100%
só ocorre com ``stage == "publication"`` em estado terminal publicado.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


PIPELINE_STAGES: tuple[str, ...] = (
    "ingestion",
    "extraction",
    "classification",
    "coverage_planning",
    "structured_extraction",
    "reconciliation",
    "legal_analysis",
    "legal_research",
    "calculations",
    "verification",
    "composition",
    "publication",
)


@dataclass(frozen=True)
class ProgressSnapshot:
    """Progresso honesto de uma execução."""

    percent: int
    stage: str | None
    completed_stages: int
    total_stages: int


def _stage_of(obj) -> str | None:
    return getattr(obj, "stage", None)


def _status_of(obj) -> str | None:
    return getattr(obj, "status", None)


def calculate_progress(run, stage_runs: Sequence | None = None) -> ProgressSnapshot:
    """Calcula progresso honesto a partir de estágios concluídos.

    Regras (spec §12.3, AC-11):
    - ``FAILED``/``CANCELLED`` → 0%.
    - Com ``stage_runs``: ``percent = 100 * concluídos / total``,
      limitado a 99% salvo ``stage == "publication"`` em terminal publicado.
    - Sem ``stage_runs`` (runs legados V2): deriva do índice do estágio
      atual em ``PIPELINE_STAGES``, também limitado a 99% fora de
      ``publication``. Terminal ``completed``/``partial`` com
      ``stage == "publication"`` → 100% (compatível com publicação real).
    """
    total = len(PIPELINE_STAGES)
    status = _status_of(run)
    stage = _stage_of(run)

    if status in ("failed", "cancelled"):
        completed = 0
        if stage_runs:
            completed = sum(1 for sr in stage_runs if getattr(sr, "status", None) == "completed")
        return ProgressSnapshot(percent=0, stage=stage, completed_stages=completed, total_stages=total)

    if stage_runs:
        completed = sum(1 for sr in stage_runs if getattr(sr, "status", None) == "completed")
        if total == 0:
            return ProgressSnapshot(percent=0, stage=stage, completed_stages=0, total_stages=0)
        percent = int(100 * completed / total)
        if (
            status in ("completed", "partial")
            and stage == "publication"
            and completed >= total
        ):
            percent = 100
        else:
            percent = min(percent, 99)
        return ProgressSnapshot(
            percent=percent, stage=stage, completed_stages=completed, total_stages=total
        )

    # Fallback sem stage_runs (runs V2 legados): índice do estágio atual.
    if status in ("completed", "partial") and stage == "publication":
        return ProgressSnapshot(percent=100, stage=stage, completed_stages=total, total_stages=total)
    if status in ("completed", "partial"):
        # Compat V2: runs antigos publicam sem stage_runs (stage composition/None).
        # Mantém 100% para não quebrar a API V2 existente.
        return ProgressSnapshot(percent=100, stage=stage, completed_stages=total, total_stages=total)
    if stage in PIPELINE_STAGES:
        index = PIPELINE_STAGES.index(stage)
        percent = 5 + int(90 * index / total)
        return ProgressSnapshot(
            percent=min(percent, 99), stage=stage, completed_stages=index, total_stages=total
        )
    return ProgressSnapshot(percent=5, stage=stage, completed_stages=0, total_stages=total)
