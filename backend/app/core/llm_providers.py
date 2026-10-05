"""Adaptadores LLM produtivos (W-1, wiring V3).

Implementam os Protocols ``StructuredProvider``/``AnalysisProvider``
sobre o cliente OpenAI-compatível real (mesma chamada de
``LegalAnalyzer.analyze_petition``: ``temperature=0.0``,
``response_format={"type": "json_object"}``). Erros de transporte viram
``ProviderUnavailableError``; conteúdo vazio/inválido vira
``OutputInvalidError`` — os consumidores convertem para os erros
seguros de cada estágio. Sem prompt de domínio aqui: os payloads vêm
dos chamadores (SYSTEM_PROMPT do extrator, payload do analisador).
"""

import json
import logging

from app.core.ai_engine import (
    OutputInvalidError,
    ProviderUnavailableError,
    resolve_chat_config,
)

logger = logging.getLogger(__name__)


def _resolve_or_raise():
    config = resolve_chat_config()
    if config is None:
        raise ProviderUnavailableError(
            "Provedor de IA nao configurado; verifique a chave do provedor ativo."
        )
    return config


def _build_client(config: dict):
    from app.core.openai_compat import build_client

    return build_client(config["api_key"], config.get("base_url"))


class _BaseLlmProvider:
    def __init__(self, client=None, model: str | None = None):
        if client is not None:
            self.client = client
            self.model = model or "test-model"
            return
        config = _resolve_or_raise()
        self.model = config["model"]
        try:
            self.client = _build_client(config)
        except Exception as exc:
            raise ProviderUnavailableError(f"Cliente LLM indisponivel: {exc}") from exc
        if self.client is None:
            raise ProviderUnavailableError("Cliente LLM indisponivel.")

    def _complete(self, *, system: str, user: str) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                temperature=0.0,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            )
        except (ProviderUnavailableError, OutputInvalidError):
            raise
        except Exception as exc:
            raise ProviderUnavailableError(f"Falha no provedor de IA: {exc}") from exc
        content = ((response.choices[0].message.content) or "").strip()
        if not content:
            raise OutputInvalidError("Resposta vazia do provedor de IA.")
        return content


class LlmStructuredProvider(_BaseLlmProvider):
    """``StructuredProvider`` real para ``extract_batch``."""

    def complete_json(self, prompt: str) -> dict:
        content = self._complete(
            system="Responda APENAS com o objeto JSON pedido, sem texto extra.",
            user=prompt,
        )
        try:
            parsed = json.loads(content)
        except Exception as exc:
            raise OutputInvalidError(f"JSON invalido da IA: {exc}") from exc
        if not isinstance(parsed, dict):
            raise OutputInvalidError("Saída da IA fora do schema (objeto esperado).")
        return parsed


ANALYSIS_OUTPUT_SCHEMA = (
    "Formato exato da resposta JSON: "
    '{"procedural_issues": [{"id": "pi<n>", "issue": "<texto>", '
    '"conclusion": "<texto>", "source_refs": ["<id de fonte>"]}], '
    '"theses": [{"id": "t<n>", "represented_side": '
    '"<claimant|respondent|neutral>", "issue": "<texto>", '
    '"conclusion": "<texto>", "factual_premises": ["<id de fato>"], '
    '"legal_premises": ["<id de referência>"], '
    '"supporting_refs": ["<id de fonte>"], "adverse_refs": ["<id de fonte>"], '
    '"counterargument": "<texto ou null>", "prerequisites": [], '
    '"requested_evidence": [], "action": "<texto ou null>", '
    '"limitations": "<texto ou null>"}], '
    '"risks": [{"id": "r<n>", "issue": "<texto>", "impact": "<texto>"}], '
    '"actions": [{"id": "a<n>", "description": "<texto>"}], '
    '"questions": [{"id": "q<n>", "question": "<texto>"}], '
    '"limitations": []}. '
    "Teses para ambos os polos; premissas e fontes restritas aos ids "
    "fornecidos; arrays vazios só quando inexistentes, nunca invente ids."
)


class LlmAnalysisProvider(_BaseLlmProvider):
    """``AnalysisProvider`` real para ``analyze_universal_case``."""

    def analyze(self, payload: dict) -> dict:
        content = self._complete(
            system="Responda APENAS com o objeto JSON pedido, sem texto extra.",
            user=f"{ANALYSIS_OUTPUT_SCHEMA}\nCaso:\n"
                 f"{json.dumps(payload, ensure_ascii=False)}",
        )
        try:
            parsed = json.loads(content)
        except Exception as exc:
            raise OutputInvalidError(f"JSON invalido da IA: {exc}") from exc
        if not isinstance(parsed, dict):
            raise OutputInvalidError("Saída da IA fora do schema (objeto esperado).")
        return parsed
