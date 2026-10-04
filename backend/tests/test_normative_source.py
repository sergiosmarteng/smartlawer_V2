"""Onda 2A fundação — fonte normativa verificável (spec §8)."""

from datetime import date


def _source(**overrides):
    base = {
        "instrument_id": "cc",
        "provision_id": "art-1584",
        "jurisdiction": "federal",
        "effective_from": "2003-01-11",
        "effective_to": None,
        "retrieved_at": "2026-10-04",
        "url": "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm",
        "hash": None,
        "version": None,
        "excerpt": "Art. 1.584. ...",
        "available": True,
    }
    base.update(overrides)
    return base


def test_normative_source_requires_fields():
    from app.core.normative_source import NormativeSource

    full = NormativeSource(**_source())
    assert full.instrument_id == "cc"
    assert full.jurisdiction == "federal"


def test_posterior_source_as_historic_grounds_is_violation():
    from app.core.normative_source import validate_normative_source

    violations = validate_normative_source(
        _source(effective_from="2024-01-01"),
        reference_date=date(2020, 5, 1),
    )
    assert any("posterior" in v.lower() or "vigência" in v.lower() for v in violations)


def test_ambiguous_or_unretrieved_source_is_violation():
    from app.core.normative_source import validate_normative_source

    assert validate_normative_source(_source(url="", available=False))
    assert validate_normative_source(_source(excerpt=""))
    assert validate_normative_source(_source(retrieved_at=""))


def test_valid_source_passes():
    from app.core.normative_source import validate_normative_source

    assert validate_normative_source(_source(), reference_date=date(2026, 10, 4)) == []


def test_classify_corporate_and_contracts():
    from app.core.classification import classify_blocks

    corporate = classify_blocks([{"normalized_text": "contrato social com sócios e quotas na assembleia"}])
    assert "corporate" in [corporate.primary_area, *corporate.related_areas]
    contracts = classify_blocks([{"normalized_text": "cláusula de reajuste e multa no aditivo"}])
    assert "contracts" in [contracts.primary_area, *contracts.related_areas]
