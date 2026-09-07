---
name: python-quality
description: Write, review and refactor production-quality Python code with strong typing, safe error handling, testing, maintainability and clear architecture.
license: MIT
compatibility: opencode
metadata:
  category: language-quality
  stack: python
  version: "1.0.0"
orchestration:
  lead_for:
    - python-cleanup
  support_for:
    - fastapi-feature
    - database-issue
    - refactor
    - structured-output
    - rag-pipeline
    - ai-evaluation
    - model-serving
    - mcp-development
    - multi-agent
    - fine-tuning
  conflicts_with:
    - testing-and-debugging
    - fastapi-backend
---

# Python Quality

Use this skill whenever creating, reviewing, debugging or refactoring Python code.

The objective is to produce code that is correct, readable, testable, maintainable and safe for production use.

## General Principles

* Inspect the existing repository before making changes.
* Follow the project’s current architecture and conventions.
* Prefer the smallest safe change.
* Avoid unrelated refactoring.
* Preserve public behavior unless the requested task requires a breaking change.
* Do not invent modules, settings, database models or APIs that do not exist.
* Confirm the installed Python version before using version-specific syntax.
* Prefer standard-library solutions when they are clear and sufficient.

## Python Version

* Use the project’s configured Python version.
* If no version is defined, assume Python 3.11 or newer only when appropriate.
* Check:

  * `pyproject.toml`
  * `.python-version`
  * `runtime.txt`
  * Dockerfile
  * CI configuration

Do not introduce syntax unsupported by the configured runtime.

## Type Hints

* Add precise type hints to public functions and important internal functions.
* Prefer concrete types over `Any`.
* Use `Protocol`, `TypedDict`, `Literal`, `TypeAlias` or generics when they improve correctness.
* Distinguish between:

  * optional values
  * nullable values
  * empty values
  * missing values
* Avoid unnecessary casts and non-null assumptions.
* Keep annotations aligned with runtime behavior.
* Use modern syntax only when the configured Python version supports it.

Examples:

```python
def get_user(user_id: UUID) -> User | None:
    ...
```

```python
def process_items(items: Sequence[str]) -> list[str]:
    ...
```

Avoid:

```python
def process(data: Any) -> Any:
    ...
```

unless the boundary genuinely requires dynamic input.

## Function Design

* Keep functions focused on one responsibility.
* Prefer descriptive names.
* Avoid deeply nested conditionals.
* Use early returns when they improve clarity.
* Avoid large parameter lists.
* Group related parameters into typed objects when appropriate.
* Do not create abstractions before repeated patterns are clear.
* Avoid hidden side effects.
* Make mutating behavior explicit.
* Return consistent types.

## Data Structures

* Prefer:

  * dataclasses
  * Pydantic models
  * enums
  * typed dictionaries
  * immutable tuples or frozen dataclasses where appropriate
* Avoid passing loosely structured dictionaries across many layers.
* Use sets for membership checks when order is irrelevant.
* Avoid mutable global state.
* Avoid mutable default arguments.

Never write:

```python
def add_item(item: str, items: list[str] = []):
    items.append(item)
    return items
```

Use:

```python
def add_item(item: str, items: list[str] | None = None) -> list[str]:
    result = [] if items is None else list(items)
    result.append(item)
    return result
```

## Error Handling

* Catch only exceptions that can be handled meaningfully.
* Never silently swallow errors.
* Avoid broad `except Exception` unless:

  * the error is logged
  * cleanup is required
  * the error is converted intentionally
  * the original context is preserved
* Preserve traceback context using `raise` or exception chaining.
* Use domain-specific exceptions for business rules.
* Do not expose internal exception details to external users.
* Ensure cleanup occurs on failure.
* Use `finally` or context managers where appropriate.

Prefer:

```python
try:
    result = client.fetch()
except TimeoutError as exc:
    raise ExternalServiceUnavailable("Provider timed out") from exc
```

Avoid:

```python
try:
    result = client.fetch()
except Exception:
    return None
```

## Logging

* Use the project’s configured logger.
* Prefer structured context.
* Include identifiers useful for tracing:

  * request ID
  * job ID
  * user ID
  * entity ID
* Do not log:

  * passwords
  * access tokens
  * authorization headers
  * session cookies
  * private keys
  * full database URLs
  * sensitive personal or medical data
* Do not use `print()` for production diagnostics.
* Avoid logging the same exception repeatedly across layers.

Example:

