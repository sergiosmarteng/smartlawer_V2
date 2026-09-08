"""Hybrid retrieval: pgvector ANN + Postgres FTS fused with RRF.

Every query is tenant-scoped: ``user_id`` filtering happens inside each
candidate query BEFORE ranking, so chunks from other tenants can never
leak into results. The shared jurisprudence corpus (C5/BL-023, owned by
the fixed system user) is included through the same closed two-id
allowlist. Reranking (Cohere) is optional and never raises —
absence of key/package silently keeps RRF order.
"""

import logging
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.precedents import NOOP_EMBEDDING_MODEL, SYSTEM_USER_ID

logger = logging.getLogger(__name__)

_TENANT_FILTER_SHARED = "(user_id = :user_id OR user_id = :system_user_id)"
_TENANT_FILTER_PRIVATE = "user_id = :user_id"

VECTOR_CANDIDATES_SQL = """
SELECT id, 1 - (embedding <=> CAST(:query_embedding AS vector)) AS score
FROM document_chunks
WHERE {tenant}
  AND NOT (user_id = :system_user_id AND embedding_model = :noop_model)
ORDER BY embedding <=> CAST(:query_embedding AS vector)
LIMIT :candidate_k
"""

FTS_CANDIDATES_SQL = """
SELECT id,
       ts_rank_cd(to_tsvector('portuguese', content),
                  plainto_tsquery('portuguese', :query_text)) AS score
FROM document_chunks
WHERE {tenant}
  AND to_tsvector('portuguese', content) @@ plainto_tsquery('portuguese', :query_text)
ORDER BY score DESC
LIMIT :candidate_k
"""


def rrf_fuse(rank_lists: list[list], k: int = 60) -> list:
    """Reciprocal Rank Fusion over ordered id lists. Returns ids by score.

    ``rank_lists``: each element is an ordered list of chunk ids (best
    first). Score(id) = sum(1 / (k + rank)) across lists containing it.
    Ties break by first-seen order (vector list should come first).
    """
    scores: dict = {}
    first_seen: dict = {}
    position = 0
    for ranking in rank_lists:
        for rank, chunk_id in enumerate(ranking, start=1):
            key = str(chunk_id)
            scores[key] = scores.get(key, 0.0) + 1.0 / (k + rank)
            if key not in first_seen:
                first_seen[key] = position
                position += 1
    return sorted(scores, key=lambda cid: (-scores[cid], first_seen[cid]))


def fetch_vector_candidates(
    db: Session,
    *,
    user_id: UUID | str,
    query_embedding: list[float],
    candidate_k: int,
    system_user_id: UUID | str = SYSTEM_USER_ID,
    include_shared: bool = True,
) -> list[str]:
    sql = VECTOR_CANDIDATES_SQL.format(
        tenant=_TENANT_FILTER_SHARED if include_shared else _TENANT_FILTER_PRIVATE
    )
    rows = db.execute(
        text(sql),
        {
            "user_id": str(user_id),
            "system_user_id": str(system_user_id),
            "noop_model": NOOP_EMBEDDING_MODEL,
            "query_embedding": str(list(query_embedding)),
            "candidate_k": candidate_k,
        },
    ).all()
    return [str(row[0]) for row in rows]


def fetch_fts_candidates(
    db: Session,
    *,
    user_id: UUID | str,
    query_text: str,
    candidate_k: int,
    system_user_id: UUID | str = SYSTEM_USER_ID,
    include_shared: bool = True,
) -> list[str]:
    sql = FTS_CANDIDATES_SQL.format(
        tenant=_TENANT_FILTER_SHARED if include_shared else _TENANT_FILTER_PRIVATE
    )
    rows = db.execute(
        text(sql),
        {
            "user_id": str(user_id),
            "system_user_id": str(system_user_id),
            "query_text": query_text,
            "candidate_k": candidate_k,
        },
    ).all()
    return [str(row[0]) for row in rows]


def rerank(
    query: str,
    candidates: list[tuple[str, str]],
    top_n: int,
) -> list[str]:
    """Cohere rerank over ``(chunk_id, content)`` pairs.

    Returns the top_n chunk ids. Any unavailability (flag off, no key,
    no package, API error) silently keeps the incoming RRF order.
    """
    fallback = [cid for cid, _ in candidates[:top_n]]
    if not candidates or not settings.RERANK_ENABLED or not settings.COHERE_API_KEY:
        return fallback
    try:
        import cohere

        client = cohere.ClientV2(api_key=settings.COHERE_API_KEY)
        response = client.rerank(
            model=settings.COHERE_RERANK_MODEL,
            query=query,
            documents=[content for _, content in candidates],
            top_n=min(top_n, len(candidates)),
        )
        return [candidates[result.index][0] for result in response.results]
    except Exception as exc:
        logger.warning("Rerank skipped (%s); keeping RRF order.", exc)
        return fallback


def hybrid_search(
    db: Session,
    *,
    user_id: UUID | str,
    query_text: str,
    query_embedding: list[float] | None,
    top_k: int | None = None,
    candidate_k: int | None = None,
    document_id: UUID | str | None = None,
) -> list:
    """Return top fused :class:`DocumentChunk` rows for a tenant query.

    Falls back to pure FTS when no query embedding is available
    (embeddings unconfigured). Never returns other tenants' chunks; the
    shared jurisprudence corpus (system user) is always included except
    when the query is scoped to one private document.
    """
    from app.models.document_chunk import DocumentChunk

    top_k = top_k or settings.RETRIEVAL_TOP_K
    candidate_k = candidate_k or settings.RETRIEVAL_CANDIDATE_K

    rankings: list[list] = []
    include_shared = document_id is None
    if query_embedding:
        rankings.append(
            fetch_vector_candidates(
                db,
                user_id=user_id,
                query_embedding=query_embedding,
                candidate_k=candidate_k,
                include_shared=include_shared,
            )
        )
    else:
        logger.warning("No query embedding; hybrid degrades to FTS-only.")
    rankings.append(
        fetch_fts_candidates(
            db,
            user_id=user_id,
            query_text=query_text,
            candidate_k=candidate_k,
            include_shared=include_shared,
        )
    )

    fused_ids = rrf_fuse(rankings, k=settings.RRF_K)
    if not fused_ids:
        return []

    # Rerank pool: top fused candidates, re-ordered to top_k.
    pool_ids = fused_ids[: max(candidate_k, top_k)]
    allowed_users = [user_id] if document_id is not None else [user_id, SYSTEM_USER_ID]
    filters = [
        DocumentChunk.user_id.in_(allowed_users),
        DocumentChunk.id.in_(pool_ids),
    ]
    if document_id is not None:
        filters.append(DocumentChunk.document_id == document_id)
    rows = db.query(DocumentChunk).filter(*filters).all()
    by_id = {str(row.id): row for row in rows}
    # Second tenant barrier (defense in depth): only rows that came back
    # through the tenant-filtered query can proceed.
    pool = [(cid, by_id[cid].content) for cid in pool_ids if cid in by_id]
    ordered_ids = rerank(query_text, pool, top_n=top_k)
    return [by_id[cid] for cid in ordered_ids if cid in by_id]
