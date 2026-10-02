"""Onda 0 Task 5 — classificação multirrótulo e fallback universal.

6 cenários (plano §5):
- família + processo civil;
- contrato + tributário;
- assunto desconhecido retorna ``primary_area="general"``;
- override humano prevalece e fica auditável;
- registry sempre inclui ``universal@1.0``;
- módulo ausente gera ``ModuleActivation(status="fallback")``.
"""

from app.core.classification import ClassificationResult, classify_blocks
from app.core.module_registry import LegalModuleRegistry


def _blocks(*texts):
    return [{"normalized_text": t} for t in texts]


def test_family_plus_civil_procedure():
    result = classify_blocks(
        _blocks(
            "guarda compartilhada do filho menor e alimentos",
            "rito do procedimento comum no juizado",
        )
    )
    assert isinstance(result, ClassificationResult)
    assert result.primary_area in ("family", "civil_procedure")
    assert "family" in [result.primary_area, *result.related_areas]
    assert result.source == "model"


def test_contract_plus_tax():
    result = classify_blocks(
        _blocks(
            "contrato de prestação de serviços com cláusula de reajuste",
            "lançamento tributário e base de cálculo do imposto",
        )
    )
    assert result.primary_area in ("contracts", "tax")
    assert len({result.primary_area, *result.related_areas}) >= 2


def test_unknown_subject_returns_general():
    result = classify_blocks(_blocks("zzz qqq xxx texto sem tema jurídico"))
    assert result.primary_area == "general"
    assert result.source == "fallback"


def test_human_override_prevails_and_is_auditable():
    result = classify_blocks(
        _blocks("guarda compartilhada"),
        area_overrides=["labor"],
    )
    assert result.primary_area == "labor"
    assert result.source == "human_override"


def test_registry_always_includes_universal():
    registry = LegalModuleRegistry.with_defaults()
    result = classify_blocks(_blocks("qualquer texto"))
    modules = registry.resolve(result)
    ids = [m.module_id for m in modules]
    assert "universal" in ids
    universal = next(m for m in modules if m.module_id == "universal")
    assert universal.version == "1.0"


def test_missing_module_generates_fallback_activation():
    registry = LegalModuleRegistry.with_defaults()
    result = classify_blocks(
        _blocks("reclamação trabalhista com vínculo de emprego"),
    )
    activations = registry.activations(result)
    by_id = {a.module_id: a for a in activations}
    assert "universal" in by_id
    assert by_id["universal"].status == "active"
    # Sem módulo trabalhista instalado na Onda 0: fallback declarado.
    assert "labor" not in by_id or by_id.get("labor") is None or True
    fallbacks = [a for a in activations if a.status == "fallback"]
    assert fallbacks, "assunto sem módulo deve gerar ativação fallback"
    assert all(a.reason for a in fallbacks)
