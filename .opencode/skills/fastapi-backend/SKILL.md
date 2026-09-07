---

name: fastapi-backend
description: Build, review and debug production FastAPI services, including routing, validation, authentication, SQLAlchemy, background tasks, streaming and external integrations.
license: MIT
compatibility: opencode
metadata:
  category: backend
  stack: fastapi
  version: "1.0.0"
orchestration:
  lead_for:
    - fastapi-feature
  support_for:
    - bug-fix
    - database-issue
    - refactor
    - code-review
    - security-review
  conflicts_with:
    - sqlalchemy-postgres
    - python-quality
---

# FastAPI Backend

Use this skill whenever implementing, reviewing, debugging or refactoring a FastAPI backend.

The objective is to produce reliable, secure, testable and production-ready API behavior.

## Initial Inspection

Before changing code:

1. Inspect the repository structure.
2. Read project-level `AGENTS.md`.
3. Inspect:

   * `pyproject.toml`
   * `requirements.txt`
   * dependency lockfiles
   * application entry point
   * router registration
   * database setup
   * settings
   * authentication dependencies
4. Determine:

   * FastAPI version
   * Pydantic version
   * SQLAlchemy version
   * sync or async database usage
   * worker and deployment model
5. Find existing patterns and follow them.

Do not assume current framework APIs without checking installed versions.

## Architecture

Prefer clear separation:

```text
routers/
schemas/
models/
services/
repositories/
dependencies/
core/
workers/
tests/
```

Use the repository’s existing structure rather than forcing this layout.

General responsibilities:

* Router: HTTP concerns
* Schema: validation and serialization
* Service: business logic
* Repository: database access when the project uses this layer
* Model: database representation
* Dependency: shared request-scoped resources
* Worker: durable background processing

Keep route handlers thin.

## Route Handlers

A route handler should primarily:

1. receive validated input
2. resolve dependencies
3. call business logic
4. return a response

Avoid embedding large business workflows directly inside routes.

Example:

```python
@router.post(
    "/assignments",
    response_model=AssignmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_assignment(
    payload: AssignmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher),
) -> AssignmentResponse:
    return assignment_service.create(
        db=db,
        payload=payload,
        actor=current_user,
    )
```

## Request Validation

* Define explicit Pydantic request models.
* Validate:

  * ranges
  * lengths
  * enums
  * identifiers
  * date relationships
  * file sizes
  * optional versus required fields
* Do not trust frontend validation.
* Use field and model validators for cross-field rules.
* Reject invalid data before business logic.
* Avoid accepting unrestricted dictionaries unless required.
* Normalize input only when normalization is intentional.

## Response Models

* Define explicit response models.
* Return only fields needed by the client.
* Do not expose:

  * password hashes
  * internal tokens
  * private metadata
  * database credentials
  * unrestricted internal JSON
* Keep response shape stable.
* Distinguish between:

  * omitted
  * `null`
  * empty list
  * empty object
* Check ORM serialization settings for the installed Pydantic version.

## Status Codes

Use status codes intentionally:

* `200 OK` for successful read or update
* `201 Created` for resource creation
* `202 Accepted` when durable asynchronous processing has been accepted
* `204 No Content` when no response body is needed
* `400 Bad Request` for malformed business requests
* `401 Unauthorized` for missing or invalid authentication
* `403 Forbidden` for insufficient permission
* `404 Not Found` for inaccessible or nonexistent resource
* `409 Conflict` for duplicate or state conflicts
* `422 Unprocessable Entity` for validation failures
* `429 Too Many Requests` for rate or quota limits
* `500 Internal Server Error` for unexpected failures
* `503 Service Unavailable` for temporary dependency failure

Do not return `200` for failed operations.

## Authentication

Check:

* token signature
* expiry
* issuer
* audience
* revocation where applicable
* session validity
* user activity status

Do not trust:

* user ID from request body
* role from frontend
* branch ID from query parameters
* organization ID from client state

Resolve identity from validated authentication.

## Authorization

Authorization must be checked server-side for each resource.

Verify:

* role
* permission
* ownership
* organization
* branch
* classroom
* assignment
* participant relationship
* tenant boundary

A user being authenticated does not mean they can access every record.

Avoid:

```python
record = db.get(Record, record_id)
return record
```

Prefer:

```python
record = (
    db.query(Record)
    .filter(
        Record.id == record_id,
        Record.branch_id == current_user.branch_id,
    )
    .first()
)
```

## Dependency Injection

Use dependencies for:

* database sessions
* authentication
* authorization
* shared clients
* configuration
* reusable validation
* request context

Dependencies should:

* have clear lifecycle
* clean up resources
* avoid hidden writes
* avoid expensive initialization per request
* expose typed results

Do not create new database engines or external clients inside every route.

## Database Sessions

Determine whether the application uses:

* sync SQLAlchemy
* async SQLAlchemy

Do not mix them.

Request-scoped session rules:

* one session per request
* commit only when appropriate
* rollback on failure
* close after request
* do not reuse after failed transaction
* do not pass into durable background work
* do not keep open during long network calls unless necessary

Example sync dependency:

```python
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

For service-level writes:

```python
try:
    db.add(entity)
    db.commit()
    db.refresh(entity)
except Exception:
    db.rollback()
    raise
