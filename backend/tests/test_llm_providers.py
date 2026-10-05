"""W-1 — adaptadores LLM produtivos sobre resolve_chat_config()."""

import pytest

from app.core.ai_engine import OutputInvalidError, ProviderUnavailableError


def _msg(content):
    return type("M", (), {"content": content})()


def _choice(content):
    return type("C", (), {"message": _msg(content)})()


def _response(content):
    return type("R", (), {"choices": [_choice(content)]})()


class _FakeCompletions:
    def __init__(self, content=None, exc=None):
        self._content = content
        self._exc = exc
        self.kwargs = None

    def create(self, **kwargs):
        self.kwargs = kwargs
        if self._exc is not None:
            raise self._exc
        return _response(self._content)


class _FakeClient:
    def __init__(self, content=None, exc=None):
        self.chat = type("H", (), {"completions": _FakeCompletions(content, exc)})()


def test_structured_success_returns_dict_and_json_mode():
    from app.core.llm_providers import LlmStructuredProvider

    provider = LlmStructuredProvider(client=_FakeClient('{"claims": []}'), model="m")
    out = provider.complete_json("extraia")
    assert out == {"claims": []}


def test_structured_transport_error_is_provider_unavailable():
    from app.core.llm_providers import LlmStructuredProvider

    provider = LlmStructuredProvider(
        client=_FakeClient(exc=RuntimeError("timeout")), model="m")
    with pytest.raises(ProviderUnavailableError):
        provider.complete_json("extraia")


def test_structured_empty_content_is_output_invalid():
    from app.core.llm_providers import LlmStructuredProvider

    provider = LlmStructuredProvider(client=_FakeClient("   "), model="m")
    with pytest.raises(OutputInvalidError):
        provider.complete_json("extraia")


def test_structured_garbage_string_surfaces_for_batch_error():
    from app.core.llm_providers import LlmStructuredProvider

    provider = LlmStructuredProvider(client=_FakeClient("nao-json {{{"), model="m")
    with pytest.raises(OutputInvalidError):
        provider.complete_json("extraia")


def test_analysis_success_returns_dict():
    from app.core.llm_providers import LlmAnalysisProvider

    provider = LlmAnalysisProvider(client=_FakeClient('{"theses": []}'), model="m")
    out = provider.analyze({"facts": []})
    assert out == {"theses": []}


def test_analysis_prompt_defines_thesis_schema():
    from app.core.llm_providers import LlmAnalysisProvider

    sent: list[str] = []

    class _Capture:
        def __init__(self):
            outer = self

            class _Comp:
                def create(self, **kwargs):
                    for message in kwargs.get("messages", []):
                        if message.get("role") == "user":
                            sent.append(message.get("content", ""))

                    class _Msg:
                        content = '{"theses": []}'

                    class _Choice:
                        message = _Msg()

                    class _Resp:
                        choices = [_Choice()]

                    return _Resp()

            self.chat = type("H", (), {"completions": _Comp()})()

    provider = LlmAnalysisProvider(client=_Capture(), model="m")
    provider.analyze({"facts": [{"id": "f1"}]})
    assert sent
    joined = sent[0]
    for token in ("factual_premises", "supporting_refs", "adverse_refs",
                  "counterargument", "represented_side", "conclusion"):
        assert token in joined


def test_unconfigured_provider_raises_on_construct(monkeypatch):
    from app.core import llm_providers
    from app.core.llm_providers import LlmStructuredProvider

    monkeypatch.setattr(llm_providers, "resolve_chat_config", lambda: None)
    with pytest.raises(ProviderUnavailableError):
        LlmStructuredProvider()
