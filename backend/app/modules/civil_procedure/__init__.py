"""Módulo cível e processo civil v1.0 (Onda 1A, spec §4)."""

from app.modules.civil_procedure.module import (
    CIVIL_PROCEDURE_SOURCES,
    CivilProcedureModule,
    DESCRIPTOR,
    assess_dimension,
    register_calculation_rules,
    soma_parcelas_documentadas,
)

__all__ = [
    "CIVIL_PROCEDURE_SOURCES",
    "CivilProcedureModule",
    "DESCRIPTOR",
    "assess_dimension",
    "register_calculation_rules",
    "soma_parcelas_documentadas",
]
