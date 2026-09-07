---

name: production-readiness
description: Assess whether Python, FastAPI, Next.js, TypeScript and PostgreSQL applications are ready for safe production deployment.
license: MIT
compatibility: opencode
metadata:
  category: production-readiness
  stack: cross-stack
  version: "1.0.0"
orchestration:
  lead_for:
    - production-release
  support_for:
    - refactor
  conflicts_with:
    - security-review
---

# Production Readiness

Use this skill before deploying a feature, service, release, migration or major configuration change to production.

The objective is to detect operational, reliability, security and maintainability gaps that could cause production incidents.

Production readiness is not established only because the application builds or tests pass.

## Assessment Principles

* Inspect the actual repository and deployment configuration.
* Identify the application's runtime, dependencies and infrastructure.
* Distinguish release blockers from recommended improvements.
* Do not assume infrastructure controls exist unless documented or visible.
* Do not expose secrets while inspecting configuration.
* Do not make destructive production changes automatically.
* Prefer repository-specific commands over generic assumptions.
* Confirm package versions before applying framework-specific recommendations.

## Readiness Levels

Classify the release as:

* Ready: no known release blockers; required checks passed.
* Conditionally ready: deployable after explicitly listed conditions are completed.
* Not ready: one or more release blockers remain.
* Unable to determine: essential configuration, infrastructure or verification is unavailable.

## Release Blockers

Treat these as potential blockers:

* Known Critical or High security vulnerability.
* Authentication or authorization bypass.
* Destructive migration without a safe plan.
* No rollback path for a high-risk release.
* Application does not build or start.
* Critical tests fail.
* Required environment variables are undefined.
* Secrets are committed or exposed.
* Data writes are non-atomic where consistency is required.
* Background jobs can duplicate critical operations.
* No health check for an orchestrated service.
* Production debug mode enabled.
* Production service uses development server settings.
* Unbounded resource consumption on public endpoints.
* Deployment changes cannot be observed or diagnosed.
* Database schema and application code are incompatible.
* A release requires unavailable infrastructure or credentials.

Use judgment based on impact and deployment context.

## 1. Application Configuration

Check:

* Production and development settings are separated.
* Environment variables are validated at startup.
* Required variables fail fast with clear errors.
* Optional variables have safe defaults.
* Secrets are not hardcoded.
* Debug mode is disabled.
* Logging level is appropriate.
* Allowed hosts and trusted origins are explicit.
* CORS origins are explicit.
* Public and private environment variables are separated.
* External service URLs use the intended environment.
* Timezone handling is explicit and consistent.
* Feature flags have known defaults.
* Configuration changes are documented.

For Next.js, verify that private secrets are not prefixed with `NEXT_PUBLIC_`.

## 2. Build and Dependency Verification

Identify and run the project's configured commands.

Typical checks may include:

### Python

```bash
ruff check .
ruff format --check .
mypy .
pyright
pytest
```

### Next.js and TypeScript

```bash
npm run lint
npm run typecheck
npm test
npm run build
```

Use `pnpm`, `yarn`, `bun` or another package manager when the repository indicates it.

Check:

* Lockfile exists.
* CI uses the same package manager.
* Runtime versions are pinned or constrained.
* Dependencies install reproducibly.
* Production dependencies are separated appropriately.
* Build output is not dependent on uncommitted local files.
* Generated files required at runtime are included.
* Native system dependencies are documented.
* Vulnerability scanning is available and reviewed.

Do not change dependency versions solely to make a readiness report look clean.

## 3. FastAPI Runtime Readiness

Check:

* The service runs behind a production-capable ASGI server.
* Worker count matches workload and infrastructure.
* Startup and shutdown hooks work correctly.
* Database engines and clients are initialized once per process when appropriate.
* Request-scoped resources are closed.
* Blocking work does not run directly in the async event loop.
* Long-running work is moved to a job system when appropriate.
* Request timeouts exist at the proxy or application level.
* Request body and upload size limits exist.
* Streaming responses retain required resources until completion.
* Background task failures are observable.
* OpenAPI documentation exposure is intentional.
* Internal exception details are hidden.
* Graceful shutdown allows in-flight operations to finish where possible.

Do not use `--reload` in production.

## 4. Next.js Runtime Readiness

Check:

* `npm run build` or equivalent succeeds.
* The application starts from the generated production build.
* Server-only code remains server-only.
* Environment variables required during build versus runtime are understood.
* Authentication works across server components, route handlers and client transitions.
* Caching behavior is intentional.
* User-specific responses cannot be shared across users through caching.
* Dynamic routes and fallback behavior are tested.
* Error boundaries and not-found states exist where appropriate.
* Loading and empty states are implemented.
* Image and asset domains are configured.
* API URLs target the production backend.
* Source maps and error reporting behavior are intentional.
* Middleware behavior is tested in the deployment runtime.
* Static assets and generated routes are included in the deployment package.

