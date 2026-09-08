# Archive — superseded microharness project docs (B5)

These files belonged to the **microharness** worker experiment (MQTT swarm
harness, phases 1–12) and no longer describe the SmartLawer V2 product:

- `microharness-TASKS.md` (was `docs/TASKS.md`)
- `microharness-CHANGELOG.md` (was `docs/CHANGELOG.md`)

The live planning surface is `docs/coordination/` (`backlog.md`,
`implementation-plan.md`, `api-contract.md`, `integration-log.md`,
`reports/`). Nothing in the codebase or coordination docs referenced the
archived files at move time (verified by grep in worker-b5 report).

History is preserved in git — `git log -- docs/archive/` and
`git log --follow` recover every version.
