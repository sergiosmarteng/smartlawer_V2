"""Descritor do núcleo universal compatível com o registry V2 e o V3."""

from app.core.module_registry import ModuleRequirements


class UniversalModule:
    module_id = "universal"
    version = "1.0"
    supported_areas = ("general",)
    document_types = ("any",)

    def requirements(self) -> ModuleRequirements:
        return ModuleRequirements(
            required_sections=[
                "parties", "events", "claims", "facts", "evidence",
                "legal_references", "theses", "risks", "action_plan", "sources",
            ],
            issue_checklists=["universal-core"],
        )


DESCRIPTOR = {
    "module_id": "universal",
    "version": "1.0",
    "supported_areas": ["general"],
    "document_types": ["any"],
    "required_sections": [
        "parties", "events", "claims", "facts", "evidence",
        "legal_references", "theses", "risks", "action_plan", "sources",
    ],
    "issue_checklists": ["universal-core"],
    "calculation_rules": [],
    "research_sources": [],
    "evaluation_cases": [],
}
