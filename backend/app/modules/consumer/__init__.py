"""Módulo consumidor v1.0 (Onda 1B, spec §7)."""

from app.modules.consumer.module import (
    CONSUMER_SOURCES,
    ConsumerModule,
    DESCRIPTOR,
    assess_dimension,
    register_calculation_rules,
    restituicao_cobranca,
)

__all__ = [
    "CONSUMER_SOURCES",
    "ConsumerModule",
    "DESCRIPTOR",
    "assess_dimension",
    "register_calculation_rules",
    "restituicao_cobranca",
]