## 5. Database Readiness

Check:

* Application models match the production schema.
* Migrations are committed.
* Migrations were tested against representative data.
* Upgrade order is compatible with running application versions.
* Downgrade or forward-fix strategy exists.
* Long-running locks are understood.
* Large table rewrites are avoided or scheduled safely.
* New non-null columns have safe migration sequencing.
* New indexes account for production table size and locking behavior.
* Unique constraints account for existing duplicate data.
* Data backfills are restartable and observable.
* Database credentials have minimum necessary privileges.
* Connection pool size matches database limits and process count.
* `pool_pre_ping` or equivalent is configured when infrastructure drops idle connections.
* Transaction failures cause rollback or session disposal.
* Read-modify-write operations are safe under concurrency.
* Backup and restore procedures exist for high-risk migrations.

Calculate total possible database connections:

```text
application instances
× workers per instance
× pool size
+ overflow
+ background workers
+ administrative connections
```

Do not configure each process as though it is the only database client.

## 6. API Readiness

Check:

* API contracts are documented or discoverable.
* Request and response schemas are stable.
* Breaking changes are coordinated.
* Authentication and authorization are server-side.
* Error responses have consistent shape.
* Pagination exists for collections.
* Maximum page sizes are enforced.
* Expensive endpoints have rate or quota controls.
* Request IDs or correlation IDs are available.
* Duplicate critical requests are handled safely.
* Idempotency exists for retryable creation, token deduction, payment, submission or job-start operations.
* External API calls have timeouts.
* Retries are bounded and limited to safe operations.
* Circuit breaking or graceful degradation exists where justified.
* Webhooks verify signatures and resist replay.
* File endpoints validate content, size and authorization.

## 7. Background Jobs and Scheduled Tasks

Check:

* Jobs create their own database sessions.
* Jobs do not depend on request-scoped objects.
* Jobs are idempotent or deduplicated.
* Retry limits exist.
* Retry delays or backoff exist.
* Permanent errors are not retried indefinitely.
* Job state is persisted when required.
* Failures are logged and observable.
* Dead-letter or failed-job handling exists.
* Multiple workers cannot process the same critical job unintentionally.
* Scheduled tasks cannot overlap unexpectedly.
* Partial completion can resume safely.
* Shutdown does not silently lose accepted work.
* User-facing status reflects actual background processing state.

In-process FastAPI background tasks are not a substitute for a durable queue when work must survive process restarts.

## 8. Security Readiness

Check:

* Authentication and authorization flows are tested.
* Secrets are stored outside source control.
* TLS is enforced.
* Cookies use appropriate security attributes.
* CORS is restricted.
* CSRF protection exists where required.
* Inputs are validated.
* File uploads are constrained.
* SQL queries are parameterized.
* Sensitive logs are redacted.
* Rate limiting protects abuse-prone endpoints.
* Dependency vulnerabilities are reviewed.
* Containers run with minimum privilege.
* Production databases and caches are not publicly exposed.
* Administrative endpoints are protected.
* Default accounts and credentials are removed.
* External callbacks and redirects use allowlists.
* AI tools cannot perform unnecessary destructive operations.

Use the `security-review` skill for a deeper security assessment.

## 9. Observability

Check whether operators can determine:

* Is the service running?
* Is it accepting traffic?
* Is it processing requests successfully?
* Is it connected to required dependencies?
* Are errors increasing?
* Are requests slow?
* Are jobs failing?
* Is the database pool exhausted?
* Are external providers failing?
* Which release introduced the issue?

Recommended signals:

* Structured application logs.
* Request or correlation IDs.
* Error tracking.
* Request latency.
* Request count.
* Error rate.
* Worker and queue metrics.
* Database pool metrics.
* External API latency and failures.
* CPU and memory usage.
* Disk usage where relevant.
* Deployment version or commit SHA.
* Health and readiness endpoints.

Never log:

* Passwords.
* Access tokens.
* Authorization headers.
* Session cookies.
* Private keys.
* Full database URLs.
* Sensitive medical or personal information unless explicitly required and protected.
* Complete uploaded document content by default.

## 10. Health Checks

Separate:

### Liveness

Determines whether the process is functioning and should remain running.

It should usually avoid expensive dependency checks.

### Readiness

Determines whether the instance can safely receive traffic.

It may check essential dependencies with strict timeouts.

Health endpoints should:

* Respond quickly.
* Avoid exposing internal configuration.
* Use appropriate status codes.
* Not perform destructive operations.
* Not overload dependencies when called frequently.
* Distinguish degraded dependency state where useful.

