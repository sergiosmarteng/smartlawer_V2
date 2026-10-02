"""Onda 0 Task 6 — reconciliação global (parte 2)."""

from app.core.reconciler import reconcile_extractions


def _extraction(claims=(), facts=(), batch_index=0):
    return {
        "batch_index": batch_index,
        "claims": list(claims),
        "facts": list(facts),
        "evidence": [],
        "legal_references": [],
        "errors": [],
    }


def test_repeated_claim_unites_occurrences_and_sources():
    data = reconcile_extractions([
        _extraction(claims=[
            {"id": "c1", "original_number": "5", "title": "Reparação",
             "amount": "215760.00", "source_refs": ["b1"]},
        ]),
        _extraction(claims=[
            {"id": "c1b", "original_number": "5", "title": "Reparação material",
             "amount": "215760.00", "source_refs": ["b2"]},
        ], batch_index=1),
    ])
    assert len(data["claims"]) == 1
    assert sorted(data["claims"][0]["source_refs"]) == ["b1", "b2"]
    assert data["claims"][0]["occurrences"] == 2


def test_divergent_values_become_controversy_not_overwrite():
    data = reconcile_extractions([
        _extraction(claims=[
            {"id": "c1", "original_number": "5", "title": "Reparação",
             "amount": "100.00", "source_refs": ["b1"]},
            {"id": "c2", "original_number": "5", "title": "Reparação",
             "amount": "200.00", "source_refs": ["b2"]},
        ]),
    ])
    assert len(data["claims"]) == 1
    assert data["controversies"], "valores divergentes geram controvérsia"
    assert any("100.00" in str(c) and "200.00" in str(c) for c in data["controversies"])


def test_same_text_different_authors_stay_separate():
    data = reconcile_extractions([
        _extraction(facts=[
            {"id": "f1", "statement": "Renda de R$ 10.000",
             "asserted_by": "parte-A", "source_refs": ["b1"]},
            {"id": "f2", "statement": "Renda de R$ 10.000",
             "asserted_by": "parte-B", "source_refs": ["b2"]},
        ]),
    ])
    assert len(data["facts"]) == 2


def test_overlapping_batch_does_not_duplicate():
    data = reconcile_extractions([
        _extraction(claims=[
            {"id": "c1", "original_number": "1", "title": "Guarda",
             "source_refs": ["b1"]},
        ]),
        _extraction(claims=[
            {"id": "c1", "original_number": "1", "title": "Guarda",
             "source_refs": ["b1"]},
        ], batch_index=1),
    ])
    assert len(data["claims"]) == 1
    assert data["claims"][0]["source_refs"] == ["b1"]
