"""Módulo trabalhista v1.0 — acidente do trabalho prioritário (V2 §10)."""

from app.modules import register_module

DESCRIPTOR = register_module(
    {
        "module_id": "labor",
        "version": "1.0",
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
    }
)
