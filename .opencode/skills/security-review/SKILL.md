---
name: security-review
description: Review Python, FastAPI, SQLAlchemy, Next.js, TypeScript and JavaScript code for security vulnerabilities, authorization flaws and unsafe data handling.
license: MIT
compatibility: opencode
metadata:
  category: security
  stack: cross-stack
  version: "1.0.0"
orchestration:
  lead_for:
    - security-review
  support_for:
    - fastapi-feature
    - nextjs-feature
    - structured-output
    - rag-pipeline
    - injection-defense
  conflicts_with:
    - code-review
    - production-readiness
---

# Security Review

Use this skill when reviewing code, APIs, authentication, database operations, file handling, external integrations, deployment configuration or infrastructure changes.

The objective is to identify realistic security risks without inventing hypothetical vulnerabilities unsupported by the code.

## Review Principles

* Inspect the actual implementation before making claims.
* Trace untrusted input from entry point to storage, execution or output.
* Prioritize exploitable issues over theoretical concerns.
* Do not report a vulnerability solely because a security control is not visible in the current file.
* Check related middleware, dependencies, schemas, service functions and configuration before concluding that a control is missing.
* Distinguish confirmed vulnerabilities from risks requiring further verification.
* Never expose real secrets, tokens, passwords, connection strings or personal data in the review output.

## Severity Levels

Classify each confirmed issue as:

* Critical: likely to cause complete system compromise, unrestricted data access, remote code execution or major credential exposure.
* High: likely to allow unauthorized access, privilege escalation, sensitive data disclosure or serious business-impacting abuse.
* Medium: requires specific conditions or has limited scope but still creates meaningful risk.
* Low: defense-in-depth weakness, limited information disclosure or minor security misconfiguration.
* Informational: improvement that does not represent a confirmed vulnerability.

Do not inflate severity.

## Authentication Review

Check for:

* Missing authentication on protected endpoints.
* Incorrect use of optional authentication.
* Token verification without signature, issuer, audience or expiry validation.
* Trusting user IDs, roles or permissions sent by the client.
* Authentication state stored insecurely in browser storage.
* Session fixation or missing session invalidation.
* Password reset tokens that are reusable, predictable or never expire.
* Account enumeration through error messages.
* Missing rate limiting on login, password reset, OTP or verification endpoints.
* Long-lived access tokens without appropriate rotation or revocation.
* Tokens included in URLs, logs or analytics events.

For cookie-based authentication, check:

* `HttpOnly`
* `Secure`
* appropriate `SameSite`
* expiry
* CSRF protection where required

## Authorization Review

Authentication does not imply authorization.

Check:

* Object-level authorization on every resource lookup.
* Tenant, branch, organization, classroom or user boundaries.
* Role and permission checks on privileged operations.
* Indirect object reference vulnerabilities.
* Mass assignment of protected properties.
* Admin-only functionality exposed through ordinary endpoints.
* Ownership validation before read, update, delete, download or submission.
* Background tasks that execute without preserving the correct authorization context.

Never trust identifiers supplied by the frontend without server-side authorization.

## FastAPI and Python Review

Check for:

* Missing request validation.
* Unsafe use of `eval`, `exec`, `pickle`, `marshal`, `yaml.load` or dynamic imports.
* Shell commands built from user-controlled strings.
* `subprocess` calls using `shell=True`.
* Path traversal in file reads, writes, extraction or download endpoints.
* Unsafe temporary-file handling.
* Uploaded files trusted only by extension or client-provided MIME type.
* Unbounded file uploads or request bodies.
* Server-side request forgery through user-provided URLs.
* Open redirects.
* Internal exception details returned to clients.
* Debug mode enabled in production.
* Sensitive data written to application logs.
* Insecure CORS configuration, especially credentials with broad origins.
* Blocking operations inside async endpoints.
* Background jobs reusing request-scoped database sessions.
* Race conditions in balance, token, quota, assignment or submission operations.
* Missing idempotency for retried financial or resource-consuming operations.

## SQLAlchemy and Database Review

Check for:

* Raw SQL assembled through string interpolation.
* Dynamic table, column, ordering or filtering values without allowlists.
* Missing tenant or ownership filters.
* Excessive database privileges.
* Sensitive fields returned unnecessarily.
* Passwords or tokens stored in plaintext.
* Failed transactions reused without rollback.
* Non-atomic multi-step writes.
* Race conditions caused by read-modify-write logic.
* Missing row locks or database constraints for critical invariants.
* Destructive migrations without backup or rollback planning.
* Production database credentials used in development tools.
* Database MCP access using a write-enabled production account.

Prefer parameterized SQL and ORM expressions.

## Next.js, React and Browser Review

Check for:

* Secrets exposed through `NEXT_PUBLIC_*`.
* Server-only modules imported into client components.
* Authorization performed only in the UI.
* Sensitive values included in rendered HTML or serialized props.
* Unsafe `dangerouslySetInnerHTML`.
* Untrusted URLs assigned to navigation, iframe or media elements.
* Open redirects.
* Missing origin checks for sensitive server actions.
* CSRF risk for cookie-authenticated mutations.
* Access tokens stored unnecessarily in `localStorage`.
* Unvalidated data crossing server/client boundaries.
* Server actions trusting hidden form values.
* Internal API errors displayed directly to users.
* Source maps or debug information exposed in production.

