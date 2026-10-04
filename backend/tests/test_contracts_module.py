"""Onda 2A — módulo contratos (spec §4)."""

import pytest

from app.modules.contracts import (
    CONTRACTS_SOURCES,
    ContractsModule,
    DESCRIPTOR,
    assess_dimension,
    diff_versions,
    register_calculation_rules,
)


def _case():
    return {
        "claims": [{"id": "c1", "title": "Reajuste de aluguel", "source_refs": ["s1"]}],
        "facts": [
            {"id": "f1", "statement": "Contrato com cláusula de reajuste anual",
             "asserted_by": "parte-A", "epistemic_status": "documented",
             "source_refs": ["s1"]},
            {"id": "f2", "statement": "Cláusula penal genérica",
             "asserted_by": "parte-A", "epistemic_status": "alleged",
             "source_refs": ["s2"]},
        ],
        "evidence": [{"id": "e1", "presence_status": "examined"}],
        "sources": [{"id": "s1", "page_number": 1}, {"id": "s2", "page_number": 2}],
    }


def test_descriptor_and_sources():
    assert DESCRIPTOR["module_id"] == "contracts"
    assert DESCRIPTOR["version"] == "1.0.0"
    assert "contracts" in DESCRIPTOR["supported_areas"]
    assert DESCRIPTOR["calculation_rules"] == ["reajuste_contratual@1.0"]
    assert {s["id"] for s in CONTRACTS_SOURCES} == {"cc"}
    assert all(s["url"].startswith("https://") for s in CONTRACTS_SOURCES)


def test_registry_resolves_contracts():
    from app.core.classification import classify_blocks
    from app.core.module_registry import LegalModuleRegistry

    registry = LegalModuleRegistry.with_defaults()
    registry.register(ContractsModule())
    result = classify_blocks([{"normalized_text": "contrato com cláusula de reajuste e aditivo"}])
    assert "contracts" in [result.primary_area, *result.related_areas]
    assert "contracts" in [m.module_id for m in registry.resolve(result)]


def test_six_themes_with_real_refs():
    out = ContractsModule().analyze(_case())
    keys = {a["issue_key"] for a in out["issue_assessments"]}
    assert len(keys) == 6
    assert "contracts.formacao" in keys and "contracts.versoes" in keys
    for assessment in out["issue_assessments"]:
        for ref in assessment["supporting_source_refs"]:
            assert ref in ("s1", "s2")


def test_reajuste_without_params_is_blocked():
    assessment = assess_dimension("financeiro", {
        "facts": [{"id": "f9", "statement": "Multa por atraso",
                   "epistemic_status": "alleged", "source_refs": ["s9"]}],
        "sources": [{"id": "s9"}],
    })
    assert assessment["status"] == "blocked"
    assert "índice" in " ".join(assessment["missing_inputs"])


def test_no_validity_in_abstract():
    assessment = assess_dimension("risco", {
        "facts": [{"id": "f9", "statement": "Cláusula possivelmente abusiva",
                   "epistemic_status": "alleged", "source_refs": ["s9"]}],
        "sources": [{"id": "s9"}],
    })
    assert assessment["status"] == "partial"
    assert "abstrato" in assessment["conclusion"]


def test_version_diff_preserves_original_text_and_position():
    old = [{"id": "cl-3", "text": "Multa de 2%.", "position": 12}]
    new = [{"id": "cl-3", "text": "Multa de 10%.", "position": 12},
           {"id": "cl-9", "text": "Nova cláusula.", "position": 30}]
    diff = diff_versions(old, new)
    changed = next(d for d in diff if d["clause_id"] == "cl-3")
    assert changed["change"] == "changed"
    assert changed["old_text"] == "Multa de 2%."
    assert changed["new_text"] == "Multa de 10%."
    assert changed["position"] == 12
    assert next(d for d in diff if d["clause_id"] == "cl-9")["change"] == "added"


def test_reajuste_calculation_reproducible_and_blocked():
    from app.core.calculations import (
        CalculationBlockedError,
        CalculationRegistry,
        execute_registered_calculation,
    )

    registry = CalculationRegistry()
    register_calculation_rules(registry)
    out = execute_registered_calculation(
        {"formula": "reajuste_contratual", "formula_version": "1.0",
         "inputs": {"base": "2000.00", "indice_percentual": "5",
                    "clausula_vigente": True, "termo": "2026-01-01",
                    "periodo": "12 meses"}},
        registry=registry,
    )
    assert out["result"] == "2100.00"
    assert out["rounding"] == "half_up_centavos"
    with pytest.raises(CalculationBlockedError):
        execute_registered_calculation(
            {"formula": "reajuste_contratual", "formula_version": "1.0",
             "inputs": {"base": "2000.00"}},
            registry=registry,
        )


def test_runner_does_not_mutate_core():
    from app.core.module_runner import run_module_analyses

    case = _case()
    before = [dict(c) for c in case["claims"]]
    results, limitations = run_module_analyses(
        modules=[ContractsModule()], case_data=case)
    assert set(results) == {"contracts"}
    assert case["claims"] == before
    assert isinstance(limitations, list)
