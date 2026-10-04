"""Onda 2B — módulo administrativo (spec §6)."""

import pytest

from app.modules.administrative import (
    ADMINISTRATIVE_SOURCES,
    AdministrativeModule,
    DESCRIPTOR,
    assess_dimension,
    register_calculation_rules,
)


def _case():
    return {
        "claims": [{"id": "c1", "title": "Anulação de sanção", "source_refs": ["s1"]}],
        "facts": [
            {"id": "f1", "statement": "Edital de licitação com critérios",
             "asserted_by": "parte-A", "epistemic_status": "documented",
             "source_refs": ["s1"]},
            {"id": "f2", "statement": "Notícia de irregularidade",
             "asserted_by": "parte-A", "epistemic_status": "alleged",
             "source_refs": ["s2"]},
        ],
        "evidence": [{"id": "e1", "presence_status": "examined"}],
        "sources": [{"id": "s1", "page_number": 1}, {"id": "s2", "page_number": 2}],
    }


def test_descriptor_and_sources():
    assert DESCRIPTOR["module_id"] == "administrative"
    assert DESCRIPTOR["version"] == "1.0.0"
    assert "administrative" in DESCRIPTOR["supported_areas"]
    assert DESCRIPTOR["calculation_rules"] == ["reajuste_contrato_publico@1.0"]
    assert {s["id"] for s in ADMINISTRATIVE_SOURCES} == {"lei14133"}
    assert all(s["url"].startswith("https://") for s in ADMINISTRATIVE_SOURCES)


def test_registry_resolves_administrative():
    from app.core.classification import classify_blocks
    from app.core.module_registry import LegalModuleRegistry

    registry = LegalModuleRegistry.with_defaults()
    registry.register(AdministrativeModule())
    result = classify_blocks([{"normalized_text": "edital de licitação e contrato administrativo"}])
    assert "administrative" in [result.primary_area, *result.related_areas]
    assert "administrative" in [m.module_id for m in registry.resolve(result)]


def test_six_themes_with_real_refs():
    out = AdministrativeModule().analyze(_case())
    keys = {a["issue_key"] for a in out["issue_assessments"]}
    assert len(keys) == 6
    assert "administrative.licitacao" in keys
    for assessment in out["issue_assessments"]:
        for ref in assessment["supporting_source_refs"]:
            assert ref in ("s1", "s2")


def test_news_is_not_final_sanction():
    assessment = assess_dimension("responsabilizacao", {
        "facts": [{"id": "f9", "statement": "Denúncia de irregularidade",
                   "epistemic_status": "alleged", "source_refs": ["s9"]}],
        "sources": [{"id": "s9"}],
    })
    assert assessment["status"] != "complete"
    assert "sanção final" in assessment["conclusion"]


def test_reajuste_requires_clause_fact_period_index():
    from app.core.calculations import (
        CalculationBlockedError,
        CalculationRegistry,
        execute_registered_calculation,
    )

    registry = CalculationRegistry()
    register_calculation_rules(registry)
    out = execute_registered_calculation(
        {"formula": "reajuste_contrato_publico", "formula_version": "1.0",
         "inputs": {"base": "50000.00", "indice": "4",
                    "clausula": "7.1", "fato": "medição 12",
                    "periodo": "2026-01"}},
        registry=registry,
    )
    assert out["result"] == "52000.00"
    with pytest.raises(CalculationBlockedError):
        execute_registered_calculation(
            {"formula": "reajuste_contrato_publico", "formula_version": "1.0",
             "inputs": {"base": "50000.00", "indice": "4"}},
            registry=registry,
        )


def test_runner_does_not_mutate_core():
    from app.core.module_runner import run_module_analyses

    case = _case()
    before = [dict(c) for c in case["claims"]]
    results, limitations = run_module_analyses(
        modules=[AdministrativeModule()], case_data=case)
    assert set(results) == {"administrative"}
    assert case["claims"] == before
    assert isinstance(limitations, list)
