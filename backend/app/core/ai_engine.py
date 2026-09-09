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

    def _fallback_analysis(self, text: str, *, reason: str) -> dict[str, Any]:
        trimmed_text = (text or "").strip()
        if not trimmed_text:
            logger.warning("Fallback analysis generated with empty petition text (%s).", reason)
            return {
                "summary": "Nao foi possivel extrair texto util do documento enviado.",
                "requests": ["Validar a extracao do PDF e reenviar o arquivo, se necessario."],
                "laws": [],
                "evidence": "Nenhuma prova estruturada foi identificada no texto extraido.",
                "defense_theses": self.FALLBACK_THESES,
            }

        paragraphs = re.split(r"\n\s*\n", trimmed_text)
        summary_source = next((paragraph.strip() for paragraph in paragraphs if paragraph.strip()), trimmed_text)
        summary = summary_source[:1500].strip()

        request_candidates = [
            line
            for line in self._first_non_empty_lines(trimmed_text, limit=240, max_lines=80)
            if any(marker in line.lower() for marker in ("requer", "pedido", "pleiteia", "postula"))
        ]
        if not request_candidates:
            request_candidates = ["Pedidos nao estruturados automaticamente; revisar o texto integral da peticao."]

        law_candidates = re.findall(
            r"(art\.?\s*\d+[A-Za-z0-9.,/-]*|lei\s*n[.o]*\s*\d+[./-]?\d*|codigo\s+[A-Za-z ]+)",
            trimmed_text,
            flags=re.IGNORECASE,
        )
        normalized_laws = self._deduplicate([item.strip() for item in law_candidates if item.strip()])[:8]

        evidence_candidates = [
            line
            for line in self._first_non_empty_lines(trimmed_text, limit=240, max_lines=120)
            if any(marker in line.lower() for marker in ("prova", "document", "anex", "comprov", "contrato", "email", "laudo"))
        ]
        if evidence_candidates:
            evidence = evidence_candidates[:5]
        else:
            evidence = "Nenhuma prova estruturada foi identificada automaticamente."

        logger.warning("Using heuristic fallback analysis because %s", reason)
        return {
            "summary": summary or "Resumo indisponivel para o documento analisado.",
            "requests": self._deduplicate(request_candidates)[:6],
            "laws": normalized_laws,
            "evidence": evidence,
            "defense_theses": self.FALLBACK_THESES,
        }

    def _normalize_analysis_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
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

        normalized = {
            "summary": summary or "Resumo indisponivel para o documento analisado.",
            "requests": [str(item).strip() for item in requests if str(item).strip()],
            "laws": [str(item).strip() for item in laws if str(item).strip()],
            "evidence": evidence if evidence not in (None, "", []) else "Nenhuma prova estruturada foi identificada.",
            "defense_theses": [str(item).strip() for item in defense_theses if str(item).strip()],
        }

        if not normalized["requests"]:
            normalized["requests"] = ["Pedidos nao estruturados automaticamente; revisar o texto integral da peticao."]
        if not normalized["defense_theses"]:
            normalized["defense_theses"] = self.FALLBACK_THESES

        return normalized

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
        return (
            f"{instructions}\n\n"
            f"{FORMAT_INSTRUCTIONS}\n\n"
            f"TEXTO DA PETICAO:\n{text[:20000]}"
        )

    def analyze_petition(self, text: str, strategy_prompt: str | None = None) -> dict:
        if not self.api_key or self.client is None or not self.model:
            return self._fallback_analysis(text, reason="AI provider is not configured")

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
            try:
                result = AnalysisResult.model_validate_json(content)
            except Exception:
                result = AnalysisResult.model_validate(json.loads(content))
            return self._normalize_analysis_payload(result.model_dump())
        except Exception as exc:
            logger.error("Erro no processamento da IA: %s", exc)
            return self._fallback_analysis(text, reason=str(exc))
