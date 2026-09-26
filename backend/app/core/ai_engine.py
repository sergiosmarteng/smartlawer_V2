import json
import logging
import re
from typing import Any
from typing import List

from pydantic import BaseModel, Field

from app.core.config import settings

logger = logging.getLogger(__name__)


class AnalysisResult(BaseModel):
    summary: str = Field(description="Um resumo detalhado e profissional da peticao.")
    requests: List[str] = Field(description="Lista de pedidos primarios exigidos pelo autor na peticao.")
    laws: List[str] = Field(description="Lista de leis, artigos e jurisprudencias citadas pelo autor.")
    evidence: Any = Field(description="Descricao agregada das provas que o autor diz possuir ou anexa.")
    defense_theses: List[str] = Field(description="Possiveis teses preliminares e de merito para a defesa.")


#: Códigos de erro normalizados da análise (V2 §14 — sem segredos no user_message).
PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
OUTPUT_INVALID = "OUTPUT_INVALID"
CONFIG_ERROR = "CONFIG_ERROR"


class AnalysisError(Exception):
    """Falha explícita da análise — nunca vira relatório final (V2 T01)."""

    code = "ANALYSIS_FAILED"

    def __init__(self, message: str, *, code: str | None = None, retryable: bool = False):
        super().__init__(message)
        if code is not None:
            self.code = code
        self.retryable = retryable


class ProviderUnavailableError(AnalysisError):
    code = PROVIDER_UNAVAILABLE

    def __init__(self, message: str = "Provedor de IA indisponivel ou nao configurado.", *, retryable: bool = True):
        super().__init__(message, code=PROVIDER_UNAVAILABLE, retryable=retryable)


class OutputInvalidError(AnalysisError):
    code = OUTPUT_INVALID

    def __init__(self, message: str = "Resposta da IA invalida ou truncada.", *, retryable: bool = False):
        super().__init__(message, code=OUTPUT_INVALID, retryable=retryable)


#: Static format instructions for the analysis JSON (replaces the former
#: langchain output parser — same contract, no extra dependency).
FORMAT_INSTRUCTIONS = (
    "Responda APENAS com um objeto JSON valido (sem markdown, sem cercas de codigo) "
    "com exatamente estas chaves: "
    '{"summary": "resumo detalhado e profissional da peticao", '
    '"requests": ["pedido 1", "pedido 2"], '
    '"laws": ["lei/artigo/jurisprudencia 1"], '
    '"evidence": "descricao agregada das provas ou lista", '
    '"defense_theses": ["tese preliminar ou de merito 1", "tese 2", "tese 3"]}'
)


def resolve_chat_config() -> dict | None:
    """Pure provider resolution (no SDK imports — unit-testable).

    Returns ``{"model", "base_url" | None, "api_key"}`` or ``None`` when
    the configured provider has no key. ``openai``/``gemini`` honor
    ``CHAT_MODEL``; ``openrouter`` keeps its pinned model.
    """
    provider = settings.AI_PROVIDER.lower()
    if provider == "openrouter":
        if not settings.OPENROUTER_API_KEY:
            return None
        return {
            "model": "anthropic/claude-3-opus",
            "base_url": "https://openrouter.ai/api/v1",
            "api_key": settings.OPENROUTER_API_KEY,
        }
    if provider == "gemini":
        if not settings.GEMINI_API_KEY:
            return None
        return {
            "model": settings.CHAT_MODEL,
            "base_url": settings.GEMINI_BASE_URL,
            "api_key": settings.GEMINI_API_KEY,
        }
    if not settings.OPENAI_API_KEY:
        return None
    return {
        "model": settings.CHAT_MODEL,
        "base_url": None,
        "api_key": settings.OPENAI_API_KEY,
    }


