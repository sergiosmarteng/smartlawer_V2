"""Onda 1A — módulo cível e processo civil (spec §4)."""

import pytest

from app.modules.civil_procedure import (
    CIVIL_PROCEDURE_SOURCES,
    CivilProcedureModule,
    DESCRIPTOR,
    assess_dimension,
    register_calculation_rules,
)


def _case():
    return {
        "claims": [{"id": "c1", "title": "Cobrança", "source_refs": ["s1"]}],
        "facts": [
            {"id": "f1", "statement": "Contrato com obrigação de pagamento",
             "asserted_by": "parte-A", "epistemic_status": "documented",
             "source_refs": ["s1"]},
            {"id": "f2", "statement": "Valor da causa em rito comum",
             "asserted_by": "parte-A", "epistemic_status": "alleged",
             "source_refs": ["s2"]},
        ],
        "evidence": [{"id": "e1", "presence_status": "examined"}],
        "sources": [{"id": "s1", "page_number": 1}, {"id": "s2", "page_number": 2}],
    }


def test_descriptor_and_sources():
    assert DESCRIPTOR["module_id"] == "civil_procedure"
    assert DESCRIPTOR["version"] == "1.0.0"
    assert "civil_procedure" in DESCRIPTOR["supported_areas"]
    assert {s["id"] for s in CIVIL_PROCEDURE_SOURCES} == {"cc", "cpc", "juizados"}
    assert all(s["url"].startswith("https://") for s in CIVIL_PROCEDURE_SOURCES)


def test_registry_resolves_civil_classification():
    from app.core.classification import classify_blocks
    from app.core.module_registry import LegalModuleRegistry

    registry = LegalModuleRegistry.with_defaults()
    registry.register(CivilProcedureModule())
    result = classify_blocks([{"normalized_text": "rito do procedimento comum e competência do foro"}])
    assert "civil_procedure" in [result.primary_area, *result.related_areas]
    assert "civil_procedure" in [m.module_id for m in registry.resolve(result)]


def test_matrix_covers_seven_themes_with_refs():
    out = CivilProcedureModule().analyze(_case())
    keys = {a["issue_key"] for a in out["issue_assessments"]}
    assert len(keys) == 7
    assert "civil_procedure.relacao_material" in keys
    assert out["issue_assessments"][0]["supporting_source_refs"]


def test_no_competence_from_value_alone():
    assessment = assess_dimension("rito_competencia", {
        "facts": [{"id": "f9", "statement": "Valor da causa alto",
                   "epistemic_status": "alleged", "source_refs": ["s9"]}],
        "sources": [{"id": "s9"}],
    })
    assert assessment["status"] != "complete"
    assert "natureza" in " ".join(assessment["missing_inputs"])


def test_no_deadline_without_intimation():
    assessment = assess_dimension("tempo", {
        "facts": [{"id": "f9", "statement": "Prazo em curso",
                   "epistemic_status": "alleged", "source_refs": ["s9"]}],
        "sources": [{"id": "s9"}],
    })
    assert assessment["status"] != "complete"
    assert any("intima" in m for m in assessment["missing_inputs"])


def test_petition_is_not_proof_of_breach():
    out = CivilProcedureModule().analyze({
        "claims": [{"id": "c1", "title": "Cobrança"}],
        "facts": [{"id": "f9", "statement": "Petição narra inadimplemento",
                   "epistemic_status": "alleged", "source_refs": []}],
        "evidence": [],
        "sources": [],
    })
    relacao = next(a for a in out["issue_assessments"]
                   if a["issue_key"] == "civil_procedure.relacao_material")
    assert relacao["status"] != "complete"


def test_documented_parcels_sum_and_undocumented_block():
    from app.core.calculations import (
        CalculationBlockedError,
        CalculationRegistry,
        execute_registered_calculation,
    )

    registry = CalculationRegistry()
    register_calculation_rules(registry)
    out = execute_registered_calculation(
        {"formula": "soma_parcelas_documentadas", "formula_version": "1.0",
         "inputs": {"parcels": [
             {"label": "p1", "value": "1000.00", "source_ref": "s1"},
             {"label": "p2", "value": "500.50", "source_ref": "s1"}]}},
        registry=registry,
    )
    assert out["result"] == "1500.50"
    with pytest.raises(CalculationBlockedError):
        execute_registered_calculation(
            {"formula": "soma_parcelas_documentadas", "formula_version": "1.0",
             "inputs": {"parcels": [{"label": "p1", "value": "1000.00"}]}},
            registry=registry,
        )
