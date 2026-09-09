from app.core import rag_answer
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
    _provider(monkeypatch, AI_PROVIDER="gemini", GEMINI_API_KEY="")
    analyzer = LegalAnalyzer()
    assert analyzer.client is None
    result = analyzer.analyze_petition("Algum texto")
    assert result["summary"]
