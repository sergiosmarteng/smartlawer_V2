"""Módulo tributário v1.0 (Onda 2B, spec §5)."""

from app.modules.tax.module import (
    DESCRIPTOR,
    TAX_SOURCES,
    TaxModule,
    assess_dimension,
    register_calculation_rules,
    tributo_competencia,
)

__all__ = [
    "DESCRIPTOR",
    "TAX_SOURCES",
    "TaxModule",
    "assess_dimension",
    "register_calculation_rules",
    "tributo_competencia",
]
