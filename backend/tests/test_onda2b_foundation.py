"""Onda 2B fundação — áreas administrative/real_estate e flags (spec §5–§7)."""

from app.core.classification import classify_blocks
from app.core.config import settings


def test_tax_areas_classify():
    auto = classify_blocks([{"normalized_text": "auto de infração de ICMS com ente estadual"}])
    assert "tax" in [auto.primary_area, *auto.related_areas]


def test_administrative_area_classifies():
    edital = classify_blocks([{"normalized_text": "edital de licitação e contrato administrativo"}])
    assert "administrative" in [edital.primary_area, *edital.related_areas]


def test_real_estate_area_classifies():
    matricula = classify_blocks([{"normalized_text": "matrícula do imóvel e escritura"}])
    assert "real_estate" in [matricula.primary_area, *matricula.related_areas]


def test_onda2b_flags_exist_and_default_off():
    assert settings.DOSSIER_MODULE_TAX is False
    assert settings.DOSSIER_MODULE_ADMINISTRATIVE is False
    assert settings.DOSSIER_MODULE_REAL_ESTATE is False
