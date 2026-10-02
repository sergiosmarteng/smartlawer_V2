"""Gate técnico do Dossiê Universal V3 (Onda 0 Task 16).

Rejeita artefato só com pedidos ou com fontes inválidas; aprova corpus
válido. Sem LLM, sem banco: validação estrutural pura sobre o JSON.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def evaluate_case(case: dict) -> list[str]:
    """Retorna violações (vazio = aprovado)."""
    errors: list[str] = []
    if (case.get("schema_version") or "") != "3.0":
        errors.append("schema_version deve ser '3.0'")
    claims = case.get("claims") or []
    facts = case.get("facts") or []
    evidence = case.get("evidence") or []
    sources = case.get("sources") or []
    if claims and not facts and not evidence:
        errors.append("artefato só com pedidos: sem fatos nem provas")
    known = {s.get("id") for s in sources if isinstance(s, dict) and s.get("id")}
    for fact in facts:
        if not isinstance(fact, dict):
            continue
        for ref in fact.get("source_refs", []) or []:
            if ref not in known:
                errors.append(f"fato {fact.get('id')}: fonte inválida {ref!r}")
    return errors


def evaluate_cases(cases: list[dict]) -> dict:
    failures = []
    for index, case in enumerate(cases):
        errors = evaluate_case(case or {})
        if errors:
            failures.append({"index": index, "errors": errors})
    return {"passed": not failures, "failures": failures, "total": len(cases)}


def main(argv: list[str] | None = None) -> int:
    argv = list(argv if argv is not None else sys.argv[1:])
    path = Path(argv[0]) if argv else Path(__file__).parent / "universal_dossier_cases.json"
    cases = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(cases, dict):
        cases = cases.get("cases", [])
    result = evaluate_cases(cases)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
