"""Módulo família e sucessões v1.0 (Onda 1A, spec §5)."""

from app.modules.family.module import (
    DESCRIPTOR,
    FAMILY_SOURCES,
    FamilyModule,
    alimentos_scenario,
    assess_dimension,
    register_calculation_rules,
)

__all__ = [
    "DESCRIPTOR",
    "FAMILY_SOURCES",
    "FamilyModule",
    "alimentos_scenario",
    "assess_dimension",
    "register_calculation_rules",
]
