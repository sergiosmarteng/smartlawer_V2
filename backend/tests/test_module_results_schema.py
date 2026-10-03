"""Onda 1 fundação — envelope module_results (spec §2).

- Artefato sem ``module_results`` continua válido (extensão opcional).
- Envelope válido com refs resolvidas valida sem violações.
- Ref fantasma em ``supporting_source_refs`` gera violação do módulo.
- Payload legado (pré-extensão) valida sem migração.
"""

from app.core.schemas_v3 import ArtifactContentV3, validate_artifact_v3


def _base(**overrides):
    payload = {
        "schema_version": "3.0",
        "coverage": {"pages_total": 1, "pages_extracted": 1},
        "section_states": {},
        "claims": [],
        "facts": [],
        "evidence": [],
        "sources": [{"id": "src-1", "page_number": 1}],
    }
    payload.update(overrides)
    return payload


def test_artifact_without_module_results_stays_valid():
    artifact = ArtifactContentV3.model_validate(_base())
    assert artifact.module_results == {}
    assert validate_artifact_v3(artifact) == []


def test_valid_module_envelope_passes():
    artifact = ArtifactContentV3.model_validate(_base(module_results={
        "family": {
            "module_id": "family",
            "module_version": "1.0.0",
            "status": "complete",
            "reason": "Matriz aplicável examinada",
            "issue_assessments": [{
                "issue_key": "child_support.need_capacity",
                "status": "partial",
                "conclusion": "Necessidade alegada; capacidade ainda não documentada",
                "factual_refs": ["f1"],
                "supporting_source_refs": ["src-1"],
                "adverse_source_refs": [],
                "missing_inputs": ["comprovante de renda atual"],
                "related_claim_ids": ["claim-1"],
                "action_ids": ["action-1"],
            }],
            "calculation_ids": [],
            "limitations": [],
        },
    }))
    assert validate_artifact_v3(artifact) == []


def test_ghost_source_ref_in_module_is_violation():
    artifact = ArtifactContentV3.model_validate(_base(module_results={
        "family": {
            "module_id": "family",
            "module_version": "1.0.0",
            "status": "complete",
            "reason": "x",
            "issue_assessments": [{
                "issue_key": "k",
                "status": "complete",
                "conclusion": "c",
                "supporting_source_refs": ["src-ghost"],
            }],
        },
    }))
    errors = validate_artifact_v3(artifact)
    assert any("family" in e and "src-ghost" in e for e in errors)


def test_legacy_payload_without_module_results_key():
    raw = _base()
    del raw["sources"]
    raw["facts"] = []
    artifact = ArtifactContentV3.model_validate(raw)
    assert artifact.module_results == {}
    assert validate_artifact_v3(artifact) == []