```

## Transaction Boundaries

Use a single transaction when operations must succeed or fail together.

Examples:

* create assignment and questions
* deduct token and create history entry
* submit exam and update participant status
* create job and reserve quota

Do not commit halfway through a logically atomic workflow unless intentionally designed.

Use database constraints for critical invariants.

## Handling Broken Connections

For transient database disconnects:

* enable `pool_pre_ping` where appropriate
* use sensible `pool_recycle`
* discard invalid connections
* rollback failed sessions
* create a fresh session for retry
* retry only safe operations
* limit retry count
* consider whether the original commit may have succeeded

Do not continue using the same failed session.

## Async Rules

* Do not mark routes async unless dependencies support async behavior.
* Do not run blocking:

  * SQLAlchemy sync queries
  * file parsing
  * CPU-heavy processing
  * synchronous HTTP calls
    directly in the event loop.
* Use async clients with async routes.
* Use threadpool helpers for unavoidable synchronous work.
* Add timeouts to external operations.
* Avoid unbounded `asyncio.gather`.
* Handle cancellation.

Do not mix async route handlers with a synchronous database session without understanding the blocking impact.

## Background Tasks

FastAPI `BackgroundTasks` is suitable only for short, non-critical work that may be lost if the process restarts.

Do not use it for critical work such as:

* financial operations
* token deduction
* large PDF processing
* long AI generation
* durable notifications
* exam evaluation
* production media processing

For durable work, prefer a queue or worker system.

Background jobs must:

* create their own database session
* not reuse request-scoped dependencies
* be idempotent
* have retry limits
* record status
* expose failure state
* handle process restart
* avoid duplicate execution

## Streaming Responses

Check resource lifetime carefully.

For sync generators inside async routes, use appropriate threadpool iteration when required by the project.

Ensure:

* database session remains valid if generator needs it
* file handles remain open during streaming
* client disconnect is handled
* exceptions are logged
* output format remains valid
* response headers are set correctly

Do not close resources before the generator finishes.

## File Uploads

Validate:

* file size
* MIME type
* actual content where possible
* extension
* filename
* authorization
* storage path

Use generated server-side filenames.

Prevent:

* path traversal
* executable upload
* decompression bombs
* oversized PDFs
* malicious SVG or HTML
* public exposure of private files

Stream large files rather than reading everything into memory.

## External APIs

For every external service:

* set connect and read timeouts
* handle non-success status codes
* validate response shape
* bound retries
* avoid logging secrets
* use pooled clients
* handle provider rate limits
* record failures
* provide graceful fallback where appropriate

Do not create a new HTTP client for every request if a reusable client is appropriate.

## Error Handling

Use centralized exception handling where useful.

Separate:

* validation errors
* domain errors
* authentication errors
* authorization errors
* conflicts
* dependency failures
* unexpected errors

Do not return raw exception strings.

Bad:

```python
except Exception as exc:
    raise HTTPException(status_code=500, detail=str(exc))
```

Better:

```python
except ExternalProviderError as exc:
    logger.exception("Provider request failed")
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="External service is temporarily unavailable.",
    ) from exc
```

## Logging

Log:

* request ID
* user ID
* relevant entity ID
* operation
* error category
* duration where useful

Do not log:

* passwords
* access tokens
* authorization headers
* full request bodies containing sensitive information
* medical records
* uploaded document content
* database URLs

Avoid duplicate logging across layers.

## Pagination and Query Limits

Every collection endpoint should consider:

* pagination
* maximum page size
* deterministic ordering
* filtering allowlists
* search limits
* authorization filters
* query cost

Avoid unbounded `.all()` on large tables.

## Idempotency

Critical operations should resist duplicates caused by:

* user double-click
* browser retry
* reverse proxy retry
* worker retry
* network timeout
* duplicate webhook
* repeated submission

Use:

* idempotency keys
* unique constraints
* atomic updates
* status checks
* row locking where justified

In-memory flags are not sufficient across multiple workers.

## Security

Check:

* authentication
* object-level authorization
* mass assignment
* CORS
* CSRF
* SQL injection
* SSRF
* file upload security
* rate limits
* secret exposure
* sensitive logs
* open redirects
* unsafe HTML
* unbounded AI usage
* webhook verification

Use the `security-review` skill for deeper review.

## Testing

Add tests for:

* successful request
* invalid payload
* missing authentication
* insufficient permission
* resource not found
* tenant boundary
* duplicate request
* transaction rollback
* database failure
* external provider timeout
* background job creation
* response schema
* status code
* file-size limits
* pagination boundaries

Prefer API-level tests for behavior and focused service tests for business logic.

## Verification

Use project-configured commands.

Typical checks:

```bash
ruff check .
ruff format --check .
mypy .
pyright
pytest
```

For focused testing:

```bash
pytest tests/api/test_assignments.py -q
```

Also verify:

* application imports successfully
* migrations align with models
* OpenAPI generation succeeds
* startup and shutdown hooks work
* changed endpoint works against the expected client contract

## Completion Criteria

A FastAPI task is complete only when:

* input is validated
* response schema is explicit
* authentication and authorization are correct
* transactions are safe
* session lifecycle is correct
* async and blocking behavior are appropriate
* failures are observable
* tests cover the changed behavior
* lint, type checks and focused tests pass
* remaining risks are disclosed
