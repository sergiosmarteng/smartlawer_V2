"""Onda 0 Task 10 — composição determinística do artefato."""

from app.core.report_composer import CompositionInputs, compose_artifact


def _inputs(**overrides):
    base = {
        "run_id": "run-1",
        "case_id": "case-1",
        "coverage": {"pages_total": 2, "pages_extracted": 2},
        "reconciled": {
            "claims": [{"id": "claim-1", "title": "Guarda",
                        "source_refs": ["src-1"]}],
            "facts": [{"id": "f1", "statement": "X",
                       "asserted_by": "parte-A",
                       "epistemic_status": "documented",
                       "source_refs": ["src-1"]}],
            "controversies": [],
            "evidence": [],
            "legal_references": [],
        },
        "analysis": {"procedural_issues": [], "theses": [], "risks": [],
                     "actions": [], "questions": [], "limitations": []},
        "research": {"results": [], "partial": False},
        "calculations": [],
        "visuals": [],
        "sources": [{"id": "src-1", "page_number": 1}],
    }
    base.update(overrides)
    return CompositionInputs(**base)


def test_composer_reorganizes_without_free_generation():
    first = compose_artifact(_inputs())
    second = compose_artifact(_inputs())
    assert first.schema_version == "3.0"
    assert first.content_hash() == second.content_hash()
    assert first.claims and first.facts
    assert first.executive_summary is not None
    assert "claim-1" in first.executive_summary.main_claims


def test_composer_summary_is_rule_based():
    artifact = compose_artifact(_inputs())
    assert artifact.executive_summary.narrative
    assert "f1" in artifact.executive_summary.key_facts
