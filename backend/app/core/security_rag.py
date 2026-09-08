"""PII masking + prompt-injection defense for the legal RAG pipeline (A6).

Two responsibilities, no external dependencies:

1. :func:`mask_pii` — deterministic redaction of Brazilian PII before any
   log/trace/LLM-debug output (CPF, CNPJ, e-mail, BR phone, OAB number,
   CNJ process number). Never raises on weird input.
2. :func:`is_injection_attempt` — lightweight PT/EN classifier for direct
   prompt-override attempts in the user query (e.g. "desconsidere as
   instrucoes", "ignore previous instructions", "revele o system prompt").

Retrieved chunks are treated as DATA, never instructions: see
``rag_answer.build_grounded_prompt`` for the isolation delimiters. This
module only classifies the *user query*; chunk content is never executed.
"""

import re

# --- PII patterns (order matters: most specific first) ---

_CPF = re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b|\b\d{11}\b")
_CNPJ = re.compile(r"\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b|\b\d{14}\b")
_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_PHONE = re.compile(
    r"\b(?:\+55\s?)?(?:\(?\d{2}\)?[\s-]?)?(?:9\d{4}|\d{4})[\s-]?\d{4}\b"
)
_OAB = re.compile(r"\bOAB\s*(?:/[A-Z]{2})?\s*(?:N[ºo°]?\s*)?\d{3,7}\b", re.IGNORECASE)
_CNJ = re.compile(r"\b\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}\b")

_PATTERNS: list[tuple[re.Pattern, str]] = [
    (_CNJ, "[PROCESSO]"),
    (_CNPJ, "[CNPJ]"),
    (_CPF, "[CPF]"),
    (_EMAIL, "[EMAIL]"),
    (_OAB, "[OAB]"),
    (_PHONE, "[TELEFONE]"),
]


def mask_pii(text: str | None, *, max_len: int = 500) -> str:
    """Return *text* with PII replaced by tokens, truncated to *max_len*.

    Never raises: ``None``/non-string input yields ``""``.
    """
    if not isinstance(text, str) or not text:
        return ""
    masked = text
    for pattern, token in _PATTERNS:
        masked = pattern.sub(token, masked)
    if len(masked) > max_len:
        masked = masked[:max_len] + "…"
    return masked


def contains_pii(text: str | None) -> bool:
    """True when any known PII pattern is present in *text*."""
    if not isinstance(text, str) or not text:
        return False
    return any(pattern.search(text) for pattern, _ in _PATTERNS)


# --- Prompt-injection classifier (direct query attacks, PT + EN) ---

_INJECTION_PATTERNS: list[re.Pattern] = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"ignor\w*\s+(todas?\s+)?(as\s+)?(instru[cç][oõ]es|ordens)\s+anteriores",
        r"ignore\s+(all\s+)?previous\s+instructions",
        r"disregard\s+(all\s+)?(previous|above)\s+(instructions|prompt)",
        r"desconsidere\s+(o\s+|as\s+)?(instru[cç][oõ]es|regras|prompt|contexto)",
        r"esque[çc]a\s+(o\s+|as\s+)?(instru[cç][oõ]es|regras|prompt|sistema)",
        r"revele?\s+o\s+(system\s+prompt|prompt\s+do\s+sistema|prompt)",
        r"mostre?\s+(o\s+|as\s+)?(instru[cç][oõ]es\s+do\s+sistema|regras\s+internas)",
        r"jailbreak|dan\s+mode|developer\s+mode",
        r"finja\s+que\s+voc[eê]\s+(é|eh)\s+",
        r"aja\s+como\s+se\s+n[aã]o\s+(tivesse|houvesse)\s+(restri|regras|limites)",
        r"exfiltre|vaze\s+os\s+documentos|liste\s+todas\s+as\s+chaves",
        r"override\s+(the\s+)?(system|safety|guardrails)",
        r"bypass\s+(the\s+)?(safety|filter|guardrails)",
        r"system\s*:\s*voce\s+e\s+um\s+assistente\s+sem\s+restri",
        r"打印机|无视.+指令",
    ]
]

# Benign legal phrasing that merely quotes procedural language; the
# classifier must not flag these as attacks.
_SAFE_HARBOR: list[re.Pattern] = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"prazo\s+para\s+(contesta[cç][aã]o|recurso|apela[cç][aã]o)",
        r"qual\s+[ée]\s+o\s+(prazo|artigo|fundamento)",
        r"resuma\s+(o|a|este|esta)\s+(contrato|peti[cç][aã]o|documento|cl[aá]usula)",
        r"quais\s+(s[aã]o\s+)?(as\s+)?cl[aá]usulas",
        r"o\s+que\s+diz\s+(o|a)\s+(artigo|contrato|documento|lei)",
    ]
]


def is_injection_attempt(query: str | None) -> bool:
    """True when *query* looks like a direct prompt-override attempt.

    Safe-harbor legal questions always return False, even if they share
    a keyword with an attack pattern.
    """
    if not isinstance(query, str) or not query.strip():
        return False
    if any(p.search(query) for p in _SAFE_HARBOR):
        # A genuine attack could append legal filler; only honor the
        # harbor when no attack pattern also matches.
        if not any(p.search(query) for p in _INJECTION_PATTERNS):
            return False
        # Both match: attack wins only for explicit override phrasing.
        explicit = any(
            p.search(query) for p in _INJECTION_PATTERNS[:6]
        )
        if not explicit:
            return False
        return True
    return any(p.search(query) for p in _INJECTION_PATTERNS)


BLOCK_MESSAGE = (
    "Nao posso seguir instrucoes embutidas na pergunta. "
    "Reformule como uma pergunta juridica sobre os seus documentos "
    "e responderei apenas com base nos trechos recuperados."
)