```python
logger.exception(
    "Failed to process assignment",
    extra={"assignment_id": str(assignment_id)},
)
```

## File and Resource Handling

* Use context managers for:

  * files
  * locks
  * temporary resources
  * database transactions where supported
* Prefer `pathlib.Path`.
* Validate paths before reading or writing.
* Avoid path traversal.
* Remove temporary files when no longer needed.
* Stream large files instead of loading them fully into memory.
* Set explicit encoding for text files.

Example:

```python
from pathlib import Path

content = Path(file_path).read_text(encoding="utf-8")
```

## Async Code

* Use `async` only when asynchronous work is performed.
* Do not call blocking I/O directly inside async functions.
* Do not use `time.sleep()` inside async functions.
* Use `asyncio.sleep()` for non-blocking delays.
* Avoid mixing sync and async clients accidentally.
* Ensure tasks are awaited or intentionally scheduled.
* Avoid unbounded task creation.
* Add timeouts to external operations.
* Handle cancellation correctly.
* Do not suppress `CancelledError` unintentionally.

## Concurrency

Check for:

* shared mutable state
* race conditions
* duplicate execution
* lost updates
* unsafe file writes
* unsafe cache updates
* unbounded thread or task creation
* non-idempotent retry behavior

Prefer database constraints, atomic operations or proper locking over in-memory checks.

## Retry Logic

* Retry only transient failures.
* Set a maximum number of attempts.
* Use delay or exponential backoff where appropriate.
* Add jitter for distributed systems.
* Do not retry:

  * validation failures
  * authorization failures
  * permanent business-rule failures
  * non-idempotent operations without protection
* Consider whether a previous commit or external request may already have succeeded.
* Log final failure with useful context.

## Configuration

* Use environment variables or typed settings classes.
* Validate required settings at startup.
* Never hardcode:

  * credentials
  * API keys
  * database URLs
  * private endpoints
* Separate development, test and production configuration.
* Keep safe defaults.
* Document new environment variables.
* Avoid reading environment variables throughout business logic; centralize configuration.

## Security

Check for:

* unsafe `eval` or `exec`
* unsafe deserialization
* shell injection
* path traversal
* insecure temporary files
* SSRF
* secret exposure
* unsafe YAML loading
* unrestricted dynamic imports
* user input passed into SQL or shell commands
* unsafe pickle usage

Avoid:

```python
subprocess.run(user_input, shell=True)
```

Prefer argument lists and allowlists.

## Database Interaction

* Use parameterized SQL or ORM expressions.
* Keep transaction boundaries explicit.
* Roll back failed transactions.
* Do not reuse failed sessions.
* Avoid long-running transactions.
* Handle session lifecycle carefully.
* Avoid N+1 queries.
* Use deterministic ordering for pagination.
* Use database constraints for critical invariants.
* Do not trust application-only uniqueness checks under concurrency.

## Testing

Add or update tests for:

* expected success
* invalid input
* empty input
* boundary values
* error handling
* external dependency failure
* duplicate execution
* rollback behavior
* timezone behavior
* async behavior
* regression scenarios

Prefer tests that validate observable behavior.

Avoid:

* excessive mocking
* tests tied to implementation details
* disabling failing tests
* arbitrary sleeps
* tests that depend on execution order

## Documentation

* Add docstrings where behavior is not obvious.
* Document public APIs.
* Explain why, not what.
* Avoid comments that duplicate the code.
* Update documentation when behavior, configuration or commands change.
* Include examples for complex public interfaces.

## Performance

Do not optimize without evidence.

Check for:

* repeated parsing
* repeated database queries
* unbounded loops
* large in-memory objects
* inefficient membership checks
* synchronous work inside async paths
* unnecessary serialization
* repeated model loading
* repeated network clients
* excessive copying

Use profiling, metrics or benchmarks before large optimizations.

## Verification

Inspect the repository and use its configured commands.

Typical commands:

```bash
ruff check .
ruff format --check .
mypy .
pyright
pytest
```

Run focused tests first.

Examples:

```bash
pytest tests/test_service.py -q
```

```bash
pytest tests/test_service.py::test_specific_case -q
```

Then run the broader suite when appropriate.

## Completion Criteria

A Python task is complete only when:

* behavior is correct
* types are consistent
* errors are handled intentionally
* resources are cleaned up
* sensitive values are protected
* relevant tests pass
* formatting and linting pass
* changes stay within scope
* any remaining limitation is reported honestly
