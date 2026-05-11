# Next Steps After This Batch

## Immediate Validation

1. Run the manual pilot smoke flow in one integrated environment using `docs/coordination/smoke-checklist.md`.
2. Run the stabilized backend suite with the documented local-safe flags and capture the result alongside the smoke outcome.
3. Verify the DOCX download works with a real uploaded document, not only route-level mocks or fallback payloads.

## Highest-Value Follow-Ups

1. Update the shared Axios unauthorized path to clear the mirrored auth cookie as well as local storage.
2. Normalize the backend runtime environment so imports, config loading, database access, and document generation behave the same in local validation and the target deployment setup.
3. Decide whether the current `document id == task id` assumption remains acceptable or should be replaced with an explicit queue/task identifier in the public contract.

## Release Decision Gate

Treat this batch as pilot-ready only if all of the following are true:

- login, upload, processing, dashboard, analysis, and DOCX download work end to end in the same environment
- backend tests still pass after final integration
- no worker handoff assumptions were invalidated during the merge of the mixed worktree
