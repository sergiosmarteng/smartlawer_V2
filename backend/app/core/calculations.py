"""Serviço de cálculo determinístico (V2 T09, §11).

O modelo identifica hipóteses; ESTE serviço executa. Decimal sempre,
arredondamento explícito, fórmulas versionadas, memória de cálculo
por cenário. Nunca executa código livre gerado pela IA. Nunca soma
rubrica possivelmente sobreposta sem marcação explícita.
"""

import logging
import re
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

logger = logging.getLogger(__name__)

ROUNDING = ROUND_HALF_UP
ROUNDING_NAME = "half_up_centavos"
CURRENCY = "BRL"

FORMULA_SUM_PARCELS = ("sum_parcels", "1.0")
FORMULA_PENSION_PROJECTION = ("monthly_pension_projection", "1.0")
FORMULA_DIFFERENCE = ("salary_difference", "1.0")
FORMULA_PERCENT = ("percent_of_base", "1.0")


@dataclass
class ParsedMoney:
    literal: str
    value: Decimal | None  # None = ambíguo ("a liquidar"); nunca float
    currency: str = CURRENCY


@dataclass
class CalcInput:
    label: str
    value: Decimal | str  # str = dependente (ex.: "pericia:percentual")
    source_ref: str | None = None


@dataclass
class CalculationRecord:
    formula: str
    formula_version: str
    inputs: list[CalcInput]
    assumptions: list[str] = field(default_factory=list)
    result: str | None = None
    rounding: str = ROUNDING_NAME
    scenario: str | None = None
    notes: list[str] = field(default_factory=list)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUNDING)


def parse_br_money(literal: str) -> ParsedMoney:
    """'R$ 215.760,20' → Decimal('215760.20'); ambíguo → value None."""
    text = (literal or "").strip()
    match = re.search(r"(\d[\d.]*,\d{2})", text)
    if not match:
        return ParsedMoney(literal=literal, value=None)
    try:
        normalized = match.group(1).replace(".", "").replace(",", ".")
        return ParsedMoney(literal=literal, value=Decimal(normalized))
    except (InvalidOperation, ValueError):
        return ParsedMoney(literal=literal, value=None)


def _require_decimal(value, label: str) -> Decimal:
    if isinstance(value, float):
        raise TypeError(f"{label}: float proibido para dinheiro (§8.4)")
    if isinstance(value, Decimal):
        return value
    if isinstance(value, str):
        parsed = parse_br_money(value)
        if parsed.value is None:
            raise ValueError(f"{label}: valor ambíguo {value!r}")
        return parsed.value
    raise TypeError(f"{label}: tipo inválido {type(value).__name__}")


def sum_parcels(
    items: list[dict], *, scenario: str | None = None
) -> CalculationRecord:
    """Soma parcelas cumulativas; sobrepostas vão para nota, não para soma.

    item: {label, value, cumulative=True, source_ref?}.
    """
    formula, version = FORMULA_SUM_PARCELS
    total = Decimal("0.00")
    inputs: list[CalcInput] = []
    notes: list[str] = []
    for item in items:
        value = _require_decimal(item["value"], item.get("label", "?"))
        entry = CalcInput(
            label=item.get("label", "?"), value=value,
            source_ref=item.get("source_ref"),
        )
        inputs.append(entry)
        if item.get("cumulative", True):
            total += value
        else:
            notes.append(
                f"'{entry.label}' não somado automaticamente "
                "(cumulação incerta — hipótese a revisar)."
            )
    return CalculationRecord(
        formula=formula, formula_version=version, inputs=inputs,
        result=str(_quantize(total)), scenario=scenario, notes=notes,
    )


def pension_projection(
    monthly: Decimal | str,
    years: int,
    *,
    scenario: str | None = None,
    inferred_chain: bool = False,
    depends_on_pericia: bool = False,
) -> CalculationRecord:
    """Pensão mensal × 12 × anos. Encadeamento reconstruído = inferência."""
    formula, version = FORMULA_PENSION_PROJECTION
    monthly_dec = _require_decimal(monthly, "mensal")
    assumptions = ["13º/ferias não incluídos salvo previsão expressa."]
    if inferred_chain:
        assumptions.append(
            "Encadeamento da fórmula reconstruído aritmeticamente; "
            "solicitar confirmação da memória de cálculo da peça."
        )
    if depends_on_pericia:
        assumptions.append("Parâmetro depende de perícia; resultado condicionado.")
    total = _quantize(monthly_dec * Decimal(12) * Decimal(int(years)))
    return CalculationRecord(
        formula=formula, formula_version=version,
        inputs=[
            CalcInput("mensal", monthly_dec),
            CalcInput("anos", Decimal(int(years))),
        ],
        assumptions=assumptions,
        result=str(total), scenario=scenario,
    )


def difference(
    minuend: Decimal | str, subtrahend: Decimal | str, *, label: str = "diferenca"
) -> CalculationRecord:
    """Diferença entre valores narrados (não comprova recebimento)."""
    formula, version = FORMULA_DIFFERENCE
    first = _require_decimal(minuend, "minuendo")
    second = _require_decimal(subtrahend, "subtraendo")
    return CalculationRecord(
        formula=formula, formula_version=version,
        inputs=[CalcInput("minuendo", first), CalcInput("subtraendo", second)],
        assumptions=["Relação entre valores narrados; não comprova recebimento."],
        result=str(_quantize(first - second)),
    )


def percent_of_base(
    base: Decimal | str, percent: Decimal | str, *, scenario: str | None = None
) -> CalculationRecord:
    """Percentual sobre base; base indeterminada → erro explícito, nunca chute."""
    formula, version = FORMULA_PERCENT
    base_dec = _require_decimal(base, "base")
    pct = _require_decimal(percent, "percentual")
    return CalculationRecord(
        formula=formula, formula_version=version,
        inputs=[CalcInput("base", base_dec), CalcInput("percentual", pct)],
        result=str(_quantize(base_dec * pct / Decimal(100))),
        scenario=scenario,
    )
