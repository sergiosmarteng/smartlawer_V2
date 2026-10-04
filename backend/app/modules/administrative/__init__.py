"""Módulo administrativo v1.0 (Onda 2B, spec §6)."""

from app.modules.administrative.module import (
    ADMINISTRATIVE_SOURCES,
    AdministrativeModule,
    DESCRIPTOR,
    assess_dimension,
    reajuste_contrato_publico,
    register_calculation_rules,
)

__all__ = [
    "ADMINISTRATIVE_SOURCES",
    "AdministrativeModule",
    "DESCRIPTOR",
    "assess_dimension",
    "reajuste_contrato_publico",
    "register_calculation_rules",
]
