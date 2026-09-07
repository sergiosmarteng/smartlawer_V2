---

name: code-review
description: Perform focused, evidence-based code reviews for Python, FastAPI, SQLAlchemy, Next.js, React, TypeScript and JavaScript changes.
license: MIT
compatibility: opencode
metadata:
  category: code-quality
  stack: cross-stack
  version: "1.0.0"
orchestration:
  lead_for:
    - code-review
    - refactor
  support_for: []
  conflicts_with:
    - security-review
---

# Code Review

Use this skill when reviewing a pull request, branch, commit, patch, diff or set of modified files.

The objective is to identify bugs, regressions, unsafe behavior and maintainability problems introduced by the change.

Do not provide generic praise or style commentary that does not help the author improve the change.

## Review Scope

Before reviewing:

1. Determine the requested review target.
2. Inspect the diff and relevant surrounding code.
3. Read repository-specific instructions.
4. Inspect package and dependency versions.
5. Identify affected entry points, callers and consumers.
6. Understand the intended behavior from tests, issue descriptions or nearby code.
7. Separate pre-existing problems from problems introduced by the current change.

Do not criticize unrelated existing code unless the change makes that issue materially worse.

## Review Priorities

Review in this order:

1. Correctness
2. Data integrity
3. Security
4. Authentication and authorization
5. Concurrency and transaction safety
6. Error handling
7. API compatibility
8. Type safety
9. Performance
10. Test coverage
11. Maintainability
12. Style

Prioritize issues that could cause production failure or incorrect user-visible behavior.

## Finding Threshold

Report a finding only when:

* The issue is supported by the code.
* It can occur under a realistic execution path.
* It has a meaningful consequence.
* It was introduced or exposed by the reviewed change.
* A reasonable remediation exists.

Do not report:

* Personal style preferences.
* Formatting already enforced by tooling.
* Hypothetical edge cases with no realistic trigger.
* Missing comments when the code is already clear.
* Refactoring opportunities unrelated to correctness.
* Issues that existing code clearly handles elsewhere.
* Dependency vulnerabilities without verified current evidence.

## Severity Levels

Use:

* Blocker: must be resolved before merging because it can cause severe security, data-loss or system-wide failure.
* High: likely production bug, authorization failure, transaction corruption or major regression.
* Medium: meaningful defect under realistic conditions, but limited in scope or frequency.
* Low: minor bug, maintainability concern or edge case worth correcting.
* Suggestion: optional improvement; do not present it as a defect.

Avoid exaggerated severity.

## Python Review

Check for:

* Incorrect default mutable arguments.
* Broad or swallowed exceptions.
* Missing cleanup in files, locks, sessions or temporary resources.
* Incorrect sync/async usage.
* Blocking work inside async functions.
* Incorrect timezone handling.
* Naive versus aware datetime comparisons.
* Iterator or generator exhaustion.
* Incorrect truthiness checks.
* Shared mutable state.
* Type annotations that disagree with runtime behavior.
* Functions returning inconsistent types.
* Incorrect use of context managers.
* Resource leaks.
* Retry loops without limits or backoff.
* Retrying non-idempotent operations.
* Silent partial failure.
* Incorrect use of multiprocessing or threading.

Prefer evidence from tests or call sites.

## FastAPI Review

Check for:

* Request and response schema mismatches.
* Incorrect status codes.
* Missing response models.
* Dependencies not executed as intended.
* Authentication dependencies omitted.
* Authorization applied inconsistently.
* Request-scoped sessions passed to background tasks.
* Blocking code inside async endpoints.
* Exceptions converted into misleading HTTP responses.
* Internal exception details exposed.
* Incorrect streaming response behavior.
* Generators used after their resources are closed.
* File uploads read entirely into memory without limits.
* Background tasks that silently lose failures.
* Endpoint changes that break existing frontend consumers.

## SQLAlchemy and PostgreSQL Review

Check for:

* Missing `rollback()` after transaction failure.
* Reusing an invalid or closed session.
* Incorrect session lifetime.
* Lazy-loaded relationships accessed after session closure.
* N+1 queries.
* Queries missing tenant, branch, user or ownership filters.
* Writes committed partially when atomicity is required.
* Read-modify-write race conditions.
* Missing uniqueness or database constraints.
* Incorrect cascade behavior.
* Accidental deletion.
* Incorrect transaction nesting.
* Connection pooling changes that hide rather than solve transaction bugs.
* Async engines used with sync sessions or the reverse.
* Migrations inconsistent with ORM models.
* Nullable database columns represented as non-nullable types.
* Enum values inconsistent between application and database.
* Pagination without deterministic ordering.

For retry logic, verify whether the operation is idempotent and whether a previous commit may already have succeeded.

## Next.js Review

First inspect the installed Next.js and React versions.

Check for:

* Incorrect Server Component and Client Component boundaries.
* Unnecessary `"use client"`.
* Server-only code imported into client bundles.
* Secrets exposed through public environment variables.
* Route handlers or server actions missing authorization.
* Cache behavior causing stale or cross-user data.
* Dynamic data accidentally statically rendered.
* Client state initialized inconsistently with server rendering.
* Hydration mismatches.
* Redirects or navigation called from invalid contexts.
* Incorrect use of cookies, headers or request APIs.
* Forms that allow duplicate submission.
* Loading, empty and error states missing for realistic flows.
* API response shape changes not reflected in consumers.
* Browser APIs accessed during server rendering.
* Unhandled promise rejection in event handlers.
* Effects with incorrect dependencies or cleanup.

