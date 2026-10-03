"""Onda 1B — módulo previdenciário (spec §8)."""

import pytest

from app.modules.social_security import (
    DESCRIPTOR,
    SOCIAL_SECURITY_SOURCES,
    SocialSecurityModule,
    register_calculation_rules,
)


def _case():
    return {
        "claims": [{"id": "c1", "title": "Aposentadoria por invalidez", "source_refs": ["s1"]}],
        "facts": [
            {"id": "f1", "statement": "CNIS com contribuições",
             "asserted_by": "parte-A", "epistemic_status": "documented",
             "source_refs": ["s1"]},
            {"id": "f2", "statement": "Laudo com incapacidade",
             "asserted_by": "perito", "epistemic_status": "documented",
             "source_refs": ["s2"]},
        ],
        "evidence": [{"id": "e1", "presence_status": "examined"}],
        "sources": [{"id": "s1", "page_number": 1}, {"id": "s2", "page_number": 2}],
    }


def test_descriptor_and_sources():
    assert DESCRIPTOR["module_id"] == "social_security"
    assert DESCRIPTOR["version"] == "1.0.0"
    assert {s["id"] for s in SOCIAL_SECURITY_SOURCES} == {"lei8213", "lei8212", "inss"}
    assert all(s["url"].startswith("https://") for s in SOCIAL_SECURITY_SOURCES)


def test_registry_resolves_social_security():
    from app.core.classification import classify_blocks
    from app.core.module_registry import LegalModuleRegistry

    registry = LegalModuleRegistry.with_defaults()
    registry.register(SocialSecurityModule())
    result = classify_blocks([{"normalized_text": "benefício do INSS com aposentadoria e auxílio"}])
    assert "social_security" in [result.primary_area, *result.related_areas]
    assert "social_security" in [m.module_id for m in registry.resolve(result)]


def test_six_themes_without_presumed_benefit():
    out = SocialSecurityModule().analyze(_case())
    assert len(out["issue_assessments"]) == 6
    assert not any("deferido" in a["conclusion"].lower() or "concedido" in a["conclusion"].lower()
                   for a in out["issue_assessments"])


def test_no_diagnosis_from_system():
    from app.modules.social_security import assess_dimension

    assessment = assess_dimension("incapacidade", {
        "facts": [{"id": "f9", "statement": "Atestado simples",
                   "epistemic_status": "alleged", "source_refs": ["s9"]}],
        "sources": [{"id": "s9"}],
    })
    assert "nenhum diagnóstico" in assessment["conclusion"].lower()
    assert assessment["status"] != "complete"


def test_beneficio_requires_full_params():
    from app.core.calculations import (
        CalculationBlockedError,
        CalculationRegistry,
        execute_registered_calculation,
    )

    registry = CalculationRegistry()
    register_calculation_rules(registry)
    out = execute_registered_calculation(
        {"formula": "beneficio_cenario", "formula_version": "1.0",
         "inputs": {"regime": "RGPS", "especie": "B32",
                    "salarios": ["2000.00", "3000.00"],
                    "regras_temporais": "vigentes"}},
        registry=registry,
    )
    assert out["result"] == "2500.00"
    with pytest.raises(CalculationBlockedError):
        execute_registered_calculation(
            {"formula": "beneficio_cenario", "formula_version": "1.0",
             "inputs": {"regime": "RGPS"}},
            registry=registry,
        )
