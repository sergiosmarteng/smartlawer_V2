"""Docling-based PDF ingestion with safe fallback.

``DoclingExtractor.extract_markdown`` converts a PDF into structured
markdown. It NEVER raises: when Docling is unavailable (not installed,
conversion error, empty output) it returns ``None`` so the caller falls
back to :class:`PDFExtractor` raw text. Docling is an optional runtime
dependency on purpose — the worker must not fail just because the
flag is on but the package/model is missing.
"""

import logging

logger = logging.getLogger(__name__)

_converter = None


def _get_converter():
    """Lazily build and cache the Docling converter (singleton)."""
    global _converter
    if _converter is None:
        from docling.document_converter import DocumentConverter

        _converter = DocumentConverter()
    return _converter


def extract_markdown(file_path: str) -> str | None:
    """Convert *file_path* PDF to markdown, or ``None`` on any failure."""
    try:
        converter = _get_converter()
    except ImportError:
        logger.warning("Docling is not installed; skipping markdown ingestion.")
        return None
    except Exception as exc:
        logger.warning("Docling converter init failed (%s); skipping.", exc)
        return None

    try:
        result = converter.convert(file_path)
        markdown = result.document.export_to_markdown()
    except Exception as exc:
        logger.warning("Docling conversion failed for %s (%s); skipping.", file_path, exc)
        return None

    if not markdown or not markdown.strip():
        logger.warning("Docling returned empty markdown for %s; skipping.", file_path)
        return None
    return markdown.strip()


def reset_converter_cache() -> None:
    """Test hook: drop the cached converter."""
    global _converter
    _converter = None
