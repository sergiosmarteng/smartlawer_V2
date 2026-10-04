"""Onda 2B — módulo imobiliário (spec §7)."""

import pytest

from app.modules.real_estate import (
    DESCRIPTOR,
    REAL_ESTATE_SOURCES,
    RealEstateModule,
    assess_dimension,
    register_calculation_rules,
)


def _case():
    return {
        "claims": [{"id": "c1", "title": "Adjudicação", "source_refs": ["s1"]}],
        "facts": [
            {"id": "f1", "statement": "Escritura de promessa registrada",
             "asserted_by": "parte-A", "epistemic_status": "documented",
             "source_refs": ["s1"]},
            {"id": "f2", "statement": "Matrícula antiga do imóvel",
             "asserted_by": "parte-A", "epistemic_status": "alleged",
             "source_refs": ["s2"]},
        ],
        "evidence": [{"id": "e1", "presence_status": "examined"}],
        "sources": [{"id": "s1", "page_number": 1}, {"id": "s2", "page_number": 2}],
    }


def test_descriptor_and_sources():
    assert DESCRIPTOR["module_id"] == "real_estate"
    assert DESCRIPTOR["version"] == "1.0.0"
    assert "real_estate" in DESCRIPTOR["supported_areas"]
    assert DESCRIPTOR["calculation_rules"] == ["parcelas_mora_rateio@1.0"]
    assert {s["id"] for s in REAL_ESTATE_SOURCES} == {"cc", "lrp"}
    assert all(s["url"].startswith("https://") for s in REAL_ESTATE_SOURCES)


def test_registry_resolves_real_estate():
    from app.core.classification import classify_blocks
    from app.core.module_registry import LegalModuleRegistry

    registry = LegalModuleRegistry.with_defaults()
    registry.register(RealEstateModule())
    result = classify_blocks([{"normalized_text": "matrícula do imóvel e escritura"}])
    assert "real_estate" in [result.primary_area, *result.related_areas]
    assert "real_estate" in [m.module_id for m in registry.resolve(result)]


def test_six_themes_with_real_refs():
    out = RealEstateModule().analyze(_case())
    keys = {a["issue_key"] for a in out["issue_assessments"]}
    assert len(keys) == 6
    assert "real_estate.direito" in keys and "real_estate.registro" in keys
    for assessment in out["issue_assessments"]:
        for ref in assessment["supporting_source_refs"]:
            assert ref in ("s1", "s2")


def test_old_matricula_is_not_current_ownership():
    assessment = assess_dimension("registro", {
        "facts": [{"id": "f9", "statement": "Matrícula antiga do imóvel",
                   "epistemic_status": "alleged", "source_refs": ["s9"]}],
        "sources": [{"id": "s9"}],
    })
    assert assessment["status"] != "complete"
    assert "certidão atualizada" in " ".join(assessment["missing_inputs"])


def test_urbanismo_without_ente_is_blocked():
    assessment = assess_dimension("urbanismo", {
        "facts": [{"id": "f9", "statement": "Zoneamento irregular",
                   "epistemic_status": "alleged", "source_refs": ["s9"]}],
        "sources": [{"id": "s9"}],
    })
    assert assessment["status"] == "blocked"
    assert "ente" in " ".join(assessment["missing_inputs"])


def test_parcelas_require_contract_payments_index():
    from app.core.calculations import (
        CalculationBlockedError,
        CalculationRegistry,
        execute_registered_calculation,
    )

    registry = CalculationRegistry()
    register_calculation_rules(registry)
    out = execute_registered_calculation(
        {"formula": "parcelas_mora_rateio", "formula_version": "1.0",
         "inputs": {"contrato": "ctr-1", "parcelas": ["1000.00", "1000.00"],
                    "pagamentos": ["1000.00"], "indice": "10"}},
        registry=registry,
    )
    assert out["result"] == "1100.00"
    with pytest.raises(CalculationBlockedError):
        execute_registered_calculation(
            {"formula": "parcelas_mora_rateio", "formula_version": "1.0",
             "inputs": {"contrato": "ctr-1", "parcelas": ["1000.00"]}},
            registry=registry,
        )


def test_runner_does_not_mutate_core():
    from app.core.module_runner import run_module_analyses

    case = _case()
    before = [dict(c) for c in case["claims"]]
    results, limitations = run_module_analyses(
        modules=[RealEstateModule()], case_data=case)
    assert set(results) == {"real_estate"}
    assert case["claims"] == before
    assert isinstance(limitations, list)
