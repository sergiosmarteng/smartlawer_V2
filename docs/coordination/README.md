# Agent Coordination

This folder is the shared execution surface for the SmartLawer V2 stabilization pass.

## Read Order

1. `backlog.md`
2. `integration-log.md`
3. `api-contract.md`
4. The latest dependency report in `reports/`

## Files

- `backlog.md`: source of truth for task status, dependencies, and ownership.
- `api-contract.md`: current frontend/backend workflow shape and known gaps.
- `integration-log.md`: append-only coordinator log for landed worker output.
- `reports/TEMPLATE.md`: required report structure.
- `reports/*.md`: worker-specific delivery notes.

## Worker Rules

1. Read your dependency chain before editing code.
2. Treat other uncommitted changes as active work in progress.
3. Do not rewrite or delete another worker's report.
4. Keep reports practical: scope, files, decisions, validation, handoff.
5. If you change contract behavior, update or request an update to `api-contract.md`.
6. **Commit local obrigatório ao concluir cada etapa (mínimo):** código + testes verdes + docs da etapa em um commit local no repo correspondente. Sem push — push somente quando o usuário pedir explicitamente.
7. **Nunca testar com Docker no Windows: usar sempre e apenas o WSL.** Todo comando `docker`/`docker compose` (build, up, smoke, validação de runtime) roda dentro do WSL. No PowerShell/Windows, apenas edição de código e testes locais (pytest sqlite, tsc, eslint).

## Coordinator Rules

- Update `backlog.md` when a worker lands or gets blocked.
- Append integration notes to `integration-log.md` instead of rewriting history.
- Keep `api-contract.md` biased toward the current workspace, not older planning docs.
- Use `docs/implementation/implementation_log.md` for milestone-level notes only.

## Current Coordination Notes

- BL-001 has landed in the workspace and its report is available in `reports/worker-bl-001-auth.md`.
- BL-002, BL-007, BL-008, and BL-009 already have worker reports and should be read before touching workflow, DOCX, or test assumptions.
- BL-005 and BL-006 are the remaining tracks most likely to move UI-facing contract details.
- `smoke-checklist.md` exists for final pilot verification, but BL-010 remains coordinator-owned.
- Keep this surface short enough for a new worker to read in a few minutes.
