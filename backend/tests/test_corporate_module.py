"""Onda 2A — módulo empresarial e societário (spec §3)."""

import pytest

from app.modules.corporate import (
    CORPORATE_SOURCES,
    CorporateModule,
    DESCRIPTOR,
    assess_dimension,
    register_calculation_rules,
)


def _case():
    return {
        "claims": [{"id": "c1", "title": "Exclusão de sócio", "source_refs": ["s1"]}],
        "facts": [
            {"id": "f1", "statement": "Contrato social com quotas dos sócios",
             "asserted_by": "parte-A", "epistemic_status": "documented",
             "source_refs": ["s1"]},
            {"id": "f2", "statement": "Administrador responsável por tudo",
             "asserted_by": "parte-A", "epistemic_status": "alleged",
             "source_refs": ["s2"]},
        ],
        "evidence": [{"id": "e1", "presence_status": "examined"}],
        "sources": [{"id": "s1", "page_number": 1}, {"id": "s2", "page_number": 2}],
    }


def test_descriptor_and_sources():
    assert DESCRIPTOR["module_id"] == "corporate"
    assert DESCRIPTOR["version"] == "1.0.0"
    assert "corporate" in DESCRIPTOR["supported_areas"]
    assert set(DESCRIPTOR["calculation_rules"]) == {
        "participacao_societaria@1.0", "rateio_cenario@1.0"}
    assert {s["id"] for s in CORPORATE_SOURCES} == {"cc", "lei6404", "lei11101"}
    assert all(s["url"].startswith("https://") for s in CORPORATE_SOURCES)


def test_registry_resolves_corporate():
    from app.core.classification import classify_blocks
    from app.core.module_registry import LegalModuleRegistry

    registry = LegalModuleRegistry.with_defaults()
    registry.register(CorporateModule())
    result = classify_blocks([{"normalized_text": "contrato social, sócios e quotas na assembleia"}])
    assert "corporate" in [result.primary_area, *result.related_areas]
    assert "corporate" in [m.module_id for m in registry.resolve(result)]


def test_seven_themes_with_real_refs():
    out = CorporateModule().analyze(_case())
    keys = {a["issue_key"] for a in out["issue_assessments"]}
    assert len(keys) == 7
    assert "corporate.estrutura" in keys and "corporate.crise" in keys
    for assessment in out["issue_assessments"]:
        for ref in assessment["supporting_source_refs"]:
            assert ref in ("s1", "s2")


def test_no_personal_liability_by_position():
    assessment = assess_dimension("obrigacoes", {
        "facts": [{"id": "f9", "statement": "Administrador da sociedade devedora",
                   "epistemic_status": "alleged", "source_refs": ["s9"]}],
        "sources": [{"id": "s9"}],
    })
    assert assessment["status"] != "complete"
    assert "posição" in assessment["conclusion"]


def test_recovery_stages_distinguished():
    assessment = assess_dimension("crise", {
        "facts": [{"id": "f9", "statement": "Pedido de recuperação judicial",
                   "epistemic_status": "documented", "source_refs": ["s9"]}],
        "sources": [{"id": "s9"}],
    })
    assert assessment["status"] == "partial"
    assert "deferimento" in assessment["conclusion"]


def test_participation_and_scenario_calculations():
    from app.core.calculations import (
        CalculationBlockedError,
        CalculationRegistry,
        execute_registered_calculation,
    )

    registry = CalculationRegistry()
    register_calculation_rules(registry)
    out = execute_registered_calculation(
        {"formula": "participacao_societaria", "formula_version": "1.0",
         "inputs": {"socio_quantidade": "30",
                    "quotas": [{"socio": "A", "quantidade": "30", "fonte": "s1"},
                               {"socio": "B", "quantidade": "70", "fonte": "s1"}]}},
        registry=registry,
    )
    assert out["result"] == "30.00"
    out2 = execute_registered_calculation(
        {"formula": "rateio_cenario", "formula_version": "1.0",
         "inputs": {"montante": "10000.00", "criterio": "quotas",
                    "fracao_percentual": "25"}},
        registry=registry,
    )
    assert out2["result"] == "2500.00"
    with pytest.raises(CalculationBlockedError):
        execute_registered_calculation(
            {"formula": "participacao_societaria", "formula_version": "1.0",
             "inputs": {"socio_quantidade": "30", "quotas": []}},
            registry=registry,
        )
    with pytest.raises(CalculationBlockedError):
        execute_registered_calculation(
            {"formula": "rateio_cenario", "formula_version": "1.0",
             "inputs": {"montante": "10000.00"}},
            registry=registry,
        )


def test_runner_does_not_mutate_core():
    from app.core.module_runner import run_module_analyses

    case = _case()
    before = [dict(c) for c in case["claims"]]
    results, limitations = run_module_analyses(
        modules=[CorporateModule()], case_data=case)
    assert set(results) == {"corporate"}
    assert case["claims"] == before
    assert isinstance(limitations, list)
