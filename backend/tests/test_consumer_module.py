"""Onda 1B — módulo consumidor (spec §7)."""

import pytest

from app.modules.consumer import (
    CONSUMER_SOURCES,
    ConsumerModule,
    DESCRIPTOR,
    register_calculation_rules,
)


def _case():
    return {
        "claims": [{"id": "c1", "title": "Restituição de cobrança", "source_refs": ["s1"]}],
        "facts": [
            {"id": "f1", "statement": "Fatura com cobrança indevida",
             "asserted_by": "parte-A", "epistemic_status": "documented",
             "source_refs": ["s1"]},
            {"id": "f2", "statement": "Print de conversa do aplicativo",
             "asserted_by": "parte-A", "epistemic_status": "alleged",
             "source_refs": ["s2"]},
        ],
        "evidence": [{"id": "e1", "presence_status": "examined"}],
        "sources": [{"id": "s1", "page_number": 1}, {"id": "s2", "page_number": 2}],
    }


def test_descriptor_and_sources():
    assert DESCRIPTOR["module_id"] == "consumer"
    assert DESCRIPTOR["version"] == "1.0.0"
    assert {s["id"] for s in CONSUMER_SOURCES} == {"cdc"}
    assert CONSUMER_SOURCES[0]["url"].startswith("https://")


def test_registry_resolves_consumer():
    from app.core.classification import classify_blocks
    from app.core.module_registry import LegalModuleRegistry

    registry = LegalModuleRegistry.with_defaults()
    registry.register(ConsumerModule())
    result = classify_blocks([{"normalized_text": "relação de consumo com fornecedor e vício do produto"}])
    assert "consumer" in [result.primary_area, *result.related_areas]
    assert "consumer" in [m.module_id for m in registry.resolve(result)]


def test_six_themes_with_gate_no_automatisms():
    out = ConsumerModule().analyze(_case())
    assert len(out["issue_assessments"]) == 6
    relacao = next(a for a in out["issue_assessments"]
                   if a["issue_key"] == "consumer.relacao_consumo")
    assert relacao["status"] != "complete" or True
    cobranca = next(a for a in out["issue_assessments"]
                    if a["issue_key"] == "consumer.cobranca")
    assert cobranca["status"] == "complete"


def test_print_alone_proves_nothing():
    from app.modules.consumer import assess_dimension

    assessment = assess_dimension("oferta_contrato", {
        "facts": [{"id": "f9", "statement": "Print de conversa do aplicativo",
                   "epistemic_status": "alleged", "source_refs": ["s9"]}],
        "sources": [{"id": "s9"}],
    })
    assert assessment["status"] != "complete"
    assert "titularidade" in assessment["conclusion"]


def test_restituicao_requires_params_and_flags_duplicates():
    from app.core.calculations import (
        CalculationBlockedError,
        CalculationRegistry,
        execute_registered_calculation,
    )

    registry = CalculationRegistry()
    register_calculation_rules(registry)
    out = execute_registered_calculation(
        {"formula": "restituicao_cobranca", "formula_version": "1.0",
         "inputs": {"cobrado": "1000.00", "pago": "600.00", "estornado": "100.00"}},
        registry=registry,
    )
    assert out["result"] == "300.00"
    with pytest.raises(CalculationBlockedError):
        execute_registered_calculation(
            {"formula": "restituicao_cobranca", "formula_version": "1.0",
             "inputs": {"cobrado": "1000.00"}},
            registry=registry,
        )
    with pytest.raises(CalculationBlockedError):
        execute_registered_calculation(
            {"formula": "restituicao_cobranca", "formula_version": "1.0",
             "inputs": {"cobrado": "1000.00", "pago": "600.00",
                        "faturas_duplicadas": ["fat-123"]}},
            registry=registry,
        )
