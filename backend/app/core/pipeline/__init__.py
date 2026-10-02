"""Pipeline universal V3 — contratos e orquestração (Onda 0).

Task 3 define ``PIPELINE_STAGES`` + ``calculate_progress``. Task 11 adiciona
o orquestrador que executa os estágios e publica somente após o verificador.
"""

from app.core.pipeline.contracts import (
    PIPELINE_STAGES,
    ProgressSnapshot,
    calculate_progress,
)

__all__ = ["PIPELINE_STAGES", "ProgressSnapshot", "calculate_progress"]
