"""Embedding service for RAG ingestion and queries.

Uses the OpenAI embeddings API (default ``text-embedding-3-small``).
The service is optional at runtime: :func:`embed_texts` returns ``None``
when no API key is configured or the ``openai`` package is missing, so
the worker can skip vector indexing without failing the task.
"""

import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


def is_configured() -> bool:
    """True when embeddings can actually be produced."""
    provider_key = (
        settings.OPENROUTER_API_KEY
        if settings.AI_PROVIDER.lower() == "openrouter"
        else settings.OPENAI_API_KEY
    )
    return bool(provider_key)


def _get_client():
    from app.core.openai_compat import build_client

    if settings.AI_PROVIDER.lower() == "openrouter":
        return build_client(
            settings.OPENROUTER_API_KEY, "https://openrouter.ai/api/v1"
        )
    return build_client(settings.OPENAI_API_KEY)


def embed_texts(texts: list[str]) -> list[list[float]] | None:
    """Embed a batch of texts. Returns ``None`` when unavailable."""
    texts = [t for t in texts if t and t.strip()]
    if not texts:
        return []
    if not is_configured():
        logger.warning("Embedding API key is not set; skipping vector indexing.")
        return None
    try:
        client = _get_client()
        response = client.embeddings.create(
            input=texts, model=settings.EMBEDDING_MODEL
        )
        return [list(item.embedding) for item in response.data]
    except ImportError:
        logger.warning("openai package is not installed; skipping embeddings.")
        return None
    except Exception as exc:
        logger.warning("Embedding request failed (%s); skipping.", exc)
        return None


def embed_query(query: str) -> list[float] | None:
    """Embed a single retrieval query. ``None`` when unavailable."""
    vectors = embed_texts([query])
    if not vectors:
        return None
    return vectors[0]
