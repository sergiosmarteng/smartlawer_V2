"""Módulo imobiliário v1.0 (Onda 2B, spec §7)."""

from app.modules.real_estate.module import (
    DESCRIPTOR,
    REAL_ESTATE_SOURCES,
    RealEstateModule,
    assess_dimension,
    parcelas_mora_rateio,
    register_calculation_rules,
)

__all__ = [
    "DESCRIPTOR",
    "REAL_ESTATE_SOURCES",
    "RealEstateModule",
    "assess_dimension",
    "parcelas_mora_rateio",
    "register_calculation_rules",
]
