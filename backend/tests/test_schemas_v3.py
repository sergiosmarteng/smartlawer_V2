"""Onda 0 Task 1 — schema 3.0 + invariantes (V3).

Os três testes abaixo são o contrato do plano da Onda 0 §1:
- test_v3_rejects_empty_section_without_reason: SectionState vazia é inválida.
- test_v3_requires_source_or_limitation_for_material_fact: fato material sem fonte = erro.
- test_v3_case_fixture_contains_more_than_claims: fixture real exercita fatos/provas, não só pedidos.
"""

import json
from pathlib import Path

import pytest


def _minimal_artifact(**overrides):
    """Constrói um ArtifactContentV3 mínimo válido para os testes falharem."""
    from app.core.schemas_v3 import ArtifactContentV3

    payload = {
        "schema_version": "3.0",
        "run_id": "run-test",
        "case_id": None,
        "status": "partial",
        "review_status": "pending",
        "scope": {"document_ids": ["doc-1"]},
        "module_activations": [],
        "coverage": {
            "pages_total": 1,
            "pages_extracted": 1,
            "unprocessed_block_ids": [],
            "explicit_claims_expected": None,
            "explicit_claims_found": 0,
        },
        "section_states": {},
        "executive_summary": None,
        "parties": [],
        "events": [],
        "claims": [],
        "facts": [],
        "controversies": [],
        "evidence": [],
        "visuals": [],
        "legal_references": [],
        "procedural_issues": [],
        "theses": [],
        "calculations": [],
        "risks": [],
        "action_plan": [],
        "client_questions": [],
        "sources": [],
        "limitations": [],
    }
    payload.update(overrides)
    return ArtifactContentV3.model_validate(payload)


def _load_fixture(name: str) -> dict:
    path = Path(__file__).parent / "fixtures" / name
    return json.loads(path.read_text(encoding="utf-8"))


def test_v3_rejects_empty_section_without_reason():
    """SectionState sem reason é inválida (spec universal §6.4).

    Proteção em duas camadas:
    1) Pydantic bloqueia ``reason == ''``/whitespace em construção
       (``min_length=1`` + ``field_validator``).
    2) ``validate_artifact_v3`` também detecta ``reason`` em branco,
       útil quando o artefato vem serializado por outra fonte.
    """
    import pytest
    from pydantic import ValidationError

    from app.core.schemas_v3 import SectionState, validate_artifact_v3

    # Camada 1: construção direta com reason vazio/white-space é recusada.
    with pytest.raises(ValidationError):
        SectionState(status="complete", reason="")

    with pytest.raises(ValidationError):
        SectionState(status="complete", reason="   ")

    # Camada 2: validate_artifact_v3 detecta artefato com reason em branco
    # (simula artefato vindo de JSON sem validação prévia).
    from app.core.schemas_v3 import ArtifactContentV3, SectionState as SS

    # Construímos manualmente o dict para driblar a validação do SectionState
    # (simula artefato serializado por fonte externa não validada).
    artifact_dict = {
        "schema_version": "3.0",
        "section_states": {
            "facts": {"status": "complete", "reason": "", "coverage": {"items_expected": None, "items_found": 0, "items_verified": 0}, "pending_actions": []}
        },
    }
    # Pydantic agora rejeita aqui também (camada 1) — então a checagem em
    # validate_artifact_v3 é redundante mas defensiva.
    try:
        artifact = ArtifactContentV3.model_validate(artifact_dict)
    except ValidationError:
        # Comportamento correto: Pydantic barra o payload mal formado.
        return

    errors = validate_artifact_v3(artifact)
    joined = " ".join(errors)
    assert "facts" in joined, f"esperava erro envolvendo 'facts', obtive: {errors}"


def test_v3_requires_source_or_limitation_for_material_fact():
    """Fato material sem source_refs E sem limitação é inválido (§5.1, §6.3.5)."""
    from app.core.schemas_v3 import validate_artifact_v3

    artifact = _minimal_artifact(
        facts=[
            {
                "id": "f1",
                "statement": "O autor firmou contrato em 2024",
                "asserted_by": "João Auto",
                "epistemic_status": "documented",
                "source_refs": [],
                "conflicts_with": [],
            }
        ]
    )
    errors = validate_artifact_v3(artifact)
    assert any("f1" in err for err in errors), f"esperava violação referenciando f1, obtive: {errors}"


def test_v3_case_fixture_contains_more_than_claims():
    """Fixture real exercita fatos, provas, visuais, fontes — não só pedidos (regressão defeito §3.1)."""
    from app.core.schemas_v3 import ArtifactContentV3

    artifact = ArtifactContentV3.model_validate(_load_fixture("family_case_v3.json"))
    assert artifact.claims, "fixture deve ter pedidos"
    assert artifact.facts, "fixture deve ter fatos (defeito original era fatos=[])"
    assert artifact.evidence, "fixture deve ter provas"
    assert artifact.sources, "fixture deve ter fontes resolvíveis"
    # facts não pode estar bloqueado (caso legítimo)
    assert "facts" in artifact.section_states
    assert artifact.section_states["facts"].status != "blocked"