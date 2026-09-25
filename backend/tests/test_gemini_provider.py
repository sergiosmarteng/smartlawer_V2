from app.core import embeddings, rag_answer
from app.core.ai_engine import LegalAnalyzer, resolve_chat_config
from app.core.config import settings
from app.core.openai_compat import build_client


def test_shared_client_factory_survives_httpx_skew():
    """Regression: openai 1.30.5 + httpx 0.28 break plain OpenAI(...)."""
    client = build_client("k", "https://example.invalid/v1/")
    assert str(client.base_url) == "https://example.invalid/v1/"
    assert build_client("k") is not None


def _provider(monkeypatch, **overrides):
    for key, value in overrides.items():
        monkeypatch.setattr(settings, key, value)


def test_resolve_chat_config_gemini(monkeypatch):
    _provider(
        monkeypatch,
        AI_PROVIDER="gemini",
        GEMINI_API_KEY="g-key",
        GEMINI_BASE_URL="https://example.invalid/v1/",
        CHAT_MODEL="gemini-3-flash-preview",
    )
    config = resolve_chat_config()
    assert config == {
        "model": "gemini-3-flash-preview",
        "base_url": "https://example.invalid/v1/",
        "api_key": "g-key",
    }


def test_resolve_chat_config_gemini_without_key_is_none(monkeypatch):
    _provider(monkeypatch, AI_PROVIDER="gemini", GEMINI_API_KEY="")
    assert resolve_chat_config() is None


def test_resolve_chat_config_openai_uses_chat_model(monkeypatch):
    _provider(
        monkeypatch, AI_PROVIDER="openai",
        OPENAI_API_KEY="o-key", CHAT_MODEL="gpt-xyz",
    )
    assert resolve_chat_config() == {
        "model": "gpt-xyz", "base_url": None, "api_key": "o-key",
    }


def test_resolve_chat_config_openrouter_preserved(monkeypatch):
    _provider(monkeypatch, AI_PROVIDER="openrouter", OPENROUTER_API_KEY="r-key")
    config = resolve_chat_config()
    assert config["model"] == "anthropic/claude-3-opus"
    assert config["base_url"] == "https://openrouter.ai/api/v1"


def test_rag_is_configured_per_provider(monkeypatch):
    _provider(monkeypatch, AI_PROVIDER="gemini", GEMINI_API_KEY="")
    assert rag_answer.is_configured() is False
    _provider(monkeypatch, GEMINI_API_KEY="g-key")
    assert rag_answer.is_configured() is True


def test_rag_chat_client_gemini_passthrough(monkeypatch):
    _provider(
        monkeypatch,
        AI_PROVIDER="gemini",
        GEMINI_API_KEY="g-key",
        GEMINI_BASE_URL="https://example.invalid/v1/",
        CHAT_MODEL="gemini-3-flash-preview",
    )
    client, model = rag_answer._chat_client()
    assert model == "gemini-3-flash-preview"
    assert str(client.base_url) == "https://example.invalid/v1/"
    assert client.api_key == "g-key"


def test_analyzer_gemini_without_key_falls_back(monkeypatch):
    from app.core.ai_engine import ProviderUnavailableError

    _provider(monkeypatch, AI_PROVIDER="gemini", GEMINI_API_KEY="")
    analyzer = LegalAnalyzer()
    assert analyzer.client is None
    # V2 T01: sem provedor, falha explicada — nunca tese genérica em relatório.
    try:
        analyzer.analyze_petition("Algum texto")
    except ProviderUnavailableError as exc:
        assert exc.code == "PROVIDER_UNAVAILABLE"
    else:
        raise AssertionError("analyze_petition deveria falhar sem provedor")
    diag = analyzer.extraction_diagnostic("Algum texto", reason="no provider")
    assert diag["kind"] == "extraction_diagnostic"
    assert "defense_theses" not in diag


