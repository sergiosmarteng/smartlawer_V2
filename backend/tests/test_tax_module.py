"""Onda 2B — módulo tributário (spec §5)."""

import pytest

from app.modules.tax import (
    DESCRIPTOR,
    TAX_SOURCES,
    TaxModule,
    assess_dimension,
    register_calculation_rules,
)


def _case():
    return {
        "claims": [{"id": "c1", "title": "Anulação de auto", "source_refs": ["s1"]}],
        "facts": [
            {"id": "f1", "statement": "Auto de infração de ICMS do ente estadual",
             "asserted_by": "parte-A", "epistemic_status": "documented",
             "source_refs": ["s1"]},
            {"id": "f2", "statement": "Prescrição alegada",
             "asserted_by": "parte-A", "epistemic_status": "alleged",
             "source_refs": ["s2"]},
        ],
        "evidence": [{"id": "e1", "presence_status": "examined"}],
        "sources": [{"id": "s1", "page_number": 1}, {"id": "s2", "page_number": 2}],
    }


def test_descriptor_and_sources():
    assert DESCRIPTOR["module_id"] == "tax"
    assert DESCRIPTOR["version"] == "1.0.0"
    assert "tax" in DESCRIPTOR["supported_areas"]
    assert DESCRIPTOR["calculation_rules"] == ["tributo_competencia@1.0"]
    assert {s["id"] for s in TAX_SOURCES} == {"ctn"}
    assert all(s["url"].startswith("https://") for s in TAX_SOURCES)


def test_registry_resolves_tax():
    from app.core.classification import classify_blocks
    from app.core.module_registry import LegalModuleRegistry

    registry = LegalModuleRegistry.with_defaults()
    registry.register(TaxModule())
    result = classify_blocks([{"normalized_text": "auto de infração de ICMS com ente estadual"}])
    assert "tax" in [result.primary_area, *result.related_areas]
    assert "tax" in [m.module_id for m in registry.resolve(result)]


def test_seven_themes_with_real_refs():
    out = TaxModule().analyze(_case())
    keys = {a["issue_key"] for a in out["issue_assessments"]}
    assert len(keys) == 7
    assert "tax.competencia" in keys and "tax.reforma" in keys
    for assessment in out["issue_assessments"]:
        for ref in assessment["supporting_source_refs"]:
            assert ref in ("s1", "s2")


def test_no_definitive_credit_from_isolated_assessment():
    assessment = assess_dimension("credito", {
        "facts": [{"id": "f9", "statement": "Auto com crédito apurado",
                   "epistemic_status": "alleged", "source_refs": ["s9"]}],
        "sources": [{"id": "s9"}],
    })
    assert assessment["status"] != "complete"
    assert "competência" in assessment["conclusion"]


def test_no_prescription_without_milestones():
    assessment = assess_dimension("tempo", {
        "facts": [{"id": "f9", "statement": "Prescrição consumada",
                   "epistemic_status": "alleged", "source_refs": ["s9"]}],
        "sources": [{"id": "s9"}],
    })
    assert assessment["status"] == "blocked"
    assert "marco" in " ".join(assessment["missing_inputs"])


def test_competence_calculation_auditable_and_blocked():
    from app.core.calculations import (
        CalculationBlockedError,
        CalculationRegistry,
        execute_registered_calculation,
    )

    registry = CalculationRegistry()
    register_calculation_rules(registry)
    out = execute_registered_calculation(
        {"formula": "tributo_competencia", "formula_version": "1.0",
         "inputs": {"base": "100000.00", "aliquota": "18",
                    "competencia": "2026-01", "fonte_ente": "SEFAZ",
                    "deducoes": "1000.00", "pagamentos": "5000.00",
                    "atualizacao": "200.00"}},
        registry=registry,
    )
    assert out["result"] == "12200.00"
    assert out["rounding"] == "half_up_centavos"
    with pytest.raises(CalculationBlockedError):
        execute_registered_calculation(
            {"formula": "tributo_competencia", "formula_version": "1.0",
             "inputs": {"base": "100000.00"}},
            registry=registry,
        )


def test_runner_does_not_mutate_core():
    from app.core.module_runner import run_module_analyses

    case = _case()
    before = [dict(c) for c in case["claims"]]
    results, limitations = run_module_analyses(
        modules=[TaxModule()], case_data=case)
    assert set(results) == {"tax"}
    assert case["claims"] == before
    assert isinstance(limitations, list)
