"""V2 T09 — cálculos determinísticos (aceite + conferências §11.1)."""

from decimal import Decimal

import pytest

from app.core.calculations import (
    difference,
    parse_br_money,
    pension_projection,
    percent_of_base,
    sum_parcels,
)


def test_parse_br_money_and_ambiguous():
    assert parse_br_money("R$ 215.760,00").value == Decimal("215760.00")
    assert parse_br_money("R$ 1.400,00").value == Decimal("1400.00")
    assert parse_br_money("a liquidar").value is None
    assert parse_br_money("").value is None


def test_subtotal_valor_da_causa_exato():
    record = sum_parcels(
        [
            {"label": "materiais", "value": "R$ 215.760,00"},
            {"label": "morais", "value": "R$ 70.000,00"},
            {"label": "estéticos", "value": "R$ 99.800,00"},
            {"label": "coletiva", "value": "R$ 16.398,20"},
        ]
    )
    assert record.result == "401958.20"
    assert record.formula_version == "1.0"
    assert record.notes == []


def test_salary_relations_are_narrated_not_proven():
    composed = sum_parcels(
        [{"label": "salário", "value": "R$ 1.200,00"}, {"label": "adicional", "value": "R$ 200,00"}]
    )
    assert composed.result == "1400.00"
    assert difference("R$ 1.400,00", "R$ 820,00").result == "580.00"


def test_pension_projection_flags_inferred_chain():
    record = pension_projection("R$ 580,00", 31, inferred_chain=True)
    assert record.result == "215760.00"
    assert any("reconstruído" in a for a in record.assumptions)


def test_overlaps_excluded_from_auto_sum():
    record = sum_parcels(
        [
            {"label": "materiais", "value": "R$ 215.760,00"},
            {"label": "pensão mensal", "value": "R$ 1.400,00", "cumulative": False},
        ]
    )
    assert record.result == "215760.00"
    assert len(record.notes) == 1
    assert "hipótese a revisar" in record.notes[0]


def test_pericia_dependency_declared_not_chosen():
    record = pension_projection("R$ 580,00", 31, depends_on_pericia=True)
    assert any("perícia" in a for a in record.assumptions)


def test_centavos_exact_and_float_rejected():
    assert sum_parcels([{"label": "a", "value": "R$ 0,10"}, {"label": "b", "value": "R$ 0,20"}]).result == "0.30"
    with pytest.raises(TypeError):
        sum_parcels([{"label": "a", "value": 0.1}])
    with pytest.raises(ValueError):
        percent_of_base("base futura indeterminada", "15")


def test_honorarios_on_determined_base():
    record = percent_of_base(Decimal("401958.20"), Decimal("15"))
    assert record.result == "60293.73"
