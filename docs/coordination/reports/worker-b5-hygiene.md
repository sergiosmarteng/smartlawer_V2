# Worker Report — B5 Frontend Hygiene + Archive Microharness Docs

## Task

- ID: BL-? / #23
- Title: [B5] Higiene frontend + arquivar docs microharness

## Scope

- What was changed: shared workflow types, polling hook, real upload
  progress, archived obsolete microharness docs.
- Intentionally left untouched: backend, contract behavior, styling,
  `docs/coordination/*` (except log/backlog entries), outer repo.

## Files Changed

- `src/types/workflow.ts` (NEW) — `UploadResponse`,
  `TaskStatusResponse`, `ProcessItem`, `AnalysisDetailResponse`,
  `NormalizedAnalysis`, `AnalysisNotReadyDetail` + `isActive/Success/
  FailureStatus` helpers. Kills 5 inline interfaces and 2 copies of the
  status Sets (`upload.tsx`, `dashboard.tsx`).
- `src/hooks/useTaskPolling.ts` (NEW) — `schedulePoll`/`cancelPoll`
  with unmount cleanup; `src/types/` and `src/hooks/` were empty dirs.
- `src/pages/upload.tsx` — consumes shared types + hook (identical
  state machine); POST uses axios `onUploadProgress` for real byte
  progress in the 1–20% band (backend pipeline takes over at 24 as
  before); checkpoint dot 1 now lights at ≥24 (upload truly accepted).
- `src/pages/dashboard.tsx` — `Process` → `ProcessItem`, status Sets →
  shared helpers (counters, `StatusBadge`, `fallbackStatusDetail`).
- `src/pages/analysis/[id].tsx` — 3 inline interfaces → shared imports.
- `docs/archive/microharness-{TASKS,CHANGELOG}.md` (moved, history kept)
  + `docs/archive/README.md` — nothing referenced them (grep verified).

## Decisions

- Decision: hook owns only scheduling/cleanup, page keeps the state
  machine.
- Reason: zero behavior drift in the polling transitions; the hook is
  still genuinely reusable for BL-021 batch polling.
- Decision: archive (git mv) instead of delete.
- Reason: `git log --follow` preserves microharness history; README
  records why + what the live surface is.
- Decision: no docker on Windows (rule 7, commit 00bfce5).
- Reason: all B5 validation is Windows-safe (tsc/eslint/pytest/build);
  runtime evidence belongs to WSL sessions.

## Validation

- `npx tsc --noEmit`: clean (one self-caught `Process`→`ProcessItem`
  miss fixed).
- `next lint` on the 5 touched files: no warnings/errors.
- `npm run build`: PENDING at report time (static export slow/hung on
  this machine — see handoff).
- `pytest backend/tests -q`: 65 passed (backend untouched).

## Handoff Notes

- If `build-b5.log` never completes on this machine, re-run `npm run
  build` in WSL or after a restart; tsc+lint already prove type/lint
  health and the change is UI-logic-preserving.
- B4 (#22) already landed via parallel session (ed559a0) — verified
  present, no action needed. C1 handoff doc stands (B4 decision now
  codified: `task_id == document id`).
- Commit: local only, no push (rule 6).
