# Worker Report — A2 Docling Ingestion (2026-09-07)

## Scope

BL-016 + GitHub issue #14: feature-flagged Docling ingestion with markdown persistence and fallback, per `docling-status.md` minimum viable recommendation.

## Changes

- `backend/app/core/docling_extractor.py` (new): `extract_markdown()` with lazy singleton `DocumentConverter`; never raises — returns `None` when Docling is missing, conversion fails, or output is empty. `reset_converter_cache()` test hook.
- `backend/app/core/config.py`: `DOCLING_ENABLED: bool = False` (default off).
- `backend/app/models/document.py`: `raw_text` + `structured_markdown` (nullable Text).
- `backend/alembic/versions/20260907_0002_doc_markdown.py` (new): adds both columns; chain `...0001 -> 20260907_0002` verified via offline `--sql`.
- `backend/app/tasks/document_tasks.py`: new `prepare_analysis_input()` — Docling markdown wins when flag on and conversion succeeds, else `raw_text`; both persisted; adapter call wrapped in try/except (defense in depth). Analyzer now receives `analysis_text`.
- `backend/requirements.txt`: `docling==2.94.0` pinned (version validated live).
- `backend/Dockerfile`: `tesseract-ocr-por` + `tesseract-ocr-eng` (extractor uses `lang="por+eng"`).
- `backend/tests/test_docling_extraction.py` (new, 6 tests): adapter missing/empty/success; flag off never calls Docling; flag on uses + persists markdown; failure falls back to raw with COMPLETED status.
- Docs: `docling-status.md` verdict flipped, `api-contract.md` extraction section updated, `backlog.md` BL-016 → completed.

## Validation

- `pytest tests/ -q`: **24 passed** (18 before + 6 new).
- Real conversion: generated PDF via PyMuPDF → `extract_markdown()` → 114 chars markdown, `DocumentConverter` init + OCR models downloaded on first run.
- Fallback preserved: flag off path byte-identical to pre-A2 behavior (raw text to analyzer).

## Notes for next worker (A3)

- `document_chunks` (A1) is still unwritten — A3 should add the legal chunker + embedding service that fills it from `structured_markdown`/`raw_text`.
- Live pgvector + Docker runtime validation still pending (daemon was down).
