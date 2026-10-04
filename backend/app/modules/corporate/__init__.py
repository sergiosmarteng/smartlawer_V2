"""Módulo empresarial e societário v1.0 (Onda 2A, spec §3)."""

from app.modules.corporate.module import (
    CORPORATE_SOURCES,
    CorporateModule,
    DESCRIPTOR,
    assess_dimension,
    participacao_societaria,
    rateio_cenario,
    register_calculation_rules,
)

__all__ = [
    "CORPORATE_SOURCES",
    "CorporateModule",
    "DESCRIPTOR",
    "assess_dimension",
    "participacao_societaria",
    "rateio_cenario",
    "register_calculation_rules",
]
