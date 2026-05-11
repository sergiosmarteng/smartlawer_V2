# Worker Report Template

## Task

- ID: BL-007
- Title: Harden the DOCX generation flow used by analysis download

## Scope

- What was changed
  Hardened `DocxGenerator` so it normalizes the analysis payload before rendering, converts mixed JSON/list/string values into template-safe strings or bullet lists, and raises clearer runtime errors when the template cannot be opened, rendered, or saved.
  Added heuristic fallback behavior to `LegalAnalyzer.analyze_petition()` so the worker still produces a compatible analysis payload when the provider is unconfigured or the structured parse fails.
- What was intentionally left untouched
  `backend/templates/base_template.docx` was left untouched because its current placeholders (`summary`, `requests`, `laws`, `defense_theses`, `evidence`) remain compatible once the payload is normalized in code.

## Files Changed

- `backend/app/core/doc_generator.py`
- `backend/app/core/ai_engine.py`
- `docs/coordination/reports/worker-bl-007-docx-flow.md`

## Decisions

- Decision:
  Normalize at the document-generation boundary instead of changing workflow routes.
- Reason:
  The download route is already being stabilized elsewhere, so the safest way to stay compatible was to accept the current analysis payload shape and make the renderer resilient to `None`, JSONB-style dicts/lists, and fallback strings.

- Decision:
  Keep the template binary unchanged.
- Reason:
  The failure mode was in payload shape and fallback handling, not in the placeholder contract inside the DOCX template.

- Decision:
  Return heuristic analysis data instead of raising hard failures from `LegalAnalyzer` when the provider or parser fails.
- Reason:
  This preserves the existing worker flow while increasing the odds that `/analysis/{id}/docx` has enough structured data to produce a usable document.

## Validation

- Tests run:
  `@'`
  `from pathlib import Path`
  `source = Path("backend/app/core/doc_generator.py").read_text(encoding="utf-8")`
  `compile(source, "backend/app/core/doc_generator.py", "exec")`
  `source = Path("backend/app/core/ai_engine.py").read_text(encoding="utf-8")`
  `compile(source, "backend/app/core/ai_engine.py", "exec")`
  `'@ | python -`
- Result:
  Both edited Python files compiled successfully without writing `__pycache__`. I did not mutate the DOCX template binary.

## Handoff Notes

- Follow-up items:
  If a future template starts using richer placeholders, extend `_normalize_analysis_context()` instead of changing the route payload contract.
- Risks or open questions:
  Runtime assumptions: the template remains available at `backend/templates/base_template.docx`, still uses the current five placeholders, and the process can write generated DOCX files into `tempfile.gettempdir()`. If the deployment environment restricts temp-file writes, the save step will now fail with a clearer error message but still needs an infrastructure fix.
