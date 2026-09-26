"""V2 T14 — corpus, gate real e comparação (aceite do plano)."""

from evals.corpus_v2 import AREAS, build_corpus, corpus_manifest
from evals.run_benchmark import evaluate_case, render_report, run_benchmark


def test_corpus_has_30_synthetic_cases_split_by_case():
    corpus = build_corpus()
    assert len(corpus) == 30
    manifest = corpus_manifest(corpus)
    assert manifest["total"] == 30
    assert set(manifest["by_area"]) == set(AREAS)
    assert all(v == 5 for v in manifest["by_area"].values())
    assert set(manifest["by_split"]) == {"dev", "val", "holdout"}
    # Determinístico: mesma seed, mesmo corpus.
    again = build_corpus()
    assert [c["text"] for c in again] == [c["text"] for c in corpus]
    # Sem PII em nenhum caso.
    import re

    pii = re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b|[\w.-]+@[\w-]+\.[\w.]+")
    assert not any(pii.search(c["text"]) for c in corpus)


def test_single_case_metrics():
    corpus = build_corpus()
    result = evaluate_case(corpus[0])
    assert result["claims_recall"] == 1.0
    assert result["values_exact"] is True
    assert result["refs_violations"] == 0
    assert result["no_pii"] and result["no_injection_leak"]
    assert result["cost"] == "unavailable"


def test_full_benchmark_gates_and_report():
    summary = run_benchmark(build_corpus())
    assert summary["cases"] == 30
    assert summary["claims_recall"] >= 0.98
    assert summary["gates"]["values_exact_all"]
    assert summary["gates"]["traps_detected_all"]
    assert summary["gates"]["v2_blocks_what_v1_passes"]
    assert summary["comparison_v1_v2"]["demo_ghost_source"]["v2"] == "partial"
    assert summary["pending_human"]  # piloto bloqueado até revisão humana
    report = render_report(summary)
    assert "recall de pedidos: 1.0" in report
    assert "- [x] values_exact_all" in report
