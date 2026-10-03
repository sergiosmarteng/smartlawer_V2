"""Registro de módulos jurídicos (Onda 0 Task 5, §8.7 + §13.5).

``LegalModuleRegistry`` resolve a classificação multirrótulo para a lista
de módulos ativos. O núcleo ``universal@1.0`` está sempre incluído;
assunto sem especialização gera ``ModuleActivation(status="fallback")``
com motivo — nunca invenção de regra específica.
"""

from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel, Field

from app.core.classification import ClassificationResult


class ModuleRequirements(BaseModel):
    required_sections: list[str] = Field(default_factory=list)
    issue_checklists: list[str] = Field(default_factory=list)
    calculation_rules: list[str] = Field(default_factory=list)
    research_sources: list[str] = Field(default_factory=list)
    evaluation_cases: list[str] = Field(default_factory=list)


class ModuleActivationRecord(BaseModel):
    module_id: str
    module_version: str = "1.0.0"
    status: str = "active"
    reason: str = ""


class LegalModule(Protocol):
    module_id: str
    version: str
    supported_areas: tuple[str, ...]

    def requirements(self) -> ModuleRequirements: ...


class _UniversalModule:
    module_id = "universal"
    version = "1.0"
    supported_areas = ("general",)

    def requirements(self) -> ModuleRequirements:
        return ModuleRequirements(
            required_sections=[
                "parties", "events", "claims", "facts", "evidence",
                "legal_references", "theses", "risks", "action_plan", "sources",
            ]
        )


class LegalModuleRegistry:
    """Resolve classificação → módulos; fallback universal garantido."""

    def __init__(self) -> None:
        self._modules: dict[str, LegalModule] = {}
        universal = _UniversalModule()
        self._modules[universal.module_id] = universal

    @classmethod
    def with_defaults(cls) -> "LegalModuleRegistry":
        return cls()

    def register(self, module: LegalModule) -> None:
        self._modules[module.module_id] = module

    def resolve(
        self,
        classification: ClassificationResult,
        *,
        enabled: set[str] | None = None,
    ) -> list[LegalModule]:
        allowed = set(enabled) if enabled is not None else None
        ordered: list[LegalModule] = [self._modules["universal"]]
        wanted = [classification.primary_area, *classification.related_areas]
        for area in wanted:
            for module in self._modules.values():
                if module.module_id == "universal":
                    continue
                if allowed is not None and module.module_id not in allowed:
                    continue
                if area in module.supported_areas and module not in ordered:
                    ordered.append(module)
        return ordered

    def activations(self, classification: ClassificationResult) -> list[ModuleActivationRecord]:
        records = [
            ModuleActivationRecord(
                module_id="universal",
                module_version="1.0",
                status="active",
                reason="Núcleo universal obrigatório",
            )
        ]
        wanted = {classification.primary_area, *classification.related_areas} - {"general"}
        for area in sorted(wanted):
            covered = any(
                area in m.supported_areas
                for m in self._modules.values()
                if m.module_id != "universal"
            )
            if not covered:
                records.append(
                    ModuleActivationRecord(
                        module_id=area,
                        module_version="0.0.0",
                        status="fallback",
                        reason=(
                            f"Área '{area}' sem módulo especializado instalado; "
                            "núcleo universal produz análise com limitação declarada."
                        ),
                    )
                )
        return records
