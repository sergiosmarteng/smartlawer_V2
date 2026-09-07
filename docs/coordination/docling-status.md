# Docling Status

Last updated: 2026-09-07 (A2 landed)
Purpose: capture the current SmartLawer workspace state for Docling and markdown conversion before AI analysis.

## Verdict

- Docling implemented in the active code path: `Yes (feature-flagged, default OFF)`
- Uploaded/imported files converted to `.md` before AI analysis: `Yes, when DOCLING_ENABLED=1`
- Active ingestion path today: `POST /api/v1/documents/upload -> process_pdf_task -> PDFExtractor.extract_text() -> prepare_analysis_input() [Docling markdown if enabled] -> LegalAnalyzer.analyze_petition(markdown or raw)`
- Live validation: real `DocumentConverter` conversion proven on dev machine 2026-09-07 (test PDF -> 114 chars markdown). Full-suite: `24 passed`.

## Current Code Path

1. Upload accepts only PDF files and stores the binary on disk.
   - Evidence: `backend/app/api/routes/documents.py:38-92`
2. The worker enqueues `process_pdf_task` and marks the document as "Extracting text from PDF".
   - Evidence: `backend/app/tasks/document_tasks.py:15-35`
3. Extraction uses `PDFExtractor.extract_text(file_path=file_path)`.
   - Evidence: `backend/app/tasks/document_tasks.py:28`
4. `PDFExtractor` uses PyMuPDF text extraction plus Tesseract OCR fallback and returns a plain string.
   - Evidence: `backend/app/core/pdf_processor.py:9-39`
5. The AI step receives that plain string directly as `text`.
   - Evidence: `backend/app/tasks/document_tasks.py:38-40`
   - Evidence: `backend/app/core/ai_engine.py:162-188`

## What Is Not Present

- No `docling` dependency in the backend runtime requirements.
  - Evidence: `backend/requirements.txt`
- No Docling adapter, service client, feature flag, or markdown persistence field in the active backend code.
  - Evidence: SUPERSEDED by A2 — see `backend/app/core/docling_extractor.py`, `Document.raw_text/structured_markdown`, migration `20260907_0002`.
- No model field for persisted markdown output in the current `Document` or `Analysis` tables.
  - Evidence: SUPERSEDED by A2 — `documents.raw_text` + `documents.structured_markdown` added.

## Current Behavior

- The imported file stays as the original PDF on disk.
- The worker flattens the document into raw text early.
- OCR is used only as a fallback for pages with too little native text.
- The AI layer analyzes raw extracted text, not markdown, not structured JSON, and not a Docling document representation.

## Existing Planning Context

- `docs/reports/V1 Flow Stabilization Report (Apr 7, 2026).md` explicitly states that Docling is out of scope for the current delivery path.
- `docs/reports/Docling Integration Assessment (Apr 7, 2026).md` recommends a phased integration in the worker with fallback, but that recommendation has not been implemented in the active code path.
- `docs/reports/90-Day SaaS Plan (Apr 7, 2026).md` treats Docling as future phased work, not current behavior.

## Minimum Viable Integration Recommendation

Recommended first step:

1. Add a feature-flagged extraction adapter inside `process_pdf_task`.
2. When the flag is on, call Docling first and request markdown output.
3. Persist both:
   - `raw_text`
   - `structured_markdown`
4. Pass `structured_markdown` to `LegalAnalyzer` first, with `raw_text` as fallback.
5. If Docling fails, log the reason and fall back to `PDFExtractor.extract_text()` without failing the whole task.

Minimum fallback rule:

- `Docling success -> analyze markdown`
- `Docling failure or disabled -> analyze raw_text from current extractor`

## Coordinator Notes For Next Agent

- Treat Docling as `not implemented`, not as a hidden feature flag.
- If a future worker starts implementation, it should update:
  - `docs/coordination/api-contract.md`
  - `docs/coordination/backlog.md`
  - a new worker report under `docs/coordination/reports/`
- The first implementation milestone should prove markdown generation and persistence before any prompt tuning work.
