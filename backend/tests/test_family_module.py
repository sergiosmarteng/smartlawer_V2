"""Onda 1A — módulo família e sucessões (spec §5)."""

import pytest

from app.modules.family import (
    DESCRIPTOR,
    FAMILY_SOURCES,
    FamilyModule,
    assess_dimension,
    register_calculation_rules,
)


def _guarda_case():
    return {
        "claims": [
            {"id": "claim-1", "title": "Guarda compartilhada", "source_refs": ["src-1"]},
            {"id": "claim-2", "title": "Alimentos", "source_refs": ["src-2"]},
        ],
        "facts": [
            {"id": "f1", "statement": "Filho menor sob guarda compartilhada",
             "asserted_by": "parte-A", "epistemic_status": "documented",
             "source_refs": ["src-1"]},
            {"id": "f2", "statement": "Renda do alimentante",
             "asserted_by": "parte-A", "epistemic_status": "alleged",
             "source_refs": ["src-2"]},
        ],
        "evidence": [
            {"id": "ev1", "presence_status": "examined", "location_refs": ["src-1"]},
            {"id": "ev2", "presence_status": "mentioned_not_located", "location_refs": []},
        ],
        "sources": [{"id": "src-1", "page_number": 1}, {"id": "src-2", "page_number": 2}],
        "coverage": {"pages_total": 12, "pages_extracted": 12},
    }


def test_descriptor_registered_with_contract():
    assert DESCRIPTOR["module_id"] == "family"
    assert DESCRIPTOR["version"] == "1.0.0"
    assert "family" in DESCRIPTOR["supported_areas"]
    assert DESCRIPTOR["calculation_rules"] == ["alimentos_scenario@1.0"]
    assert {"cc", "cpc", "eca"} <= set(DESCRIPTOR["research_sources"])
    assert {s["id"] for s in FAMILY_SOURCES} == {"cc", "cpc", "eca"}
    assert all(s["url"].startswith("https://") for s in FAMILY_SOURCES)


def test_registry_resolves_family_classification():
    from app.core.classification import classify_blocks
    from app.core.module_registry import LegalModuleRegistry

    registry = LegalModuleRegistry.with_defaults()
    registry.register(FamilyModule())
    result = classify_blocks([{"normalized_text": "guarda compartilhada do filho menor e alimentos"}])
    assert "family" in [result.primary_area, *result.related_areas]
    assert "family" in [m.module_id for m in registry.resolve(result)]


def test_regression_guarda_alimentos_has_refs_and_states():
    module = FamilyModule()
    out = module.analyze(_guarda_case())
    assert out["module_id"] == "family"
    assert out["status"] in ("complete", "partial")
    keys = {a["issue_key"] for a in out["issue_assessments"]}
    assert "family.guarda_convivencia" in keys and "family.alimentos" in keys
    for assessment in out["issue_assessments"]:
        for ref in assessment["supporting_source_refs"]:
            assert ref in ("src-1", "src-2")


def test_no_capacity_conclusion_without_source():
    assessment = assess_dimension("alimentos", {
        "facts": [{"id": "f9", "statement": "Renda alta do alimentante",
                   "asserted_by": "parte-A", "epistemic_status": "alleged",
                   "source_refs": []}],
        "sources": [],
    })
    assert assessment["status"] != "complete"
    assert assessment["missing_inputs"]


def test_child_risk_never_complete_on_bare_allegation():
    assessment = assess_dimension("guarda_convivencia", {
        "facts": [{"id": "f9", "statement": "Risco à criança na convivência",
                   "asserted_by": "parte-A", "epistemic_status": "alleged",
                   "source_refs": []}],
        "sources": [],
        "evidence": [],
    })
    assert assessment["status"] != "complete"
    assert "condicionado" in assessment["conclusion"]


def test_alimentos_calculation_is_explicit_scenario():
    from app.core.calculations import (
        CalculationBlockedError,
        CalculationRegistry,
        execute_registered_calculation,
    )

    registry = CalculationRegistry()
    register_calculation_rules(registry)
    out = execute_registered_calculation(
        {"formula": "alimentos_scenario", "formula_version": "1.0",
         "inputs": {"base_renda": "10000.00", "percentual": "30"}},
        registry=registry,
    )
    assert out["result"] == "3000.00"
    assert out["rounding"] == "half_up_centavos"
    with pytest.raises(CalculationBlockedError):
        execute_registered_calculation(
            {"formula": "alimentos_scenario", "formula_version": "1.0",
             "inputs": {"base_renda": "10000.00"}},
            registry=registry,
        )


def test_runner_runs_family_without_touching_core():
    from app.core.module_runner import run_module_analyses

    case = _guarda_case()
    before = [dict(c) for c in case["claims"]]
    results, limitations = run_module_analyses(
        modules=[FamilyModule()], case_data=case)
    assert set(results) == {"family"}
    assert case["claims"] == before
    assert isinstance(limitations, list)
