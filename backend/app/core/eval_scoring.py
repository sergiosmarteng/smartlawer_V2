"""Deterministic RAG quality scorer (no LLM judge required).

Metrics per golden item:
- ``context_recall``: share of expected terms present in retrieved contexts.
- ``answer_relevancy``: share of expected terms present in the answer.
- ``faithfulness``: share of claim sentences carrying a ``[N]`` citation;
  when contexts lack the expected terms, the only faithful output is an
  explicit abstention ("não encontrei fundamento").

This is a structural gate, not a semantic judge: it catches regressions
in citation plumbing, retrieval wiring and abstention behavior. An
LLM-as-a-judge upgrade can replace :func:`score_item` internals later
without changing the gate contract (mean faithfulness >= threshold).
"""

import re

ABSTAIN_MARKERS = ("nao encontrei fundamento", "não encontrei fundamento")
CITATION_RE = re.compile(r"\[\d+\]")
GATE_THRESHOLD = 0.85


def _normalize(text: str) -> str:
    return (text or "").lower()


def split_sentences(text: str) -> list[str]:
    protected = _protect_abbreviations((text or "").strip())
    parts = re.split(r"(?<=[.!?])\s+", protected)
    sentences = [_restore_abbreviations(p).strip() for p in parts if p.strip()]
    # A lone "[N]" orphaned by splitting belongs to the previous sentence.
    merged: list[str] = []
    for sentence in sentences:
        if re.fullmatch(r"\[\d+\]", sentence) and merged:
            merged[-1] = f"{merged[-1]} {sentence}"
        else:
            merged.append(sentence)
    return merged


_ABBREVIATIONS = (
    "Art.", "Arts.", "§", "nº", "n.", "ex.", "p. ex.", "v.g.", "fls.",
    "cf.", "Dr.", "Dra.", "Sr.", "Sra.", "Min.", "Rel.", "inc.", "al.",
)


def _protect_abbreviations(text: str) -> str:
    for abbr in _ABBREVIATIONS:
        text = text.replace(abbr, abbr.replace(".", "<DOT>"))
    return text


def _restore_abbreviations(text: str) -> str:
    return text.replace("<DOT>", ".")


def needs_citation(sentence: str) -> bool:
    """Long sentences state claims; short/fallback ones do not."""
    lowered = _normalize(sentence)
    if any(marker in lowered for marker in ABSTAIN_MARKERS):
        return False
    return len(sentence) >= 40


def has_citation(sentence: str) -> bool:
    return CITATION_RE.search(sentence) is not None


def term_hit(term: str, text: str) -> bool:
    return _normalize(term) in _normalize(text)


def score_item(item: dict, answer: str, citations: list, contexts: list[str]) -> dict:
    """Score one golden item. Returns metric dict with ``faithfulness``."""
    expected = item.get("expected_terms", [])
    contexts_text = "\n".join(contexts)
    recall = (
        sum(1 for t in expected if term_hit(t, contexts_text)) / len(expected)
        if expected
        else 1.0
    )
    relevancy = (
        sum(1 for t in expected if term_hit(t, answer)) / len(expected)
        if expected
        else 1.0
    )

    abstained = any(marker in _normalize(answer) for marker in ABSTAIN_MARKERS)
    if recall == 0:
        # Nothing retrieved: abstention is correct, anything else is hallucination.
        faithfulness = 1.0 if abstained else 0.0
    else:
        sentences = split_sentences(answer)
        needing = [s for s in sentences if needs_citation(s)]
        if not needing:
            faithfulness = 1.0 if citations else 0.0
        else:
            cited = sum(1 for s in needing if has_citation(s))
            faithfulness = cited / len(needing)
            if not citations:
                faithfulness = 0.0

    return {
        "id": item.get("id"),
        "faithfulness": round(faithfulness, 3),
        "answer_relevancy": round(relevancy, 3),
        "context_recall": round(recall, 3),
        "cited": bool(citations),
        "abstained": abstained,
    }


def gate_passed(scores: list[dict], threshold: float = GATE_THRESHOLD) -> bool:
    """CI gate: mean faithfulness must reach *threshold*."""
    if not scores:
        return False
    mean_faithfulness = sum(s["faithfulness"] for s in scores) / len(scores)
    return mean_faithfulness >= threshold


def mean_faithfulness(scores: list[dict]) -> float:
    if not scores:
        return 0.0
    return sum(s["faithfulness"] for s in scores) / len(scores)
