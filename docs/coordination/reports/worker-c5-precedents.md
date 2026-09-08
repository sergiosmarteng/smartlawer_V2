# Worker Report — C5 Traceable Jurisprudence in RAG (BL-023, issue #28)

## Task

- ID: BL-023 / #28
- Title: [C5] Jurisprudência rastreável no RAG
- DoD: respostas com precedentes citados e golden cobrindo.

## Scope

- Shared corpus: 6 curated precedents (SV 11/13/10, STJ 297/479, Tema 69)
  seeded as ordinary `document_chunks` owned by a fixed system user —
  one system Document per precedent so citations resolve to
  `[Jurisprudência] TRIBUNAL número — tema` labels.
- Retrieval includes the corpus through the same closed two-id
  allowlist (caller + system); document-scoped chat stays private-only.
  Keyless `seed-noop` rows are excluded from the vector branch (they
  still match via FTS); lifespan reseed upgrades them when keys appear.
- Auto-seed in API lifespan (flag `PRECEDENTS_AUTO_SEED`, off in tests);
  admin `POST /precedents/seed` + `GET /precedents` (labels).
- Golden +2 (`g31/g32`, category `jurisprudencia`) + corpus `c13/c14`;
  gate stays green. Chat UI renders precedent citations as badges
  (no dead analysis links).
- No new tables, no migration.

## Files Changed

- Backend: `core/precedents.py` (NEW), `core/retrieval.py` (allowlist),
  `core/config.py` + compose + `.env.example` (flag),
  `app/main.py` (lifespan seed + router),
  `api/routes/precedents.py` (NEW), `tests/conftest.py` (flag off).
- `backend/tests/test_precedents.py` — NEW (7 tests).
- `backend/tests/test_retrieval.py` — tenant-SQL test updated to the
  template structure (barrier preserved + stronger).
- `backend/tests/test_eval_gate.py` — 30 → 32 items.
- `backend/evals/{golden_legal,corpus_fixture}.json` — g31/g32 + c13/c14.
- Frontend: `pages/chat.tsx` (precedent badge).

## Decisions

- Decision: shared chunks over a new precedents table/vectors infra.
- Reason: reuses FTS+HNSW+RRF+rerank+citations+gate unchanged; zero
  migration; tenant barrier stays a closed allowlist.
- Decision: thesis-level paraphrase + official portals, not verbatim ementas.
- Reason: verbatim reproduction from memory risks error; counsel must
  review before production reliance (HITL spirit).
- Decision: precedent chunks excluded from document-scoped chat.
- Reason: scope means "answer from THIS document".

## Validation

- `pytest backend/tests` → **106 passed** (99 + 7), no regressions.
- Eval gate: **32 items, mean 0.969, PASSED** (g09 still the only canary;
  negative controls still fail as designed).
- `tsc` clean, targeted `next lint` clean.
- WSL live: lifespan auto-seeded 6 rows; FTS `algemas` hits the SV 11
  chunk; B2 smoke re-passed **10/10**.
- Known FTS characteristic (pre-existing, A3): unaccented query terms
  don't match accented stems (`licito` vs `lícit`) — consistent for all
  chunks, not a C5 defect; `unaccent` extension is a future upgrade.
- Live chat with precedent citations needs real AI keys (env has none) —
  covered at unit level (retrieval returns them; answer cites them).

## Handoff Notes

- After configuring embedding keys, hit `POST /precedents/seed` as
  admin once (or just reboot the API) for real seed vectors.
- Commit: local only, no push (per implementation-plan rule 6).
