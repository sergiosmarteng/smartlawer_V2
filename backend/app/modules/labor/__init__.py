"""Módulo trabalhista v1.0 — acidente do trabalho prioritário (V2 §10 + Onda 1B §6)."""

from app.modules import register_module
from app.modules.labor.module import (
    LABOR_SOURCES,
    LABOR_THEMES,
    LaborModule,
    assess_theme,
    register_calculation_rules,
    rubricas_trabalhistas,
)

DESCRIPTOR = register_module(
    {
        "module_id": "labor",
        # Onda 1B: contrato V3 (spec §2); chaves V2 preservadas.
        "version": "1.0.0",
        "supported_areas": ["labor"],
        "document_types": ["reclamacao_trabalhista", "contestacao"],
        "required_sections": [
            "relacao_trabalho",
            "evento",
            "seguranca",
            "nexo_dano",
            "responsabilidade",
            "reparacao",
            "processo",
        ],
        "entity_schema": "schemas_v2",
        "issue_checklists": "labor.checklist:WORK_ACCIDENT_MATRIX",
        "research_sources": ["planalto", "tst", "stf", "mte_nr"],
        "calculation_rules": ["rubricas_trabalhistas@1.0"],
        "evaluation_cases": ["labor_cases"],
    }
)
