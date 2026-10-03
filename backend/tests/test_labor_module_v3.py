"""Onda 1B — módulo trabalhista no contrato V3 (spec §6)."""

import pytest

from app.modules.labor import DESCRIPTOR
from app.modules.labor.module import (
    LABOR_SOURCES,
    LABOR_THEMES,
    LaborModule,
    assess_theme,
    register_calculation_rules,
)


def _case():
    return {
        "claims": [{"id": "c1", "title": "Verbas rescisórias", "source_refs": ["s1"]}],
        "facts": [
            {"id": "f1", "statement": "Vínculo de emprego com CTPS assinada",
             "asserted_by": "parte-A", "epistemic_status": "documented",
             "source_refs": ["s1"]},
            {"id": "f2", "statement": "Acidente com equipamento",
             "asserted_by": "parte-A", "epistemic_status": "alleged",
             "source_refs": ["s2"]},
        ],
        "evidence": [
            {"id": "ev1", "kind": "document", "presence_status": "examined"},
            {"id": "foto-equip", "kind": "photo", "presence_status": "examined"},
        ],
        "sources": [{"id": "s1", "page_number": 1}, {"id": "s2", "page_number": 2}],
    }


def test_descriptor_v3_contract():
    assert DESCRIPTOR["module_id"] == "labor"
    assert DESCRIPTOR["version"] == "1.0.0"
    assert "labor" in DESCRIPTOR["supported_areas"]
    assert DESCRIPTOR["calculation_rules"] == ["rubricas_trabalhistas@1.0"]
    assert {s["id"] for s in LABOR_SOURCES} == {"clt", "lei8213", "nr", "cct"}


def test_registry_resolves_labor():
    from app.core.classification import classify_blocks
    from app.core.module_registry import LegalModuleRegistry

    registry = LegalModuleRegistry.with_defaults()
    registry.register(LaborModule())
    result = classify_blocks([{"normalized_text": "reclamação trabalhista com vínculo de emprego e verbas rescisórias"}])
    assert "labor" in [result.primary_area, *result.related_areas]
    assert "labor" in [m.module_id for m in registry.resolve(result)]


def test_six_themes_assessed_with_refs():
    out = LaborModule().analyze(_case())
    keys = {a["issue_key"] for a in out["issue_assessments"]}
    assert len(keys) == 6
    assert {f"labor.{k}" for k, _, _ in LABOR_THEMES} == keys
    vinculo = next(a for a in out["issue_assessments"] if a["issue_key"] == "labor.vinculo")
    assert vinculo["status"] == "complete"


def test_photo_alone_never_proves_incapacity_culpa_nexo():
    assessment = assess_theme("acidente_doenca", {
        "facts": [{"id": "f9", "statement": "Acidente com equipamento",
                   "epistemic_status": "alleged", "source_refs": ["s9"]}],
        "evidence": [{"id": "foto", "kind": "photo", "presence_status": "examined"}],
        "sources": [{"id": "s9"}],
    })
    assert assessment["status"] != "complete"
    assert "perícia" in " ".join(assessment["missing_inputs"])


def test_mentioned_pericia_stays_mentioned():
    case = _case()
    case["evidence"].append(
        {"id": "pericia", "kind": "pericia_medica", "presence_status": "mentioned_not_located"})
    out = LaborModule().analyze(case)
    assert out["status"] in ("complete", "partial")


def test_rubricas_require_params_and_detect_overlap():
    from app.core.calculations import (
        CalculationBlockedError,
        CalculationRegistry,
        execute_registered_calculation,
    )
    from app.modules.labor.findings import detect_overlaps

    registry = CalculationRegistry()
    register_calculation_rules(registry)
    out = execute_registered_calculation(
        {"formula": "rubricas_trabalhistas", "formula_version": "1.0",
         "inputs": {"remuneracao": "5000.00", "periodo": "12 meses",
                    "jornada": "220h", "reflexos": "1000.00", "exclusoes": "500.00"}},
        registry=registry,
    )
    assert out["result"] == "5500.00"
    with pytest.raises(CalculationBlockedError):
        execute_registered_calculation(
            {"formula": "rubricas_trabalhistas", "formula_version": "1.0",
             "inputs": {"remuneracao": "5000.00"}},
            registry=registry,
        )
    overlaps = detect_overlaps([
        {"id": "c1", "title": "A",
         "related_claims": [{"claim_id": "c2", "relation": "overlaps"}]},
        {"id": "c2", "title": "B", "related_claims": []},
    ])
    assert any(f.code == "POSSIBLE_OVERLAP" for f in overlaps)
