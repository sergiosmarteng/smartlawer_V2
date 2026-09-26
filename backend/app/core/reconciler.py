"""Reconciliação global: unifica repetições sem apagar conflitos (T06, §5).

Lotes com sobreposição (T05) e páginas repetidas geram candidatos
duplicados; o reconciliador agrupa por número original/título,
une referências e preserva cada ocorrência e divergência.
"""

import re

from app.core.schemas_v2 import Claim


def normalize_claim_number(raw: str | None) -> str | None:
    """'Pedido 8', 'item 8.' → '8'. Retorna None se irreconhecível."""
    if not raw:
        return None
    match = re.search(r"\d+", str(raw))
    return match.group(0) if match else None


def _claim_key(claim: Claim) -> str:
    number = normalize_claim_number(claim.original_number)
    if number is not None:
        return f"num:{number}"
    title = (claim.title or "").casefold().strip()[:120]
    return f"title:{title}"


def _union(first: list[str], second: list[str]) -> list[str]:
    merged = list(first)
    for item in second:
        if item not in merged:
            merged.append(item)
    return merged


def reconcile_claims(candidates: list[Claim]) -> list[Claim]:
    """Dedup por número/título; conflitos viram issues revisáveis."""
    grouped: dict[str, Claim] = {}
    order: list[str] = []
    for candidate in candidates:
        key = _claim_key(candidate)
        existing = grouped.get(key)
        if existing is None:
            grouped[key] = candidate.model_copy(deep=True)
            order.append(key)
            continue
        merged = grouped[key]
        merged.occurrences += candidate.occurrences
        merged.source_refs = _union(merged.source_refs, candidate.source_refs)
        merged.factual_basis_refs = _union(
            merged.factual_basis_refs, candidate.factual_basis_refs
        )
        merged.legal_basis_refs = _union(
            merged.legal_basis_refs, candidate.legal_basis_refs
        )
        merged.evidence_refs = _union(merged.evidence_refs, candidate.evidence_refs)
        for rel in candidate.related_claims:
            if rel not in merged.related_claims:
                merged.related_claims.append(rel)
        my_amount = merged.amount.value if merged.amount else None
        other_amount = candidate.amount.value if candidate.amount else None
        if my_amount and other_amount and my_amount != other_amount:
            issue = (
                f"valor divergente entre ocorrências: {my_amount} x {other_amount}"
            )
            if issue not in merged.issues:
                merged.issues.append(issue)
        if candidate.title not in (merged.title, "") and len(candidate.title) > len(
            merged.title
        ):
            merged.title = candidate.title
    return [grouped[key] for key in order]


def reconcile_facts(candidates: list[dict]) -> list[dict]:
    """Dedup simples de fatos por statement normalizado (1ª ocorrência vence)."""
    seen: dict[str, dict] = {}
    for fact in candidates:
        key = (fact.get("statement") or "").casefold().strip()
        if not key or key in seen:
            continue
        seen[key] = fact
    return list(seen.values())