## API Security

Check for:

* Missing input size limits.
* Missing pagination or maximum result limits.
* Unbounded filtering or expensive search requests.
* Mass assignment.
* Replayable requests.
* Duplicate submission or payment processing.
* Missing rate limits for costly AI, file-processing or media endpoints.
* Webhook requests accepted without signature verification.
* Webhook replay protection missing.
* APIs returning fields that the client does not need.
* Sequential identifiers exposing private records.
* Inconsistent authorization across similar endpoints.
* GraphQL or query endpoints allowing excessive complexity.

## File and Document Processing

Check for:

* Path traversal.
* Zip-slip during archive extraction.
* Decompression bombs.
* Unbounded PDF, image, audio or video processing.
* Malicious filenames.
* Executable uploads.
* Uploaded HTML or SVG served from a trusted application origin.
* Inadequate content-type verification.
* Files stored with predictable public URLs.
* Temporary files not removed.
* Metadata containing sensitive information.
* PDF or document parsers processing untrusted files without isolation.

Use generated server-side filenames and explicit size limits.

## AI and LLM Security

Check for:

* Prompt injection from uploaded documents or retrieved webpages.
* Model output passed directly into shell commands, SQL, HTML or code execution.
* Sensitive system prompts or credentials included in model context.
* Retrieval without tenant-level access control.
* Untrusted model output treated as validated JSON.
* Model-generated URLs fetched without allowlists or network restrictions.
* Tools available to the model with unnecessary write or destructive permissions.
* LLM decisions used as the sole authority for access control, grading, financial actions or disciplinary decisions.
* Private user data sent to external providers without explicit policy support.
* Logs containing prompts, medical information or personal data.

Treat model output as untrusted input.

## Secrets and Configuration

Search for:

* API keys.
* Database URLs.
* JWT secrets.
* Private keys.
* Cloud credentials.
* SMTP passwords.
* OAuth client secrets.
* Webhook signing secrets.
* Hardcoded production URLs containing credentials.

Do not print secret values. Report only:

* file path
* approximate location
* secret type
* recommended remediation

Recommend secret rotation when a real secret appears committed or exposed.

## Dependency and Supply-Chain Review

Check:

* Lockfiles are present and used.
* Newly added packages are necessary.
* Package names are correct and not likely typosquatting.
* Install scripts or post-install hooks deserve scrutiny.
* Dependencies are imported from expected packages.
* Git dependencies are pinned to immutable revisions when appropriate.
* Container base images are pinned appropriately.
* Untrusted scripts are not downloaded and piped directly into a shell.
* CI workflows do not execute untrusted pull-request code with privileged secrets.

Do not claim that a dependency is vulnerable without current evidence from an authoritative advisory source or the project’s vulnerability scanner.

## Infrastructure and Deployment

Check:

* Development servers exposed publicly.
* Debug endpoints enabled.
* Containers running as root without need.
* Broad filesystem permissions.
* Publicly exposed databases, Redis, dashboards or object storage.
* Missing TLS verification.
* Insecure reverse-proxy headers.
* Trusting forwarded headers from arbitrary clients.
* Production secrets embedded in images.
* CI logs exposing secrets.
* Overly broad cloud IAM permissions.
* Health endpoints exposing internal details.
* Backups unencrypted or publicly accessible.

## Required Output Format

Present findings in descending severity.

For every confirmed finding include:

1. Title
2. Severity
3. File and location
4. Evidence from the code
5. Exploitation or failure scenario
6. Impact
7. Minimal remediation
8. Verification or regression test

Use the following structure:

```text
[Severity] Finding title

Location:
path/to/file.py:line-range

Evidence:
What the code currently does.

Risk:
How the issue could realistically be exploited or cause harm.

Fix:
The smallest safe remediation.

Verification:
How to test that the vulnerability is resolved.
```

After findings, include:

* Confirmed findings count by severity.
* Items requiring manual verification.
* Security checks or tests executed.
* Areas not reviewed because they were outside the available scope.

## False-Positive Control

Do not report an issue when:

* Input is already validated by a clearly identified upstream control.
* The route is protected by verified middleware or dependency.
* SQL values are parameterized.
* The value is not attacker-controlled.
* The behavior is limited to development-only configuration and cannot enter production.
* The concern is purely stylistic.
* The relevant implementation is unavailable.

When evidence is incomplete, label it:

```text
Needs verification
```

State exactly what must be inspected to confirm it.

## Safe Modification Rules

When asked to fix security issues:

* Make the smallest safe change.
* Preserve public API behavior unless the behavior itself is unsafe.
* Add regression tests.
* Avoid unrelated refactoring.
* Do not weaken validation to preserve broken clients.
* Do not rotate, delete or modify real credentials automatically.
* Do not execute destructive security tests against production systems.
* Do not add a security package unless the existing stack cannot solve the problem cleanly.

## Completion Criteria

A security review is complete only after:

* Relevant entry points were inspected.
* Input-to-sink paths were traced.
* Authentication and authorization were considered separately.
* Secrets and logging were checked.
* Database and transaction behavior were checked where applicable.
* Confirmed findings were separated from unverified concerns.
* Available security tests, linters or scanners were run when appropriate.
