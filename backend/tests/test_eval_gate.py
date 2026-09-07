"""Tests for A5: eval gate sensitivity + scorer units (Onda A - RAG)."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "evals"))

from app.core.eval_scoring import (
    GATE_THRESHOLD,
    gate_passed,
    has_citation,
    mean_faithfulness,
    needs_citation,
    score_item,
    split_sentences,
)
from run_gate import ABSTAIN_ANSWER, evaluate_all, retrieve, student_answer

EVALS_DIR = Path(__file__).resolve().parents[1] / "evals"


@pytest.fixture()
def golden():
    return json.loads((EVALS_DIR / "golden_legal.json").read_text(encoding="utf-8"))[
        "items"
    ]


@pytest.fixture()
def corpus():
    return json.loads((EVALS_DIR / "corpus_fixture.json").read_text(encoding="utf-8"))[
        "chunks"
    ]


def test_golden_set_has_30_items(golden):
    assert len(golden) == 30
    assert sum(1 for i in golden if i.get("abstain_expected")) == 6
    assert all(i.get("expected_terms") for i in golden)


def test_gate_passes_with_grounded_student(golden, corpus):
    scores = evaluate_all(golden, corpus)
    assert gate_passed(scores, GATE_THRESHOLD)
    assert mean_faithfulness(scores) >= GATE_THRESHOLD


def test_gate_fails_when_citations_stripped(golden, corpus):
    def sloppy_student(question, contexts):
        answer, _citations = student_answer(question, contexts)
        if not contexts:
            return answer, []
        # Claim everything, cite nothing.
        import re

        return re.sub(r"\s*\[\d+\]", "", answer), []

    scores = evaluate_all(golden, corpus, student=sloppy_student)
    assert not gate_passed(scores, GATE_THRESHOLD)


def test_gate_fails_when_student_never_abstains(golden, corpus):
    def reckless_student(question, contexts):
        if not contexts:
            return "O prazo é de 15 dias conforme o artigo 42 do CDC.", []
        return student_answer(question, contexts)

    scores = evaluate_all(golden, corpus, student=reckless_student)
    assert not gate_passed(scores, GATE_THRESHOLD)


def test_abstain_items_score_perfect_when_abstaining(golden, corpus):
    scores = evaluate_all(golden, corpus)
    abstain_scores = [s for s in scores if s["id"].startswith("a")]
    assert len(abstain_scores) == 6
    assert all(s["faithfulness"] == 1.0 and s["abstained"] for s in abstain_scores)


def test_hallucination_on_empty_context_scores_zero():
    item = {"id": "x", "expected_terms": ["prazo"]}
    result = score_item(item, "O prazo é de 15 dias [1].", [{"ref": "[1]"}], [])
    assert result["faithfulness"] == 0.0


def test_correct_abstention_scores_one():
    item = {"id": "x", "expected_terms": ["prazo"]}
    result = score_item(item, ABSTAIN_ANSWER, [], ["texto irrelevante"])
    assert result["faithfulness"] == 1.0


def test_uncited_claims_score_zero():
    item = {"id": "x", "expected_terms": ["prazo"]}
    result = score_item(
        item,
        "O prazo para contestação é de 15 dias corridos.",
        [],
        ["O prazo para contestação é de 15 dias."],
    )
    assert result["faithfulness"] == 0.0


def test_abbreviations_do_not_split_sentences():
    sentences = split_sentences("Art. 1 O contrato vale. Parágrafo único.")
    assert sentences[0].startswith("Art. 1")
    assert any("Parágrafo único" in s for s in sentences)


def test_citation_detection():
    assert has_citation("O prazo é de 15 dias [1].")
    assert not has_citation("O prazo é de 15 dias.")
    assert not needs_citation("Sim.")
    assert needs_citation(
        "O prazo para contestação é de quinze dias corridos contados da juntada."
    )
