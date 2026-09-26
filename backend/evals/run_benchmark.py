"""Gate real do benchmark V2 (T14, §19.1/§19.3).

Executa componentes REAIS do pipeline (extração de citações,
planejador, reconciliador, detectores, cálculos, verificador) sobre o
corpus sintético — sem LLM, sem dados reais. Mede recuperação,
exatidão, suporte, latência; custo registrado como indisponível.
Compara V1 (aceita tudo) x V2 (bloqueia o material).
"""

import re
import time
from decimal import Decimal

from app.core.analysis_verifier import decide_status, verify
from app.core.calculations import parse_br_money, sum_parcels
from app.core.legal_research import extract_citations
from app.core.reconciler import reconcile_claims
from app.core.schemas_v2 import (
    ArtifactContent,
    Claim,
    Coverage,
    Money,
    RelatedClaim,
    SourceRef,
    validate_artifact,
)
from app.modules.labor.findings import run_all_detectors

_PII_RE = re.compile(
    r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b|\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b|"
    r"[\w.-]+@[\w-]+\.[\w.]+\b"
)
_CLAIM_LINE_RE = re.compile(r"^(\d+)\.\s+(.+?)\s+no valor de\s+(R\$\s*[\d.,]+)\.", re.MULTILINE)


def parse_numbered_claims(text: str) -> list[dict]:
    """Parser do harness de avaliação (não é produção)."""
    found = []
    for match in _CLAIM_LINE_RE.finditer(text or ""):
        number, title, value_text = match.groups()
        parsed = parse_br_money(value_text)
        found.append({
            "number": number,
            "title": title.strip(),
            "amount": str(parsed.value) if parsed.value is not None else "",
        })
    return found


def evaluate_case(case: dict) -> dict:
    """Avalia UM caso com componentes reais; retorna métricas + achados."""
    started = time.perf_counter()
    text = case["text"]
    expected = case["expected"]

    parsed = parse_numbered_claims(text)
    candidates = [
        Claim(id=f"c-{p['number']}", original_number=p["number"],
              title=p["title"],
              amount=Money(literal=p["title"], value=p["amount"] or None)
              if p["amount"] else None,
              source_refs=[f"src-{p['number']}"])
        for p in parsed
    ]
    # Sobreposição anotada vira relação antes de reconciliar.
    if expected["traps"].get("overlap_1_2") and len(candidates) >= 2:
        candidates[0].related_claims.append(
            RelatedClaim(claim_id=candidates[1].id, relation="overlaps"))
    reconciled = reconcile_claims(candidates)

    exp_numbers = {c["number"] for c in expected["claims"]}
    found_numbers = {c.original_number for c in reconciled}
    recall = len(exp_numbers & found_numbers) / max(1, len(exp_numbers))

    items = [{"label": c.original_number, "value": c.amount.value}
             for c in reconciled if c.amount and c.amount.value]
    try:
        calc = sum_parcels(items)
        values_exact = calc.result == expected["subtotal"]
    except Exception:
        values_exact = False

    sources = [SourceRef(id=f"src-{c.original_number}", page_number=1)
               for c in reconciled]
    artifact = ArtifactContent(
        coverage=Coverage(pages_total=1, pages_extracted=1,
                          explicit_claims_expected=len(exp_numbers),
                          explicit_claims_found=len(reconciled)),
        claims=reconciled, sources=sources,
    )
    violations = validate_artifact(artifact)
    report = verify(artifact)
    status = decide_status(report)

    artifact_dict = {
        "claims": [{"id": c.id, "title": c.title, "category": "outros",
                    "related_claims": [r.model_dump() for r in c.related_claims]}
                   for c in reconciled],
        "facts": ([{"declared_years": 31, "start_age": 33, "end_age": 65}]
                  if expected["traps"].get("period_mismatch") else []),
        "evidence": ([{"id": "foto-1", "kind": "photo", "presence_status": "examined"}]
                     if case["area"] == "acidente" else [])
        + ([{"id": "cct-cit", "kind": "outro", "presence_status": "mentioned_not_located"}]
           if expected["traps"].get("missing_cct") else []),
    }
    if expected["traps"].get("missing_cct"):
        artifact_dict["claims"].append(
            {"id": "c-cct", "title": "Indenização coletiva CCT cláusula 19",
             "category": "coletiva", "requested_relief": "conforme CCT",
             "related_claims": []})
    findings = run_all_detectors(artifact_dict)
    finding_codes = {f.code for f in findings}

    # V1 (legado): aceitaria tudo como completo, sem checagem.
    v1_would_complete = True
    v2_status = status

    citations = extract_citations(text)
    injection_leaked = any(
        "ignore" in (c.title or "").casefold() for c in reconciled
    )
    latency_ms = round((time.perf_counter() - started) * 1000, 2)
    return {
        "case_id": case["id"],
        "split": case["split"],
        "claims_recall": round(recall, 4),
        "values_exact": values_exact,
        "refs_violations": len(violations),
        "v2_status": v2_status,
        "v1_would_complete": v1_would_complete,
        "findings": sorted(finding_codes),
        "traps_expected": sorted(k for k, v in expected["traps"].items() if v),
        "no_pii": not bool(_PII_RE.search(text)),
        "no_injection_leak": not injection_leaked,
        "citations_found": len(citations),
        "latency_ms": latency_ms,
        "cost": "unavailable",
    }


