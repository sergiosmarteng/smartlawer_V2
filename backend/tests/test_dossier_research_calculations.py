"""Onda 0 Task 9 — pesquisa com origem e cálculos reproduzíveis."""

from datetime import date

import pytest


def test_cited_and_researched_stay_separate():
    from app.core.legal_research import research_issues

    batch = research_issues(
        [{"id": "q1", "question": "Vigência do art. 1.584 do CC",
          "cited_in_document": {"literal": "Art. 1.584, CC"}}],
        sources=[{"id": "planalto", "available": True, "organ": "Planalto",
                  "url": "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm"}],
        reference_date=date(2026, 10, 2),
    )
    assert batch["partial"] is False
    result = batch["results"][0]
    assert result["cited_literal"] == "Art. 1.584, CC"
    assert result["researched_url"].startswith("https://")
    assert result["cited_literal"] != result["researched_url"]


def test_unavailable_research_keeps_documentary_analysis_partial():
    from app.core.legal_research import research_issues

    batch = research_issues(
        [{"id": "q1", "question": "Tese vinculante aplicável"}],
        sources=[{"id": "tribunal", "available": False, "organ": "TST"}],
        reference_date=date(2026, 10, 2),
    )
    assert batch["partial"] is True
    assert batch["pending_actions"], "queda vira ação pendente, nunca apaga análise"
    assert batch["results"][0]["status"] in ("blocked", "partial")


def test_research_result_keeps_provenance():
    from app.core.legal_research import research_issues

    batch = research_issues(
        [{"id": "q1", "question": "Súmula 331 do TST"}],
        sources=[{"id": "tst", "available": True, "organ": "TST",
                  "url": "https://www.tst.jus.br/sumulas",
                  "excerpt": "Contrato de prestação de serviços..."}],
        reference_date=date(2026, 10, 2),
    )
    result = batch["results"][0]
    assert result["url"] and result["organ"] == "TST"
    assert result["consulted_at"] and result["excerpt"]


def test_unknown_formula_is_blocked():
    from app.core.calculations import CalculationBlockedError, execute_registered_calculation

    with pytest.raises(CalculationBlockedError):
        execute_registered_calculation(
            {"formula": "juros_livres", "formula_version": "9.9", "inputs": {}},
            registry={},
        )


def test_decimal_half_up_reproduces_result():
    from app.core.calculations import execute_registered_calculation

    first = execute_registered_calculation(
        {"formula": "sum_parcels", "formula_version": "1.0",
         "inputs": {"parcels": ["100.10", "200.20"]}},
        registry=None,
    )
    second = execute_registered_calculation(
        {"formula": "sum_parcels", "formula_version": "1.0",
         "inputs": {"parcels": ["100.10", "200.20"]}},
        registry=None,
    )
    assert first["result"] == "300.30"
    assert first["rounding"] == "half_up_centavos"
    assert first["result"] == second["result"]
    assert first["output_hash"] == second["output_hash"]
