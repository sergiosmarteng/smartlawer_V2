# Worker Report — B1 Normalize Integrated Runtime (BL-011, issue #19)

## Task

- ID: BL-011 / #19
- Title: [B1] Normalizar ambiente integrado

## Scope

- What was changed: single-source env for the whole stack, worker boot
  reference, healthchecks, dev-safe Dockerfile flags, full `.env.example`.
- Intentionally left untouched: application code, migrations, frontend,
  CI workflow, ports/topology (same 4 services, same volumes).

## Files Changed

- `docker-compose.yml` — `x-backend-env` anchor shared by `api` + `worker`
  (all `Settings` keys via `${VAR:-default}` + optional `.env` file);
  worker command fixed to unambiguous `celery -A app.worker:celery_app`;
  NEW worker healthcheck (`celery inspect ping`); `start_period` on
  api/worker (migrations + heavy imports); parametrized ports.
- `.env.example` — rewritten: was stale (Clerk-only, unused by the JWT
  backend); now covers compose ports, infra URLs, JWT, AI/RAG flags and
  `NEXT_PUBLIC_API_URL` for `npm run dev`.
- `backend/Dockerfile` — `PYTHONDONTWRITEBYTECODE` + `PYTHONUNBUFFERED`;
  system deps unchanged (tesseract por/eng, docling, docxtpl, psycopg2
  all already present); CMD keeps `--reload` (dev recipe; prod must drop
  it — left for a deployment pass, not this item).
- `docs/coordination/handoff-c1-template-mvp.md` — NEW scoping + ownership
  contract for the parallel Session C (BL-015).

## Decisions

- Decision: `${VAR:-default}` interpolation instead of hardcoded values.
- Reason: `docker compose up` works with zero config for pilot, while any
  `.env` (gitignored) overrides cleanly for shared/prod keys.
- Decision: worker `-A app.worker:celery_app` (module:attr form).
- Reason: unambiguous app reference; the dotted form relies on importer
  fallback heuristics.
- Decision: Session B owns alembic migrations during Onda B/C parallel
  work (single migration-chain owner avoids chain conflicts).
- Reason: coordination rule agreed with user for the two-session split.

## Validation

- Tests run: `docker compose config --quiet` → valid; full backend suite
  untouched by this change (no app code modified).
- `docker compose up -d --build` (background, daemon 29.1.2): backend
  image BUILD COMPLETED (`naming to smartlawer_v2-api:latest done` —
  proves Dockerfile + requirements resolve end-to-end).
- Result: PARTIAL. Container-start/health evidence pending: the daemon
  wedged during multi-GB image unpack (torch/docling tree) and stopped
  responding to CLI; `Restart-Service com.docker.service` issued,
  recovery unconfirmed in-session. Daemon was already down at session
  start (same as A1/A3 notes) — machine-level, not recipe-level.

## Handoff Notes

- Resume for B2/integrator on a healthy daemon:
  1. `docker info` responds → `docker compose up -d` (no rebuild needed)
  2. `docker compose ps` → api/worker/db/redis `healthy`
  3. `curl localhost:8000/health` → `{"status":"healthy"}`
  4. If unpack wedges again: check Docker Desktop disk allocation
     (multi-GB image) before retrying; consider `docling` lazy extras
     or a slim worker image as follow-up.
- Frontend recipe: `NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
  npm run dev` (defaults already match compose).
- C1 (Session C) is unblocked to START implementation against the sqlite
  route harness NOW (see handoff doc); live validation waits for the
  healthy environment above. B4 identifier decision still Session B's.
- Commit: local only, no push (per implementation-plan rule 6).
