"""Onda 0 Task 8 — análise jurídica universal bilateral."""

from datetime import date

import pytest

from app.core.universal_legal_analyzer import (
    UniversalAnalysisError,
    analyze_universal_case,
)


def _data():
    return {
        "claims": [
            {"id": "claim-1", "title": "Guarda", "source_refs": ["src-1"]},
        ],
        "facts": [
            {"id": "f1", "statement": "Genitores separados",
             "asserted_by": "parte-A", "source_refs": ["src-1"]},
            {"id": "f2", "statement": "Filho menor",
             "asserted_by": "parte-A", "source_refs": ["src-1"]},
        ],
        "controversies": [],
        "evidence": [
            {"id": "ev1", "presence_status": "examined", "location_refs": ["src-1"]},
        ],
        "legal_references": [
            {"id": "lr1", "literal_citation": "CC art. 1.584"},
        ],
        "sources": [{"id": "src-1"}],
    }


class _Provider:
    def __init__(self, payload):
        self._payload = payload

    def analyze(self, payload: dict):
        assert payload["represented_side"] in (
            "claimant", "respondent", "third_party", "neutral")
        return self._payload


def _ok_payload():
    return {
        "procedural_issues": [
            {"id": "pi1", "issue": "Competência", "conclusion": "Foro do domicílio",
             "source_refs": ["src-1"]},
        ],
        "theses": [
            {"id": "t1", "represented_side": "claimant", "issue": "Guarda",
             "conclusion": "Compartilhada", "factual_premises": ["f1"],
             "legal_premises": ["lr1"], "supporting_refs": ["src-1"],
             "adverse_refs": []},
            {"id": "t2", "represented_side": "respondent", "issue": "Guarda",
             "conclusion": "Unilateral subsidiária", "factual_premises": ["f2"],
             "legal_premises": ["lr1"], "supporting_refs": [],
             "adverse_refs": ["src-1"]},
        ],
        "risks": [
            {"id": "r1", "issue": "Distância", "impact": "Execução difícil",
             "supporting_refs": ["src-1"]},
        ],
        "actions": [
            {"id": "a1", "description": "Requerer estudo social", "priority": "high"},
        ],
        "questions": [
            {"id": "q1", "question": "Há acordo possível?"},
        ],
        "limitations": [],
    }


def test_respondent_side_still_produces_adverse_elements():
    out = analyze_universal_case(
        _data(), modules=[], represented_side="respondent",
        objective=None, reference_date=date(2026, 10, 2),
        provider=_Provider(_ok_payload()),
    )
    sides = {t["represented_side"] for t in out["theses"]}
    assert "respondent" in sides and "claimant" in sides


def test_thesis_references_existing_premises_and_sources():
    out = analyze_universal_case(
        _data(), modules=[], represented_side="claimant",
        objective=None, reference_date=date(2026, 10, 2),
        provider=_Provider(_ok_payload()),
    )
    fact_ids = {f["id"] for f in _data()["facts"]}
    source_ids = {s["id"] for s in _data()["sources"]}
    for thesis in out["theses"]:
        assert set(thesis["factual_premises"]) <= fact_ids
        for ref in [*thesis["supporting_refs"], *thesis["adverse_refs"]]:
            assert ref in source_ids


def test_unknown_subject_returns_universal_with_limitation():
    out = analyze_universal_case(
        {"claims": [], "facts": [], "controversies": [], "evidence": [],
         "legal_references": [], "sources": []},
        modules=[], represented_side="neutral",
        objective=None, reference_date=date(2026, 10, 2),
        provider=_Provider({"procedural_issues": [], "theses": [], "risks": [],
                            "actions": [], "questions": [], "limitations": []}),
    )
    codes = [lim["code"] for lim in out["limitations"]]
    assert "SPECIALIZATION_UNAVAILABLE" in codes


def test_missing_dates_block_prescription_but_create_action():
    payload = _ok_payload()
    payload["theses"] = [
        {"id": "t1", "represented_side": "claimant", "issue": "Guarda",
         "conclusion": "Compartilhada", "factual_premises": ["f1"],
         "legal_premises": ["lr1"], "supporting_refs": ["src-1"],
         "adverse_refs": []},
    ]
    payload["actions"] = []
    payload["questions"] = []
    out = analyze_universal_case(
        _data(), modules=[], represented_side="claimant",
        objective=None, reference_date=None,
        provider=_Provider(payload),
    )
    assert any("prescri" in a["description"].lower() or "data" in a["description"].lower()
               for a in out["actions"])
    assert not any("prescrito" in (t.get("conclusion") or "").lower()
                   for t in out["theses"])


def test_empty_or_generic_provider_response_rejected():
    with pytest.raises(UniversalAnalysisError):
        analyze_universal_case(
            _data(), modules=[], represented_side="claimant",
            objective=None, reference_date=date(2026, 10, 2),
            provider=_Provider({"procedural_issues": [], "theses": [],
                                "risks": [], "actions": [], "questions": [],
                                "limitations": []}),
        )
    with pytest.raises(UniversalAnalysisError):
        analyze_universal_case(
            _data(), modules=[], represented_side="claimant",
            objective=None, reference_date=date(2026, 10, 2),
            provider=_Provider({
                "procedural_issues": [], "risks": [], "actions": [],
                "questions": [], "limitations": [],
                "theses": [{
                    "id": "tg", "represented_side": "claimant",
                    "issue": "x",
                    "conclusion": "Exigir comprovacao documental integral dos fatos "
                                  "constitutivos alegados pelo autor.",
                    "factual_premises": [], "legal_premises": [],
                    "supporting_refs": [], "adverse_refs": []}],
            }),
        )