def test_embeddings_configured_per_provider(monkeypatch):
    """Regression: gemini provider must not require an OpenAI key."""
    _provider(monkeypatch, AI_PROVIDER="gemini", GEMINI_API_KEY="")
    assert embeddings.is_configured() is False
    _provider(monkeypatch, AI_PROVIDER="gemini", GEMINI_API_KEY="g-key")
    assert embeddings.is_configured() is True
    _provider(
        monkeypatch,
        AI_PROVIDER="gemini",
        GEMINI_API_KEY="g-key",
        OPENAI_API_KEY="",
    )
    assert embeddings.is_configured() is True


def test_resolve_embedding_model_gemini_skew_guard(monkeypatch):
    # Default OpenAI model + gemini provider resolves to a Gemini model.
    _provider(
        monkeypatch,
        AI_PROVIDER="gemini",
        GEMINI_API_KEY="g-key",
        EMBEDDING_MODEL="text-embedding-3-small",
    )
    assert embeddings.resolve_embedding_model() == "gemini-embedding-001"
    # Explicit Gemini-family model is respected.
    _provider(monkeypatch, EMBEDDING_MODEL="text-embedding-004")
    assert embeddings.resolve_embedding_model() == "text-embedding-004"
    # OpenAI provider keeps its default.
    _provider(
        monkeypatch,
        AI_PROVIDER="openai",
        EMBEDDING_MODEL="text-embedding-3-small",
    )
    assert embeddings.resolve_embedding_model() == "text-embedding-3-small"


class _FakeEmbeddings:
    def __init__(self, calls, dims, error=None):
        self._calls = calls
        self._dims = dims
        self._error = error

    def create(self, **kwargs):
        if self._error is not None:
            raise self._error
        self._calls.append(kwargs)
        data = [
            type("Item", (), {"embedding": [0.1] * self._dims})()
            for _ in kwargs["input"]
        ]
        return type("Response", (), {"data": data})()


class _FakeEmbedClient:
    def __init__(self, calls, dims, error=None):
        self.embeddings = _FakeEmbeddings(calls, dims, error)


def test_embed_texts_gemini_sends_dimensions_and_batches(monkeypatch):
    calls: list[dict] = []
    _provider(
        monkeypatch,
        AI_PROVIDER="gemini",
        GEMINI_API_KEY="g-key",
        GEMINI_BASE_URL="https://example.invalid/v1/",
        EMBEDDING_MODEL="text-embedding-3-small",  # default skew — must resolve
        EMBEDDING_DIMENSIONS=1536,
        EMBEDDING_BATCH_SIZE=2,
    )
    monkeypatch.setattr(
        embeddings,
        "_get_client",
        lambda: _FakeEmbedClient(calls, dims=1536),
    )
    vectors = embeddings.embed_texts(["a", "b", "c"])
    assert vectors is not None and len(vectors) == 3
    # Batched (limit 2 per request) and every call requests 1536 dims.
    assert len(calls) == 2
    assert [len(c["input"]) for c in calls] == [2, 1]
    assert all(c["model"] == "gemini-embedding-001" for c in calls)
    assert all(c["dimensions"] == 1536 for c in calls)


def test_embed_texts_gemini_dimension_mismatch_is_rejected(monkeypatch):
    calls: list[dict] = []
    _provider(
        monkeypatch,
        AI_PROVIDER="gemini",
        GEMINI_API_KEY="g-key",
        EMBEDDING_DIMENSIONS=1536,
    )
    # API ignores `dimensions` and returns 768-d vectors (old text-embedding-004).
    monkeypatch.setattr(
        embeddings, "_get_client", lambda: _FakeEmbedClient(calls, dims=768)
    )
    assert embeddings.embed_texts(["a"]) is None


def test_embed_texts_gemini_api_error_returns_none(monkeypatch):
    _provider(
        monkeypatch,
        AI_PROVIDER="gemini",
        GEMINI_API_KEY="g-key",
    )
    monkeypatch.setattr(
        embeddings,
        "_get_client",
        lambda: _FakeEmbedClient([], dims=1536, error=RuntimeError("boom")),
    )
    assert embeddings.embed_texts(["a"]) is None