Use current documentation when behavior depends on the framework version.

## React Review

Check for:

* State derived unnecessarily from props.
* Stale closures.
* Missing effect cleanup.
* Infinite render or effect loops.
* Unstable keys.
* Mutating state directly.
* Race conditions between requests.
* Old requests overwriting newer results.
* Event listeners added repeatedly.
* Components retaining sensitive state after logout or account switching.
* Controlled and uncontrolled input transitions.
* Incorrect memoization.
* Context causing excessive rerenders.
* Error boundaries missing around failure-prone areas when appropriate.

Do not request memoization without evidence of a performance problem.

## TypeScript and JavaScript Review

Check for:

* `any` hiding incorrect assumptions.
* Unsafe type assertions.
* Non-null assertions without runtime guarantees.
* Optional and nullable values confused.
* API data trusted without runtime validation.
* Promise-returning functions not awaited.
* Floating promises.
* Errors assumed to be a specific type.
* Object spread allowing protected fields to be overwritten.
* Incorrect equality or coercion.
* Date parsing dependent on browser locale.
* Numeric values accidentally treated as strings.
* Missing exhaustive handling of unions or enums.
* Shared object references mutated unexpectedly.
* Environment variables assumed to exist without validation.

A TypeScript type does not validate network, database or user input at runtime.

## API Compatibility Review

Check whether the change modifies:

* Route paths.
* HTTP methods.
* Request fields.
* Response fields.
* Nullability.
* Status codes.
* Error shape.
* Pagination.
* Sorting.
* Enum values.
* Date formats.
* Authentication requirements.
* WebSocket event names.
* Streaming format.
* File-download behavior.

Search for all consumers before approving an API change.

Flag breaking changes unless they are intentionally coordinated.

## Concurrency and Idempotency

Check for:

* Duplicate requests.
* User double-clicks.
* Worker retries.
* Network retries.
* Multiple workers processing the same job.
* Concurrent balance, quota or token updates.
* Concurrent submissions.
* Background tasks started more than once.
* Scheduled jobs overlapping.
* Webhook replay.
* Lost updates.
* Check-then-act race conditions.

For critical operations, prefer database constraints, atomic updates, idempotency keys or appropriate locking over in-memory checks.

## Error Handling

Check that:

* Errors are not silently ignored.
* User-facing errors are meaningful but do not expose internals.
* Logs retain enough context for diagnosis.
* Sensitive values are not logged.
* Partial writes are rolled back.
* Cleanup occurs during errors.
* Retries are bounded.
* Permanent errors are not retried.
* Background failures are observable.
* Client code handles non-success responses.
* Error handling does not convert every failure into the same status code.

## Performance Review

Report performance concerns only when the code provides evidence.

Check for:

* N+1 queries.
* Unbounded database queries.
* Missing pagination.
* Entire files loaded into memory.
* Repeated expensive parsing.
* Duplicate API calls.
* Sequential independent network calls.
* Large values serialized unnecessarily.
* Expensive work during every render.
* Unbounded loops or recursion.
* Missing indexes for newly introduced frequent filters.
* Long database transactions.
* CPU-heavy work inside the web request lifecycle.
* Excessive model or external API calls.

Do not recommend caching until correctness, invalidation and data isolation are understood.

## Test Review

Check whether tests cover:

* Normal success.
* Invalid input.
* Authentication failure.
* Authorization failure.
* Empty data.
* Database or external-service failure.
* Transaction rollback.
* Duplicate request.
* Boundary values.
* New enum or status values.
* Existing behavior likely to regress.

Tests should validate externally observable behavior rather than internal implementation details.

Do not demand tests for trivial declarations or purely mechanical changes unless risk justifies them.

## Required Finding Format

Use this exact structure:

```text
[Severity] Concise finding title

Location:
path/to/file.ts:line-range

Problem:
Describe the defect and the realistic conditions that trigger it.

Impact:
Describe the incorrect behavior or risk.

Recommended fix:
Describe the smallest safe correction.

Verification:
Describe the regression test or command that confirms the fix.
```

Findings should be ordered by severity, then by importance.

## Review Summary

After findings, provide:

```text
Review summary

Verdict:
- Approve
- Approve with minor changes
- Request changes
- Unable to verify

Findings:
- Blocker:
- High:
- Medium:
- Low:

Verification performed:
- Commands or tests executed.

Not verified:
- Relevant areas that could not be tested or inspected.
```

Do not approve when unresolved Blocker or High findings remain.

Do not claim that tests passed unless they were actually executed.

## Review Versus Modification

By default, a code review should not edit files.

Only modify code when the user explicitly asks to:

* fix findings
* address review comments
* implement corrections
* update tests

When modifying:

* Keep the patch focused.
* Preserve unrelated user changes.
* Add regression tests.
* Run focused checks first.
* Report remaining failures honestly.