## 11. Reliability and Failure Handling

Check behavior when:

* PostgreSQL disconnects.
* Redis is unavailable.
* An external AI provider times out.
* A request is retried.
* The client disconnects.
* A worker restarts.
* The service receives malformed data.
* Storage is unavailable.
* An upload is too large.
* A background job fails halfway.
* Multiple requests modify the same record.
* Deployment occurs during active requests.
* A feature flag changes.
* Rate or quota limits are reached.

The system should fail predictably, preserve data integrity and provide actionable diagnostics.

## 12. Performance and Capacity

Check:

* Queries are bounded.
* Pagination is enforced.
* Relevant indexes exist.
* N+1 queries are absent from important paths.
* Upload and response sizes are limited.
* CPU-heavy processing is isolated appropriately.
* Memory usage is bounded.
* Database pools respect database limits.
* Worker counts match CPU and workload.
* External service concurrency is controlled.
* AI requests have token, cost and concurrency limits.
* Large files are streamed where appropriate.
* Cache keys include tenant or user boundaries when data is private.
* Cache invalidation is understood.
* Load tests cover critical high-volume paths when justified.

Do not optimize based only on intuition. Use traces, metrics, query plans or profiling evidence.

## 13. Deployment Safety

Check:

* Deployment steps are documented.
* CI gates required checks.
* Build artifacts are immutable.
* Production configuration is injected safely.
* Database migrations run in a controlled stage.
* Application and migration deployment order is defined.
* Rollback steps are documented.
* Previous artifacts remain available.
* Health checks gate traffic.
* Rolling deployment compatibility is considered.
* Feature flags protect high-risk behavior.
* One-time tasks are not run by every replica.
* Deployment identity has minimum required permissions.
* Production smoke tests exist.
* Deployment version is visible in logs or monitoring.

## 14. Rollback Plan

A rollback plan should specify:

1. What triggers rollback.
2. Who or what performs it.
3. How the previous application version is restored.
4. Whether the database schema remains backward-compatible.
5. How irreversible data changes are handled.
6. How jobs created by the new version are handled.
7. How rollback success is verified.

For destructive or irreversible migrations, prefer:

* expand schema
* deploy compatible code
* backfill
* switch reads and writes
* verify
* remove old schema in a later release

## 15. Data Protection

Check:

* Sensitive data is identified.
* Only necessary data is collected.
* Access is restricted.
* Backups are protected.
* Retention rules exist.
* Deletion behavior is defined.
* Logs and analytics avoid unnecessary sensitive content.
* Test environments do not use uncontrolled production data.
* Export and download endpoints enforce authorization.
* Object storage is private by default.
* Signed URLs have limited scope and expiry.
* Medical, academic or personal records have appropriate auditability.

## 16. Documentation and Operations

Ensure documentation includes:

* Local setup.
* Required runtime versions.
* Environment variables without secret values.
* Database migration commands.
* Build and start commands.
* Worker commands.
* Health endpoints.
* External dependencies.
* Deployment procedure.
* Rollback procedure.
* Common failure recovery.
* Ownership or escalation information.
* Scheduled tasks.
* Backup and restore process where applicable.

## Required Output Format

Use this structure:

```text
Production readiness assessment

Status:
Ready | Conditionally ready | Not ready | Unable to determine

Release blockers:
1. ...

High-priority requirements:
1. ...

Recommended improvements:
1. ...

Verification completed:
- command
- result

Verification not completed:
- check
- reason

Deployment sequence:
1. ...

Rollback sequence:
1. ...

Final recommendation:
...
```

For each blocker include:

```text
Title:
Concise blocker name

Evidence:
Relevant file, configuration or failed command.

Risk:
What can happen in production.

Required action:
Specific correction required before release.

Verification:
How to prove the issue is resolved.
```

## Modification Rules

When asked to make the application production-ready:

* Address blockers first.
* Make minimal, reviewable changes.
* Do not rewrite the entire architecture unnecessarily.
* Preserve public behavior where possible.
* Add tests for failure paths.
* Avoid changing production secrets.
* Do not execute production migrations automatically.
* Do not deploy automatically unless explicitly instructed and supported.
* Document new environment variables.
* Update deployment documentation.
* Run the production build and relevant tests.
* Report anything that still requires infrastructure or manual verification.

## Completion Criteria

A readiness assessment is complete only when:

* Build and test status are known.
* Runtime configuration was reviewed.
* Database and migration safety were considered.
* Authentication and authorization were considered.
* Failure handling was considered.
* Background processing was considered.
* Observability and health checks were assessed.
* Deployment and rollback paths were assessed.
* Blockers were clearly separated from improvements.
* Unverified assumptions were disclosed.
