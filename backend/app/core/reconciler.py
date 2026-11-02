"""Reconciliação global: unifica repetições sem apagar conflitos (T06, §5).

Lotes com sobreposição (T05) e páginas repetidas geram candidatos
duplicados; o reconciliador agrupa por número original/título,
une referências e preserva cada ocorrência e divergência.
"""

import logging
import re
import unicodedata

from app.core.schemas_v2 import Claim

logger = logging.getLogger(__name__)

# Palavras vazias: não distinguem pedidos.
_STOPWORDS = frozenset(
    {
        "a", "ao", "aos", "as", "com", "como", "da", "das", "de", "do", "dos",
        "e", "em", "entre", "na", "nas", "no", "nos", "o", "os", "ou", "para",
        "pelo", "pela", "por", "que", "se", "sem", "sob", "um", "uma", "uns",
        "umas",
    }
)

# Aberturas típicas de pedido: dizem o verbo, não o objeto.
_LEAD_INS = frozenset(
    {
        "condenacao", "deferimento", "indenizacao", "indenizatorio", "pagamento",
        "pedido", "pleiteia", "pleito", "reparacao", "requer", "requerimento",
    }
)

# Variantes morfológicas do mesmo termo (não sinônimos de conteúdo).
_MORPHOLOGY = {
    "gratuidade": "gratuit",
    "gratuita": "gratuit",
    "gratuito": "gratuit",
}


def normalize_for_match(text: str | None) -> str:
    """Minúsculas, sem acento, sem pontuação, espaço único."""
    decomposed = unicodedata.normalize("NFKD", text or "")
    stripped = "".join(c for c in decomposed if not unicodedata.combining(c))
    cleaned = re.sub(r"[^a-z0-9]+", " ", stripped.casefold())
    return " ".join(cleaned.split())


def _claim_tokens(text: str | None) -> frozenset[str]:
    """Tokens que distinguem um pedido dos demais."""
    tokens = {
        _MORPHOLOGY.get(token, token)
        for token in normalize_for_match(text).split()
        if token not in _STOPWORDS and token not in _LEAD_INS
    }
    return frozenset(tokens)


def _should_merge(first: frozenset[str], second: frozenset[str]) -> bool:
    """Só funde quando um conjunto CONTÉM o outro.

    Contenção é conservadora por construção: "danos morais" e "danos
    estéticos" nunca se contêm, então jamais são fundidos. Já "pensão
    vitalícia" ⊂ "pensão mensal vitalícia" funde sem ambiguidade.
    """
    if not first or not second:
        return False
    return first <= second or second <= first


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


def _dict_claim_key(claim: dict) -> str:
    number = normalize_claim_number(claim.get("original_number"))
    if number is not None:
        return f"num:{number}"
    title = str(claim.get("title") or "").casefold().strip()[:120]
    return f"title:{title}"


def reconcile_extractions(extractions: list[dict]) -> dict:
    """Reconciliação global V3 (Onda 0 Task 6, §8.6).

    Une repetições preservando ocorrências e fontes; registra conflitos
    sem apagar versões divergentes; fatos de autores distintos permanecem
    separados; lote sobreposto não duplica objeto reconciliado.
    """
    claims: dict[str, dict] = {}
    order: list[str] = []
    controversies: list[dict] = []
    facts: list[dict] = []
    fact_keys: set[tuple[str, str]] = set()
    evidence: dict[str, dict] = {}
    legal_references: dict[str, dict] = {}

    groups: list[dict] = []
    by_number: dict[str, dict] = {}

    def group_for(claim: dict) -> dict:
        """Grupo do pedido: número quando existe, senão contenção de tokens."""
        number = normalize_claim_number(claim.get("original_number"))
        tokens = _claim_tokens(claim.get("title"))
        if number is not None:
            group = by_number.get(number)
            if group is None:
                group = {"key": f"num:{number}", "number": number}
                by_number[number] = group
                groups.append(group)
            return group
        for group in groups:
            if group["number"] is None and _should_merge(
                tokens, group["tokens"]
            ):
                group["tokens"] = group["tokens"] | tokens
                return group
        group = {"key": f"cont:{len(groups)}", "number": None, "tokens": tokens}
        groups.append(group)
        return group

    for extraction in sorted(extractions, key=lambda e: e.get("batch_index", 0)):
        for claim in extraction.get("claims", []) or []:
            key = group_for(claim)["key"]
            refs = list(dict.fromkeys(claim.get("source_refs", []) or []))
            existing = claims.get(key)
            if existing is None:
                merged = dict(claim)
                merged["source_refs"] = refs
                merged["occurrences"] = int(claim.get("occurrences", 1) or 1)
                claims[key] = merged
                order.append(key)
                continue
            for ref in refs:
                if ref not in existing.setdefault("source_refs", []):
                    existing["source_refs"].append(ref)
            existing["occurrences"] = int(existing.get("occurrences", 1) or 1) + int(
                claim.get("occurrences", 1) or 1
            )
            old_amount = existing.get("amount")
            new_amount = claim.get("amount")
            if old_amount and new_amount and old_amount != new_amount:
                controversies.append(
                    {
                        "id": f"controversy-{key}",
                        "description": (
                            f"Pedido {existing.get('original_number')}: "
                            f"valores divergentes {old_amount} x {new_amount}"
                        ),
                        "claim_key": key,
                    }
                )
            # Título mais longo carrega mais informação (ex.: inclui "lucros
            # cessantes" que a variante curta omitia).
            if len(str(claim.get("title") or "")) > len(
                str(existing.get("title") or "")
            ):
                existing["title"] = claim.get("title")
        for fact in extraction.get("facts", []) or []:
            statement = normalize_for_match(fact.get("statement"))
            author = normalize_for_match(fact.get("asserted_by") or "unknown")
            key = (statement, author)
            if not statement or key in fact_keys:
                continue
            fact_keys.add(key)
            facts.append(dict(fact))
        for item in extraction.get("evidence", []) or []:
            item_id = str(item.get("id") or "")
            if item_id and item_id not in evidence:
                evidence[item_id] = dict(item)
        for ref in extraction.get("legal_references", []) or []:
            ref_id = str(ref.get("id") or "")
            if ref_id and ref_id not in legal_references:
                legal_references[ref_id] = dict(ref)

    return {
        "claims": [claims[key] for key in order],
        "facts": facts,
        "controversies": controversies,
        "evidence": list(evidence.values()),
        "legal_references": list(legal_references.values()),
    }