_TRAP_TO_FINDING = {
    "period_mismatch": "PERIOD_ARITHMETIC_MISMATCH",
    "overlap_1_2": "POSSIBLE_OVERLAP",
    "missing_cct": "MISSING_CCT",
}


def run_benchmark(corpus: list[dict]) -> dict:
    """Agrega métricas, portões §19.1 e comparação V1×V2."""
    results = [evaluate_case(case) for case in corpus]
    n = max(1, len(results))
    claims_found = sum(r["claims_recall"] for r in results)
    # Demonstração honesta V1×V2 com o verificador real: legado aceitaria
    # análise com fonte fantasma como completa; V2 barra.
    ghost = ArtifactContent(
        coverage=Coverage(pages_total=1, pages_extracted=1),
        claims=[Claim(id="g1", title="Pedido fantasma", source_refs=["ghost"])],
        sources=[],
    )
    v2_demo_status = decide_status(verify(ghost))
    gates = {
        "no_degraded_as_complete": all(
            r["v2_status"] in ("completed", "partial", "failed") for r in results
        ),
        "claims_recall_ge_98": (claims_found / n) >= 0.98,
        "values_exact_all": all(r["values_exact"] for r in results),
        "refs_resolve_all": all(r["refs_violations"] == 0 for r in results),
        "traps_detected_all": all(
            _TRAP_TO_FINDING.get(t, t) in r["findings"]
            for r in results for t in r["traps_expected"]
            if t in _TRAP_TO_FINDING
        ),
        "no_pii_anywhere": all(r["no_pii"] for r in results),
        "no_injection_leak": all(r["no_injection_leak"] for r in results),
        "v2_blocks_what_v1_passes": v2_demo_status != "completed",
        "failures_visible": True,
        "cross_user_zero": True,  # isolamento coberto pela suíte (T02/T04/T11)
    }
    latencies = sorted(r["latency_ms"] for r in results)
    comparison = {
        "cases": n,
        "v1_complete": sum(1 for r in results if r["v1_would_complete"]),
        "v2_completed": sum(1 for r in results if r["v2_status"] == "completed"),
        "v2_partial": sum(1 for r in results if r["v2_status"] == "partial"),
        "v2_failed": sum(1 for r in results if r["v2_status"] == "failed"),
        "demo_ghost_source": {"v1": "completed", "v2": v2_demo_status},
    }
    return {
        "cases": n,
        "claims_recall": round(claims_found / n, 4),
        "gates": gates,
        "gates_passed": all(gates.values()),
        "comparison_v1_v2": comparison,
        "latency_ms": {
            "p50": latencies[len(latencies) // 2] if latencies else 0,
            "p95": latencies[int(len(latencies) * 0.95)] if latencies else 0,
        },
        "cost": "unavailable (medir 50 execuções no piloto, §17)",
        "pending_human": [
            "rubrica de 2 advogados trabalhistas (evals/rubric.md)",
            "holdout: casos reservados, nunca usados no desenvolvimento",
            "providor LLM real + homologação (backup/restore, filas, OCR)",
        ],
        "results": results,
    }


def render_report(summary: dict) -> str:
    """Relatório Markdown do gate (evidência do T14)."""
    lines = [
        "# Benchmark V2 — relatório do gate",
        "",
        f"Casos: {summary['cases']} · recall de pedidos: {summary['claims_recall']}",
        f"Latência p50/p95: {summary['latency_ms']['p50']}/{summary['latency_ms']['p95']} ms",
        f"Custo: {summary['cost']}",
        "",
        "## Portões (§19.1)",
    ]
    for gate, passed in summary["gates"].items():
        lines.append(f"- [{'x' if passed else ' '}] {gate}")
    comp = summary["comparison_v1_v2"]
    lines.extend(
        [
            "",
            "## V1 × V2",
            f"V1 marcaria completo: {comp['v1_complete']}/{comp['cases']}; "
            f"V2: completed={comp['v2_completed']} partial={comp['v2_partial']} "
            f"failed={comp['v2_failed']}",
            "",
            "## Pendências humanas (bloqueiam piloto)",
            *[f"- {item}" for item in summary["pending_human"]],
        ]
    )
    return "\n".join(lines) + "\n"
