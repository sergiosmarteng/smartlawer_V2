"""Módulo contratos v1.0 (Onda 2A, spec §4)."""

from app.modules.contracts.module import (
    CONTRACTS_SOURCES,
    ContractsModule,
    DESCRIPTOR,
    assess_dimension,
    diff_versions,
    register_calculation_rules,
    reajuste_contratual,
)

__all__ = [
    "CONTRACTS_SOURCES",
    "ContractsModule",
    "DESCRIPTOR",
    "assess_dimension",
    "diff_versions",
    "register_calculation_rules",
    "reajuste_contratual",
]
