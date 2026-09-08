# Worker Report — B2 Integrated Pilot Smoke (BL-010/012, issue #20)

## Task

- ID: BL-012 (smoke) + BL-013 (DOCX proof) / issues #20, #21
- Title: [B2] Smoke end-to-end + defect sweep

## Scope

- API-level happy path in the live WSL compose stack (B1): JWT register →
  login → me → PDF upload → task poll → processes → analysis → DOCX.
- Reusable script persisted as `docs/coordination/smoke-api.py` (stdlib only,
  self-generates a minimal text PDF, WSL-only per rule 7).
- Browser UI pass (`/sign-up`, `/upload`, `/dashboard` pages) intentionally
  left as manual follow-up — no browser tool in this session.

## Validation

- `python3 docs/coordination/smoke-api.py` → **SMOKE PASSED 10/10**, first run:
  - `register` 200, `login` 200 (JWT), `users/me` 200
  - `upload` 200, `task_id == id` (`1e863c00-…`), canonical
    `taskStatusUrl=/tasks/{id}` (B4 contract holds live)
  - task `COMPLETED` in ~5s (`status_detail=Analysis ready`, fallback
    analyzer — no AI keys in env, expected per smoke-checklist notes)
  - `GET /processes` lists the document (dashboard source of truth OK)
  - `GET /analysis/{id}` 200 with summary/strategy keys
  - `GET /analysis/{id}/docx` 200, `PK` magic, **37151 bytes** — real DOCX
    from the active template path in the integrated env (also covers BL-013).
- Zero defects found on the API path; no sweep items opened.

## Decisions

- Decision: API-level smoke first, browser UI pass deferred to operator.
- Reason: full happy path is provable headlessly today; UI pass needs a
  running `npm run dev` + browser session.
- Decision: smoke PDF is generated in-script (hand-built xref, Helvetica).
- Reason: no binary fixture in repo, no network fetch, deterministic bytes.

## Handoff Notes

- Browser pass still wanted before pilot signoff: sign-up → upload →
  polling → dashboard → analysis → DOCX download via
  `NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1 npm run dev`.
- Stack must be up (`docker compose up -d` in WSL); if the host slept, WSL
  reboots and smartlawer containers stay exited (no restart policy — see
  B1 addendum 2026-09-08). Re-run `up -d` then the smoke script.
- Commit: local only, no push (per implementation-plan rule 6).
