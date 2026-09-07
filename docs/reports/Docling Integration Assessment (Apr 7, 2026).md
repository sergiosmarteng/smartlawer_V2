# Docling Integration Assessment for SmartLawer_V2

Date: April 7, 2026
Scope: Evaluate whether integrating Docling is strategically and technically beneficial for SmartLawer_V2.

## Executive Recommendation

Integrating Docling is a good strategic move for SmartLawer_V2, with one condition:
- Integrate in a phased way, starting with a feature-flagged replacement of the current PDF extraction path inside Celery workers.
- Do not make a big-bang migration.

Why:
- Your current extraction is mostly plain text + fallback OCR. It loses layout semantics and tables.
- Legal petitions often depend on structure (sections, exhibits, tables, numbered requests, references) that improves downstream AI quality.
- Docling provides richer document conversion outputs and extraction options that can significantly improve analysis quality and reduce hallucinations caused by poor input representation.

## What We Have Today (SmartLawer_V2)

Current pipeline (backend):
- Upload PDF via `/api/v1/documents/upload`.
- Celery task `process_pdf_task` calls `PDFExtractor.extract_text`.
- OCR fallback with Tesseract.
- Send raw text to LLM (`LegalAnalyzer.analyze_petition`) and store `Analysis`.

Technical limits in current approach:
- Layout is flattened early (lists, tables, headers, multi-column documents degrade).
- No robust structural representation for legal argument hierarchy.
- No dedicated extraction quality metrics.

## Docling Snapshot (as of April 7, 2026)

Observed from official sources:
- Python package available on PyPI (`docling`), latest version observed: `2.84.0` (Apr 1, 2026).
- Built-in Python API (`DocumentConverter`) and CLI.
- Can export converted output to markdown/JSON and supports table extraction workflows.
- Official API wrapper exists (`docling-serve`) with stable `v1` API and container images.
- `docling-serve` latest release observed: `v1.15.1` (Mar 26, 2026).
- Licenses observed: MIT.

## Fit Analysis for SmartLawer_V2

### Strong Fit Areas

1. Better input quality for legal LLM analysis
- Keep structure, section boundaries, and table content.
- Improves prompt grounding and consistency.

2. OCR + structure in one conversion layer
- Replaces custom extraction branching logic with a more standardized converter.

3. Output flexibility
- Markdown/JSON outputs can feed:
  - current summarize/classify prompts
  - future RAG indexing
  - evidence/request detection pipelines

4. Future-ready architecture
- Direct library mode for fast integration.
- Service mode (`docling-serve`) later for scale isolation and independent autoscaling.

### Risks / Tradeoffs

1. Resource footprint
- Docling service images are large and can be expensive on infra.
- CPU-only performance may be slower on large scanned petitions.

2. Fast release cadence
- Frequent releases are good but may break assumptions.
- Must pin version and regression test extraction output.

3. Operational complexity
- Another moving part if deployed as separate service.
- Requires observability and fallback path.

4. Data privacy operations
- Self-hosted is required for legal confidentiality expectations.
- Need strict controls over temporary files and retention.

## Integration Options

### Option A: In-process library integration (recommended first step)

Approach:
- Add Docling conversion call inside `process_pdf_task`.
- Keep existing extractor as fallback with feature flag.

Pros:
- Lowest adoption friction.
- No new service in early stage.

Cons:
- Worker containers become heavier.
- Extraction and task execution remain coupled.

Effort estimate:
- 2 to 3 weeks (1 backend engineer + QA support).

### Option B: Dedicated `docling-serve` microservice (recommended phase 2)

Approach:
- Run `docling-serve` container.
- Worker sends file/url to `/v1/convert/...` API.
- Persist normalized conversion output in DB/object storage.

Pros:
- Better separation of concerns.
- Independent scaling and tuning.
- Cleaner path to GPU acceleration later.

Cons:
- More infra and deployment complexity.

Effort estimate:
- 3 to 5 weeks (backend + infra + QA).

## Proposed Target Architecture with Docling

1. Upload PDF.
2. Celery task requests Docling conversion (library or service).
3. Store:
- `raw_text`
- `structured_markdown`
- `tables_json` (when available)
- extraction metadata (converter version, elapsed time, confidence proxy fields if available)
4. Analyzer prompt consumes structured representation first, raw text as fallback.
5. Persist analysis as usual.

## Effort and Cost Estimate (Practical)

### MVP integration (production-safe)

Work packages:
1. Extraction adapter and feature flags.
2. Storage schema updates for structured outputs.
3. Prompt updates to use structured input.
4. Benchmark suite (50 to 100 representative legal docs).
5. Rollout controls and fallback.

Estimated effort:
- Engineering: 4 to 6 person-weeks.
- QA + legal review: 1 to 2 person-weeks.
- Total elapsed time: 4 to 6 calendar weeks.

## Decision: Is It a Real Good Thing to Integrate?

Yes, for SmartLawer_V2 this is a high-value integration, especially for Brazilian legal documents where formatting and legal structure carry semantic weight.

Business value:
- Better analysis quality.
- Better user trust in AI outputs.
- Better foundation for premium features (RAG, citations, evidence mapping).

Recommendation:
- Proceed with phased integration now.
- Gate rollout with measurable quality KPIs.

## Success Metrics for the Integration

Track before/after on a fixed legal corpus:
- Extraction completeness (manually sampled).
- Section detection accuracy.
- Table extraction quality.
- LLM output quality score by legal reviewers.
- End-to-end processing time and failure rate.

Go/No-Go threshold (suggested):
- >= 20% reduction in extraction-related analysis errors.
- <= 15% increase in median processing time on CPU baseline.
- No regression in task failure rate.

## Primary Sources

- Docling GitHub: https://github.com/docling-project/docling
- Docling docs: https://docling-project.github.io/docling/v2/
- Docling CLI docs: https://docling.site/cli/
- Docling PyPI: https://pypi.org/project/docling/
- Docling Serve GitHub: https://github.com/docling-project/docling-serve