class LegalAnalyzer:
    FALLBACK_THESES = [
        "Exigir comprovacao documental integral dos fatos constitutivos alegados pelo autor.",
        "Questionar o nexo entre os fatos narrados e o pedido final com base nas lacunas do material extraido.",
        "Avaliar preliminares processuais e inconsistencias formais antes do enfrentamento do merito.",
    ]

    def __init__(self):
        self.provider = settings.AI_PROVIDER.lower()
        self.api_key = ""
        self.model: str | None = None
        self.client = None

        config = resolve_chat_config()
        if config is None:
            logger.warning(
                "%s is not set for provider '%s'. Falling back to heuristic summary.",
                "GEMINI_API_KEY" if self.provider == "gemini" else (
                    "OPENROUTER_API_KEY" if self.provider == "openrouter" else "OPENAI_API_KEY"
                ),
                self.provider,
            )
            return

        self.api_key = config["api_key"]
        self.model = config["model"]
        try:
            from app.core.openai_compat import build_client

            self.client = build_client(config["api_key"], config["base_url"])
        except Exception as exc:
            logger.warning("LLM client unavailable (%s); using heuristic summary.", exc)
            self.client = None

    @staticmethod
    def _first_non_empty_lines(text: str, *, limit: int, max_lines: int) -> list[str]:
        lines: list[str] = []
        for line in text.splitlines():
            cleaned = line.strip(" -\t")
            if cleaned:
                lines.append(cleaned)
            if len(lines) >= max_lines:
                break
        return [line[:limit].strip() for line in lines if line.strip()]

    @staticmethod
    def _deduplicate(items: list[str]) -> list[str]:
        seen: set[str] = set()
        normalized: list[str] = []
        for item in items:
            key = item.casefold()
            if key in seen:
                continue
            seen.add(key)
            normalized.append(item)
        return normalized

    def extraction_diagnostic(self, text: str, *, reason: str, code: str = PROVIDER_UNAVAILABLE) -> dict[str, Any]:
        """Diagnóstico técnico de extração — NÃO é análise jurídica final (V2 T01).

        Rotulado como ``kind=extraction_diagnostic`` para que nenhum
        consumidor o apresente como relatório. Não preenche summary,
        requests ou theses jurídicas.
        """
        trimmed_text = (text or "").strip()
        logger.warning("Diagnostico de extracao (%s): %s", code, reason)
        return {
            "kind": "extraction_diagnostic",
            "code": code,
            "reason": reason,
            "chars_extracted": len(trimmed_text),
            "message": "Extracao concluida sem analise juridica; verifique a configuracao do provedor de IA.",
        }

    def _fallback_analysis(self, text: str, *, reason: str) -> dict[str, Any]:
        """Compat: antigo fallback agora retorna só diagnóstico técnico.

        Mantido para não quebrar importadores; NÃO usar como Analysis final.
        """
        return self.extraction_diagnostic(text, reason=reason)

    def _normalize_analysis_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Normaliza resposta REAL da IA sem inventar conteúdo (V2 T01).

        Seções ausentes permanecem vazias para o verificador bloquear a
        completude — nunca preenchidas com teses/frases genéricas.
        """
        summary = str(payload.get("summary") or "").strip()
        requests = payload.get("requests") or []
        laws = payload.get("laws") or []
        defense_theses = payload.get("defense_theses") or []
        evidence = payload.get("evidence")

        if not isinstance(requests, list):
            requests = [str(requests)]
        if not isinstance(laws, list):
            laws = [str(laws)]
        if not isinstance(defense_theses, list):
            defense_theses = [str(defense_theses)]

        return {
            "kind": "analysis",
            "summary": summary,
            "requests": [str(item).strip() for item in requests if str(item).strip()],
            "laws": [str(item).strip() for item in laws if str(item).strip()],
            "evidence": evidence if evidence not in (None, "", []) else "Nenhuma prova estruturada foi identificada.",
            "defense_theses": [str(item).strip() for item in defense_theses if str(item).strip()],
        }

    BASE_INSTRUCTIONS = (
        "Voce e um Especialista de Inteligencia Artificial Juridica.\n"
        "Sua tarefa e analisar o texto extraido da peticao inicial abaixo e organiza-lo.\n"
        "Extraia o resumo dos fatos, os pedidos finais do autor, as leis ou artigos invocados,\n"
        "as evidencias citadas, e construa 3 ou mais teses preliminares ou de merito."
    )

    def build_prompt_text(self, text: str, strategy_prompt: str | None = None) -> str:
        """Assemble the LLM prompt, honoring an optional profile (C3/BL-020).

        ``strategy_prompt`` is extra user guidance prepended to the base
        instructions. ``None``/blank keeps the legacy prompt byte-identical.
        """
        extra = (strategy_prompt or "").strip()
        instructions = (
            f"{self.BASE_INSTRUCTIONS}\n\nOrientacao adicional do perfil: {extra}"
            if extra
            else self.BASE_INSTRUCTIONS
        )
        # V2 T05: sem corte fixo — o CoveragePlanner monta a janela a
        # montante com cobertura registrada; aqui o texto passa integral.
        return (
            f"{instructions}\n\n"
            f"{FORMAT_INSTRUCTIONS}\n\n"
            f"TEXTO DA PETICAO:\n{text}"
        )

    def analyze_petition(self, text: str, strategy_prompt: str | None = None) -> dict:
        """Análise real via LLM. Falha explicada, nunca fallback genérico (V2 T01)."""
        if not self.api_key or self.client is None or not self.model:
            raise ProviderUnavailableError(
                "Provedor de IA nao configurado; verifique a chave do provedor ativo."
            )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                temperature=0.0,
                response_format={"type": "json_object"},
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Voce e um Especialista de Inteligencia Artificial Juridica. "
                            "Responda APENAS com o objeto JSON pedido, sem texto extra."
                        ),
                    },
                    {
                        "role": "user",
                        "content": self.build_prompt_text(text, strategy_prompt),
                    },
                ],
            )
            content = (response.choices[0].message.content or "").strip()
            if not content:
                raise OutputInvalidError("Resposta vazia do provedor de IA.")
            try:
                result = AnalysisResult.model_validate_json(content)
            except Exception:
                try:
                    result = AnalysisResult.model_validate(json.loads(content))
                except Exception as exc:
                    raise OutputInvalidError(f"JSON invalido da IA: {exc}") from exc
            return self._normalize_analysis_payload(result.model_dump())
        except (ProviderUnavailableError, OutputInvalidError):
            raise
        except Exception as exc:
            logger.error("Erro no processamento da IA: %s", exc)
            raise ProviderUnavailableError(f"Falha no provedor de IA: {exc}") from exc
