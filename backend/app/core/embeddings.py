"""Embedding service for RAG ingestion and queries.

Provider-aware (openai / openrouter / gemini): whichever chat provider is
configured supplies the embeddings too — a Gemini-only deployment gets
vector search out of the box instead of silently indexing nothing.

- openai: ``text-embedding-3-small`` (default, 1536 dims).
- gemini: ``gemini-embedding-001`` (Matryoshka — requests the same
  ``EMBEDDING_DIMENSIONS`` as the pgvector column, so no migration).
- openrouter: via the multi-provider gateway.

The service stays optional at runtime: :func:`embed_texts` returns
``None`` when no provider key is configured or the ``openai`` package is
missing, so the worker can skip vector indexing without failing the
task. Vector dimensionality is validated against settings before use —
a mismatch (wrong model, ignored ``dimensions``) is logged and skipped
rather than corrupting the HNSW index.
"""

import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# When AI_PROVIDER=gemini but EMBEDDING_MODEL still carries the OpenAI
# default, resolve to a Gemini-native model instead of failing at the API.
GEMINI_DEFAULT_EMBEDDING_MODEL = "gemini-embedding-001"
_OPENAI_FAMILY_MODELS = (
    "text-embedding-3-small",
    "text-embedding-3-large",
    "text-embedding-ada-002",
)


def resolve_embedding_model() -> str:
    """Effective embedding model for the configured provider."""
    provider = settings.AI_PROVIDER.lower()
    configured = (settings.EMBEDDING_MODEL or "").strip()
    if provider == "gemini":
        if configured in _OPENAI_FAMILY_MODELS or not configured:
            return GEMINI_DEFAULT_EMBEDDING_MODEL
        return configured
    return configured or "text-embedding-3-small"


def is_configured() -> bool:
    """True when embeddings can actually be produced (per provider)."""
    provider = settings.AI_PROVIDER.lower()
    if provider == "openrouter":
        return bool(settings.OPENROUTER_API_KEY)
    if provider == "gemini":
        return bool(settings.GEMINI_API_KEY)
    return bool(settings.OPENAI_API_KEY)


def _get_client():
    from app.core.openai_compat import build_client

    provider = settings.AI_PROVIDER.lower()
    if provider == "openrouter":
        return build_client(
            settings.OPENROUTER_API_KEY, "https://openrouter.ai/api/v1"
        )
    if provider == "gemini":
        return build_client(settings.GEMINI_API_KEY, settings.GEMINI_BASE_URL)
    return build_client(settings.OPENAI_API_KEY)


def _validate_dimensions(vectors: list[list[float]]) -> bool:
    expected = int(settings.EMBEDDING_DIMENSIONS)
    for vector in vectors:
        if len(vector) != expected:
            logger.error(
                "Embedding dimension mismatch: got %s, expected %s "
                "(model %s, provider %s). Skipping — refusing to "
                "corrupt the vector index.",
                len(vector),
                expected,
                resolve_embedding_model(),
                settings.AI_PROVIDER,
            )
            return False
    return True


def embedding_space() -> dict:
    """Identidade do espaço vetorial ativo (V2 §15).

    Modelos distintos com a mesma dimensão NÃO são intercambiáveis:
    provedor + modelo + versão + dimensão identificam a geração.
    """
    return {
        "provider": settings.AI_PROVIDER.lower(),
        "model": resolve_embedding_model(),
        "version": settings.EMBEDDING_MODEL_VERSION,
        "dimensions": int(settings.EMBEDDING_DIMENSIONS),
    }


def validate_vectors(texts: list[str], vectors: list | None) -> bool:
    """Cardinalidade, dimensão e valores finitos (V2 §15).

    Nunca usar zip silencioso com comprimentos diferentes.
    """
    import math

    if not vectors:
        return False
    if len(vectors) != len(texts):
        logger.error(
            "Embedding cardinalidade divergente: %s textos, %s vetores. "
            "Recusando indexação vetorial.",
            len(texts),
            len(vectors),
        )
        return False
    expected = int(settings.EMBEDDING_DIMENSIONS)
    for vector in vectors:
        if len(vector) != expected or not all(
            isinstance(x, (int, float)) and math.isfinite(x) for x in vector
        ):
            logger.error(
                "Embedding inválido (dimensão ou NaN/Inf); recusando vetor."
            )
            return False
    return True


def validate_query_embedding(query_embedding: list | None) -> bool:
    """Vetor de consulta íntegro para o ANN; inválido degrada para FTS."""
    import math

    if not query_embedding:
        return False
    expected = int(settings.EMBEDDING_DIMENSIONS)
    return len(query_embedding) == expected and all(
        isinstance(x, (int, float)) and math.isfinite(x)
        for x in query_embedding
    )


def embed_texts(texts: list[str]) -> list[list[float]] | None:
    """Embed a batch of texts. Returns ``None`` when unavailable.

    Sends in ``EMBEDDING_BATCH_SIZE`` slices (Gemini caps requests at
    ~100 inputs). For gemini the ``dimensions`` parameter is sent so the
    Matryoshka model matches the pgvector column width.
    """
    texts = [t for t in texts if t and t.strip()]
    if not texts:
        return []
    if not is_configured():
        logger.warning("Embedding API key is not set; skipping vector indexing.")
        return None
    try:
        client = _get_client()
    except ImportError:
        logger.warning("openai package is not installed; skipping embeddings.")
        return None

    model = resolve_embedding_model()
    provider = settings.AI_PROVIDER.lower()
    batch_size = max(1, int(settings.EMBEDDING_BATCH_SIZE))
    vectors: list[list[float]] = []
    for start in range(0, len(texts), batch_size):
        batch = texts[start : start + batch_size]
        try:
            kwargs = {"input": batch, "model": model}
            if provider == "gemini":
                kwargs["dimensions"] = int(settings.EMBEDDING_DIMENSIONS)
            response = client.embeddings.create(**kwargs)
            vectors.extend(list(item.embedding) for item in response.data)
        except Exception as exc:
            logger.warning(
                "Embedding request failed (batch %s-%s, model %s): %s",
                start,
                start + len(batch),
                model,
                exc,
            )
            return None
    if not _validate_dimensions(vectors):
        return None
    return vectors


def embed_query(query: str) -> list[float] | None:
    """Embed a single retrieval query. ``None`` when unavailable."""
    vectors = embed_texts([query])
    if not vectors:
        return None
    return vectors[0]
