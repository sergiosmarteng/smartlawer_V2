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

## Completion Addendum — 2026-09-08 (WSL session, rule 7)

- Status: COMPLETED. `docker compose up -d` on native WSL dockerd 29.1.3,
  all layers cached (no rebuild). Evidence, stable 4+ min:
  - `compose ps`: api/db/redis/worker all `healthy`; `/health` →
    `{"status":"healthy"}`; `celery inspect ping` → `pong`, 1 node online;
    worker healthcheck ExitCode 0 across consecutive 15s probes.
  - Alembic ran the full chain at api startup: `20260407_0001 →
    20260907_0001 (pgvector) → 20260907_0002 (raw_text/markdown) →
    20260907_0003 (FTS)`, head = `20260907_0003`.
  - Live DB: `vector` ext `0.8.6`, `documents` has `raw_text` +
    `structured_markdown`, `document_chunks.embedding` is `vector`, indexes
    `…_embedding_hnsw` + `…_content_fts` + tenant/matter present.
- Environment finding (no recipe change made): the WSL Ubuntu guest
  `poweroff`s every few minutes of host idle (journal boot list 23:26→01:29,
  each ending at `poweroff.target`; host-side sleep is the prime suspect —
  01:30 AM local). Each reboot stops `dockerd`; smartlawer containers stay
  `Exited (0)` (compose has no `restart:` policy) while third-party stacks
  with restart policies self-heal. For pilot stability either keep the host
  awake during validation or add `restart: unless-stopped` to the four
  services (recommended B1 follow-up; needs an `up -d` + re-verify cycle).
- B2 smoke followed immediately on this stack: see
  `reports/worker-b2-smoke.md` (PASSED 10/10).

## Resilience Follow-Up — 2026-09-08 (same session)

- Implemented: `restart: unless-stopped` on api/worker/db/redis
  (`docker-compose.yml` only change). `config` valid; `up -d` recreated all
  four; `docker inspect` confirms the policy on every container; all
  `healthy`, `/health` OK, and B2 smoke re-ran **PASSED 10/10** on the final
  recipe (incl. fresh-user tenant isolation: `processes` returned only the
  new user's row).
- Host check: Windows sleep-on-AC is already `never` (`powercfg`
  STANDBYIDLE AC=0); battery idle is 15 min — so the WSL poweroffs track
  host idle/sleep events, not an aggressive AC policy. No rogue scheduled
  tasks found. No sudo passwordless in WSL, so a daemon-restart end-to-end
  test was left to the operator (`wsl -d Ubuntu sudo systemctl restart
  docker` → stack must return alone).
- Caveat learned live: `docker compose kill/stop` sets the daemon's
  manual-stop flag (`hasBeenManuallyStopped=true`), which `unless-stopped`
  honors — after an intentional stop, run `up -d` again or the next daemon
  reboot will leave the stack down. Real crashes/reboots (flag false) do
  self-heal.
