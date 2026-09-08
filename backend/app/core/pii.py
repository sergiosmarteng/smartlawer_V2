"""PII masking for logs and traces (LGPD).

Structured Brazilian identifiers are replaced before anything reaches
logs, error messages or observability payloads: CPF, CNPJ, e-mail,
Brazilian phones, CNJ process numbers and OAB registrations. Free-form
names are intentionally NOT masked (regex cannot do that safely) —
never log raw document text; log ids and hashes instead.
"""

import logging
import re

_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\d{3}\.\d{3}\.\d{3}-\d{2}"), "[CPF]"),
    (re.compile(r"\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}"), "[CNPJ]"),
    (
        re.compile(r"\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}"),
        "[PROCESSO]",
    ),
    (
        re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
        "[EMAIL]",
    ),
    (
        # BR phones require area-code framing: (11) 99999-9999 or 11 99999-9999.
        # Plain digit runs (years, amounts) must NOT match.
        re.compile(r"(?:\(\d{2}\)\s?|\d{2}[\s-])\d{4,5}[\s-]?\d{4}"),
        "[PHONE]",
    ),
    (
        re.compile(r"\bOAB[\s/\-]*[A-Z]{2}[\s\-]*\d[\d.\-]*", re.IGNORECASE),
        "[OAB]",
    ),
]


def mask_pii(text: str | None) -> str | None:
    """Replace structured PII in *text* with Stable placeholders."""
    if not text:
        return text
    masked = str(text)
    for pattern, placeholder in _PATTERNS:
        masked = pattern.sub(placeholder, masked)
    return masked


class PiiMaskingFilter(logging.Filter):
    """Logging filter that masks PII in the final rendered message."""

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            record.msg = mask_pii(record.getMessage())
            record.args = ()
        except Exception:
            pass
        return True


def install_pii_log_filter(
    logger: logging.Logger | None = None,
) -> PiiMaskingFilter:
    """Attach PII masking to *logger* (root by default). Idempotent."""
    target = logger if logger is not None else logging.getLogger()
    for existing in target.filters:
        if isinstance(existing, PiiMaskingFilter):
            return existing
    filt = PiiMaskingFilter()
    target.addFilter(filt)
    return filt
