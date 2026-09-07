---

name: sqlalchemy-postgres
description: Build, review, debug and optimize SQLAlchemy and PostgreSQL code, including sessions, transactions, pooling, migrations, concurrency and production reliability.
license: MIT
compatibility: opencode
metadata:
  category: database
  stack: sqlalchemy-postgres
  version: "1.0.0"
orchestration:
  lead_for:
    - database-issue
    - alembic-migration
  support_for:
    - fastapi-feature
    - production-release
    - bug-fix
  conflicts_with:
    - fastapi-backend
---

# SQLAlchemy and PostgreSQL

Use this skill whenever implementing, reviewing, debugging or optimizing SQLAlchemy and PostgreSQL code.

The objective is to produce correct, transaction-safe, concurrency-safe and production-ready database behavior.

## Initial Inspection

Before changing database code:

1. Inspect the repository structure.
2. Read project-level `AGENTS.md`.
3. Inspect:

   * `pyproject.toml`
   * `requirements.txt`
   * lockfiles
   * database configuration
   * engine creation
   * session factory
   * dependency injection
   * ORM models
   * migration files
   * repository and service layers
4. Determine:

   * SQLAlchemy version
   * PostgreSQL version where available
   * sync or async architecture
   * database driver
   * deployment worker count
   * connection-pool configuration
   * migration tool
5. Find existing database patterns before introducing new ones.

Do not assume SQLAlchemy 2.x APIs unless the installed version supports them.

## Supported Architectures

Determine whether the project uses:

### Synchronous SQLAlchemy

Typical components:

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
```

Typical drivers:

```text
psycopg2
psycopg
```

### Asynchronous SQLAlchemy

Typical components:

```python
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
```

Typical drivers:

```text
asyncpg
psycopg async
```

Do not mix:

* sync engine with `AsyncSession`
* async engine with ordinary `Session`
* sync queries inside async code without threadpool handling
* async clients inside synchronous code without a deliberate bridge

## Engine Configuration

Create the engine once per process.

Do not create a new engine:

* for every request
* inside every service call
* inside every repository function
* for every background task

Example synchronous setup:

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_recycle=1800,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)
```

Example asynchronous setup:

```python
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

engine = create_async_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_recycle=1800,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
)
```

Do not copy pool settings blindly. Tune them according to:

* PostgreSQL connection limit
* application instance count
* worker count
* background workers
* expected concurrency
* connection proxy behavior
* database infrastructure timeout

## Connection Pool Sizing

Calculate total possible application connections.

For synchronous applications:

```text
instances
× workers per instance
× (pool_size + max_overflow)
```

Then add:

```text
background workers
scheduled workers
administrative connections
migration connections
monitoring connections
```

Example:

```text
3 instances
× 4 workers
× (5 pool size + 5 overflow)
= 120 possible application connections
```

Do not configure each worker as though it is the only database client.

Leave capacity for:

* database administration
* migrations
* monitoring
* failover
* temporary spikes

## Pool Configuration

Common parameters:

```python
engine = create_engine(
    settings.database_url,
    pool_size=10,
    max_overflow=5,
    pool_timeout=30,
    pool_recycle=1800,
    pool_pre_ping=True,
)
```

Meaning:

* `pool_size`: persistent pooled connections per process
* `max_overflow`: temporary connections beyond the pool size
* `pool_timeout`: maximum wait for a connection
* `pool_recycle`: replace old connections after a configured age
* `pool_pre_ping`: validate connections before checkout

Use `pool_pre_ping=True` when infrastructure may close idle connections.

Do not treat `pool_pre_ping` as a fix for:

* invalid session state
* missing rollback
* transaction bugs
* leaked sessions
* excessive worker count
* incorrectly sized pools

## Session Lifecycle

Use one session per request, task or isolated unit of work.

A session should not be:

* global
* shared between threads
* shared between async tasks
* reused after an unrecoverable database error
* passed from a request into a durable background task
* kept open longer than necessary

Example synchronous dependency:

```python
from collections.abc import Generator
from sqlalchemy.orm import Session

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

Example asynchronous dependency:

```python
from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
```

## Session State

A SQLAlchemy session tracks:

* pending objects
* loaded objects
* transaction state
* connection state
* identity map
* failed transaction state

After a transaction error, the session may remain unusable until rollback.

Do not continue using a failed session without resetting its transaction state.

Example:

```python
try:
    session.add(entity)
    session.commit()
except Exception:
    session.rollback()
    raise
```

For serious connection errors, prefer closing the session and creating a new one.

## Transaction Boundaries

A transaction should represent one logical atomic operation.

Operations that must succeed or fail together should use the same transaction.

Examples:

* create order and reserve inventory
* deduct tokens and create token history
* submit exam and update participant status
* create assignment and insert generated questions
* update balance and create audit record

Avoid:

```python
session.add(parent)
session.commit()

session.add(child)
session.commit()
```

when both writes are logically atomic.

Prefer:

```python
try:
    session.add(parent)
    session.flush()

    child.parent_id = parent.id
    session.add(child)

    session.commit()
except Exception:
    session.rollback()
    raise
```

Use `flush()` when database-generated values are needed before commit.

## Context-Managed Transactions

Where appropriate:

```python
with SessionLocal.begin() as session:
    session.add(entity)
```

Or asynchronously:

```python
async with AsyncSessionLocal.begin() as session:
    session.add(entity)
```

Do not combine automatic transaction context management with manual commits unless the project pattern explicitly requires it.

## Commit Ownership

Define which layer owns the transaction.

Recommended patterns:

### Service-owned transaction

Repository methods perform queries and mutations but do not commit.

```python
def create_user(session: Session, payload: UserCreate) -> User:
    user = User(**payload.model_dump())
    session.add(user)
    session.flush()
    return user
```

Service commits:

```python
def register_user(session: Session, payload: UserCreate) -> User:
    try:
        user = user_repository.create_user(session, payload)
        audit_repository.create_entry(session, user.id)
        session.commit()
        session.refresh(user)
        return user
    except Exception:
        session.rollback()
        raise
```

Avoid hidden commits inside repository methods when several operations must be atomic.

## Rollback Rules

Rollback after:

* `IntegrityError`
* `OperationalError`
* `DataError`
* transaction failure
* failed flush
* failed commit

Example:

```python
from sqlalchemy.exc import IntegrityError

try:
    session.commit()
except IntegrityError as exc:
    session.rollback()
    raise DuplicateRecordError from exc
```

Do not catch an exception and continue using the session without rollback.

## Broken Connection Handling

Common errors include:

```text
SSL connection has been closed unexpectedly
server closed the connection unexpectedly
connection reset by peer
connection already closed
terminating connection due to administrator command
```

When a connection fails:

1. Capture the original exception.
2. Roll back if possible.
3. Close or discard the failed session.
4. Allow the pool to invalidate the broken connection.
5. Create a fresh session before retry.
6. Retry only if the operation is safe.
7. Limit retries.
8. Consider whether the previous commit may already have succeeded.

Do not reuse the same failed session.

## Safe Retry Strategy

Retry only transient failures.

Potentially retryable:

* connection reset
* temporary network failure
* serialization failure
* deadlock
* database restart
* temporary connection exhaustion

Usually not retryable:

* invalid input
* unique constraint violation
* foreign key violation
* authorization failure
* invalid SQL
* missing table or column
* application logic error

Example bounded retry:

```python
import time
from collections.abc import Callable
from typing import TypeVar

from sqlalchemy.exc import OperationalError

T = TypeVar("T")

def run_with_retry(
    operation: Callable[[], T],
    *,
    attempts: int = 3,
    delay_seconds: float = 0.5,
) -> T:
    last_error: OperationalError | None = None

    for attempt in range(attempts):
        try:
            return operation()
        except OperationalError as exc:
            last_error = exc

            if attempt == attempts - 1:
                break

            time.sleep(delay_seconds * (2**attempt))

    assert last_error is not None
    raise last_error
```

The operation must create a fresh session for each attempt.

Do not blindly retry non-idempotent writes.

## Ambiguous Commit Outcomes

A connection may fail after PostgreSQL committed but before the application received confirmation.

This means:

```text
commit may have succeeded
application sees an error
retry may create duplicate data
```

Protect critical operations with:

* idempotency keys
* unique constraints
* deterministic operation IDs
* status checks
* transaction records
* reconciliation logic

Do not assume every failed commit means nothing was written.

## Idempotency

Use idempotency for operations such as:

* token deduction
* payment processing
* exam submission
* job creation
* AI generation requests
* webhook processing
* notification dispatch
* resource creation triggered by retries

Example model concept:

```python
class Operation(Base):
    __tablename__ = "operations"

    idempotency_key: Mapped[str] = mapped_column(
        String,
        unique=True,
        nullable=False,
    )
```

Use a unique database constraint, not only an application-level lookup.

## Concurrency Safety

Check for read-modify-write patterns.

Unsafe:

```python
account = session.get(Account, account_id)
account.balance -= amount
session.commit()
```

Concurrent requests may overwrite each other.

Prefer atomic updates:

```python
from sqlalchemy import update

result = session.execute(
    update(Account)
    .where(
        Account.id == account_id,
        Account.balance >= amount,
    )
    .values(balance=Account.balance - amount)
)

if result.rowcount != 1:
    raise InsufficientBalanceError
```

Then commit within the transaction.

## Row Locking

Use row-level locking when a business operation requires exclusive access.

```python
from sqlalchemy import select

account = session.execute(
    select(Account)
    .where(Account.id == account_id)
    .with_for_update()
).scalar_one()
```

Use carefully because row locks can:

* block concurrent transactions
* increase latency
* cause deadlocks
* reduce throughput

Keep locked transactions short.

Do not call slow external APIs while holding database locks.

## Optimistic Concurrency

For records edited concurrently, consider version columns.

```python
class Document(Base):
    __tablename__ = "documents"

    version_id: Mapped[int] = mapped_column(nullable=False)

    __mapper_args__ = {
        "version_id_col": version_id,
    }
```

Use optimistic concurrency when conflicts are uncommon and blocking is undesirable.

## Isolation Levels

Understand common PostgreSQL isolation levels:

* Read Committed
* Repeatable Read
* Serializable

PostgreSQL defaults to Read Committed.

Do not raise isolation level globally without understanding the performance and retry implications.

Use Serializable only when:

* correctness requires it
* conflicts are handled
* transaction retries are implemented

## Deadlocks

Deadlocks can occur when transactions lock resources in inconsistent order.

Reduce deadlocks by:

* updating tables in consistent order
* locking rows in consistent order
* keeping transactions short
* avoiding unnecessary locks
* avoiding external calls inside transactions
* adding bounded retry for confirmed deadlock errors

Do not hide persistent deadlocks with unlimited retries.

## ORM Models

Use SQLAlchemy 2-style typing when supported:

```python
from sqlalchemy.orm import Mapped, mapped_column

class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(
        String(320),
        unique=True,
        nullable=False,
    )
```

Ensure ORM definitions match database schema:

* nullability
* type
* length
* default
* server default
* index
* uniqueness
* foreign key
* cascade behavior
* enum values

Do not rely only on Python defaults when the database must enforce a default.

## Relationships

Configure relationships deliberately.

Check:

* lazy loading
* eager loading
* cascade
* delete behavior
* orphan behavior
* nullable foreign keys
* back references

Example:

```python
children: Mapped[list["Child"]] = relationship(
    back_populates="parent",
    cascade="all, delete-orphan",
)
```

Do not add destructive cascade settings without understanding data-loss impact.

## Foreign Key Deletion Behavior

Application-level cascade and database-level cascade are different.

Database example:

```python
ForeignKey("parents.id", ondelete="CASCADE")
```

ORM example:

```python
relationship(
    passive_deletes=True,
)
```

Ensure model, migration and database behavior agree.

## Query Design

Prefer SQLAlchemy expressions over interpolated SQL.

Example:

```python
stmt = select(User).where(User.email == email)
user = session.execute(stmt).scalar_one_or_none()
```

Avoid:

```python
query = f"SELECT * FROM users WHERE email = '{email}'"
```

For raw SQL, use parameters:

```python
from sqlalchemy import text

stmt = text("SELECT * FROM users WHERE email = :email")
result = session.execute(stmt, {"email": email})
```

## Dynamic Query Parameters

User-controlled values for:

* table names
* column names
* sort fields
* sort direction
* SQL functions

cannot be parameterized in the same way as ordinary values.

Use explicit allowlists:

```python
SORT_FIELDS = {
    "created_at": User.created_at,
    "email": User.email,
}

sort_column = SORT_FIELDS.get(sort_by)

if sort_column is None:
    raise InvalidSortFieldError
```

## Query Result APIs

Use the correct result method:

* `scalar_one()`: exactly one result
* `scalar_one_or_none()`: zero or one
* `scalars().all()`: collection of ORM entities
* `first()`: first result or none
* `one()`: exactly one row
* `one_or_none()`: zero or one row

Do not use `.first()` when duplicates should be treated as a data-integrity error.

## Pagination

Use deterministic ordering.

Unsafe:

```python
select(User).limit(20).offset(20)
```

Better:

```python
select(User)
.order_by(User.created_at.desc(), User.id.desc())
.limit(20)
.offset(20)
```

For large datasets, consider keyset pagination.

Example concept:

```python
select(User)
.where(User.id > last_seen_id)
.order_by(User.id)
.limit(page_size)
```

Avoid unbounded `.all()` on large tables.

## N+1 Queries

Detect code that loads related records one query at a time.

Example risk:

```python
users = session.execute(select(User)).scalars().all()

for user in users:
    print(user.roles)
```

Use deliberate eager loading:

```python
from sqlalchemy.orm import selectinload

stmt = select(User).options(selectinload(User.roles))
```

Choose:

* `selectinload`
* `joinedload`
* `contains_eager`

based on query shape.

Do not eager-load large relationships blindly.

## Lazy Loading and Closed Sessions

A relationship may fail when accessed after the session is closed.

Typical error:

```text
DetachedInstanceError
```

Avoid returning ORM entities that require later lazy loading.

Options:

* eager-load required relationships
* serialize within the session
* return explicit DTOs or response schemas
* set appropriate loading strategy

## Bulk Operations

Bulk operations may bypass:

* ORM events
* relationship handling
* identity map updates
* object-level validation

Use bulk operations only when their behavior is understood.

For large inserts, consider:

* PostgreSQL COPY
* batched inserts
* SQLAlchemy Core insert
* `execute(insert(...), values)`

Avoid adding millions of ORM objects to one session without flushing and clearing in batches.

## PostgreSQL Constraints

Use database constraints for critical invariants.

Examples:

* primary keys
* foreign keys
* unique constraints
* check constraints
* non-null constraints
* exclusion constraints

Example:

```python
from sqlalchemy import CheckConstraint

__table_args__ = (
    CheckConstraint("balance >= 0", name="ck_account_balance_nonnegative"),
)
```

Application validation improves errors. Database constraints guarantee integrity.

## Unique Constraints

Do not implement uniqueness only as:

```python
existing = find_by_email(session, email)

if existing:
    raise DuplicateEmailError
```

Concurrent requests can both pass the check.

Enforce uniqueness in PostgreSQL and handle `IntegrityError`.

## PostgreSQL Indexes

Add indexes based on real query patterns.

Good candidates:

* foreign key filters
* frequent equality filters
* range filters
* join columns
* ordering columns
* tenant and status combinations

Example composite index:

```python
Index(
    "ix_jobs_tenant_status_created",
    Job.tenant_id,
    Job.status,
    Job.created_at,
)
```

Column order matters.

Do not add an index to every column.

Indexes increase:

* storage
* insert cost
* update cost
* maintenance cost

## Partial Indexes

PostgreSQL partial indexes are useful for frequently queried subsets.

Example:

```sql
CREATE INDEX CONCURRENTLY ix_jobs_pending
ON jobs (created_at)
WHERE status = 'pending';
```

Use when query predicates consistently match the index condition.

## JSONB

Use JSONB for flexible data when relational columns are not more appropriate.

Good uses:

* provider metadata
* optional structured settings
* event payloads
* flexible audit details

Avoid storing core relational data entirely inside JSONB.

When querying JSONB frequently, consider:

* GIN indexes
* expression indexes
* generated columns
* normalized columns

Validate JSON structure in the application.

## Enums

Choose deliberately between:

* PostgreSQL native enum
* text column plus check constraint
* lookup table

Native enums are strict but require careful migrations.

Ensure consistency across:

* Python enum
* SQLAlchemy model
* migration
* PostgreSQL type
* frontend contract

## UUIDs

Use PostgreSQL-native UUID types when appropriate.

```python
from sqlalchemy.dialects.postgresql import UUID

id: Mapped[UUID] = mapped_column(
    UUID(as_uuid=True),
    primary_key=True,
)
```

Avoid converting UUIDs to strings unnecessarily inside the database layer.

## Timezones

Store timestamps consistently.

Prefer timezone-aware UTC values.

Example:

```python
created_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True),
    server_default=func.now(),
)
```

Avoid comparing naive and aware datetimes.

Do not assume database timestamps are in the user’s local timezone.

Convert to local time only at presentation boundaries.

## Server Defaults

Use server defaults when the database must populate values reliably.

Example:

```python
created_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True),
    server_default=func.now(),
    nullable=False,
)
```

Python-side defaults do not apply when another service inserts directly into the database.

## Soft Deletion

When using soft deletion:

* apply filters consistently
* decide whether unique constraints include deleted rows
* prevent accidental exposure
* define restoration behavior
* define cascade behavior
* consider partial unique indexes

Example:

```sql
CREATE UNIQUE INDEX ux_users_active_email
ON users (email)
WHERE deleted_at IS NULL;
```

Do not rely on every developer remembering to add `deleted_at IS NULL` manually.

## Multi-Tenant Safety

For multi-tenant applications, every relevant query must enforce tenant boundaries.

Check:

* reads
* updates
* deletes
* exports
* downloads
* aggregate queries
* background jobs
* admin workflows
* relationship loading

Avoid:

```python
session.get(Document, document_id)
```

when a tenant condition is required.

Prefer:

```python
stmt = select(Document).where(
    Document.id == document_id,
    Document.tenant_id == tenant_id,
)
```

Consider PostgreSQL Row-Level Security only when the team can operate and test it correctly.

## Background Jobs

Each background job must create its own session.

Example:

```python
def process_job(job_id: UUID) -> None:
    with SessionLocal() as session:
        try:
            job = session.get(Job, job_id)
            if job is None:
                return

            process(job)
            session.commit()
        except Exception:
            session.rollback()
            raise
```

Do not pass a request-scoped session into:

* Celery
* RQ
* Dramatiq
* scheduled tasks
* threads
* subprocesses
* FastAPI background tasks

## Long-Running Operations

Do not keep a database transaction open while:

* calling an LLM
* uploading to cloud storage
* processing large PDFs
* waiting for external APIs
* generating media
* sending email

Preferred flow:

1. create job record
2. commit
3. perform external work
4. open new transaction
5. save result
6. commit

Use status values and idempotency to make the workflow recoverable.

## Migrations

Use Alembic or the project’s configured migration tool.

Every schema change should include a migration.

Check:

* upgrade path
* downgrade or forward-fix strategy
* data compatibility
* application deployment order
* lock duration
* existing data
* nullability
* index creation impact
* enum changes
* foreign key validation
* default values

Do not modify production schema manually without recording the change in migrations.

## Safe Migration Pattern

For a new required column:

Unsafe:

```sql
ALTER TABLE users
ADD COLUMN status TEXT NOT NULL;
```

Safer sequence:

1. add nullable column
2. deploy code that writes the new column
3. backfill existing rows
4. verify no null values remain
5. add default if required
6. apply non-null constraint
7. remove transitional compatibility later

## Index Migrations

For large production tables, use concurrent index creation where supported.

```sql
CREATE INDEX CONCURRENTLY ix_events_created_at
ON events (created_at);
```

PostgreSQL concurrent index operations generally cannot run inside a normal transaction block.

Configure the migration carefully.

## Foreign Key Migrations

Large foreign key validation can lock or scan significant data.

A safer PostgreSQL pattern may use:

```sql
ALTER TABLE child
ADD CONSTRAINT fk_child_parent
FOREIGN KEY (parent_id)
REFERENCES parent(id)
NOT VALID;
```

Then validate separately:

```sql
ALTER TABLE child
VALIDATE CONSTRAINT fk_child_parent;
```

Use only when appropriate and supported by deployment procedures.

## Data Backfills

Backfills should be:

* restartable
* idempotent
* batched
* observable
* bounded
* safe under concurrent application writes

Avoid one enormous transaction for millions of rows.

Track progress explicitly.

## Schema and Model Consistency

Verify consistency between:

* ORM models
* Alembic migrations
* actual PostgreSQL schema
* Pydantic schemas
* TypeScript API types

Watch for:

* nullable mismatch
* enum mismatch
* missing index
* renamed column
* changed foreign key
* length mismatch
* different defaults
* timezone mismatch

## Error Mapping

Translate database errors into domain-level errors.

Example:

```python
from sqlalchemy.exc import IntegrityError

try:
    session.commit()
except IntegrityError as exc:
    session.rollback()

    if is_unique_violation(exc):
        raise DuplicateEmailError from exc

    raise
```

Do not expose raw database error messages to API clients.

Avoid relying only on fragile string matching when PostgreSQL error codes are available.

## PostgreSQL Error Codes

When supported by the driver, inspect SQLSTATE codes.

Examples:

```text
23505 unique_violation
23503 foreign_key_violation
23502 not_null_violation
40001 serialization_failure
40P01 deadlock_detected
```

Use structured driver attributes where possible.

## Observability

Log useful database context:

* operation name
* entity type
* entity ID
* request ID
* job ID
* duration
* retry count
* SQLSTATE where safe
* pool timeout events

Do not log:

* passwords
* database URLs
* connection strings
* full sensitive queries
* private user data
* raw medical or academic records

Enable SQL echo only for controlled development environments.

## Slow Query Investigation

Use evidence.

Inspect:

* query count
* query duration
* execution plan
* row estimates
* actual rows
* index usage
* sequential scans
* sort operations
* join strategy
* lock waits

Use:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT ...;
```

Do not run expensive `EXPLAIN ANALYZE` statements against production without understanding their impact.

## Session Leak Detection

Symptoms:

* pool timeout
* exhausted connections
* increasing idle transactions
* requests hanging while waiting for a connection

Check:

* missing `close()`
* generators not finalized
* sessions stored globally
* sessions passed to background jobs
* open streaming responses
* exceptions bypassing cleanup
* uncommitted transactions
* excessive worker count

Inspect PostgreSQL activity:

```sql
SELECT
    pid,
    usename,
    application_name,
    state,
    query_start,
    wait_event_type,
    wait_event,
    query
FROM pg_stat_activity
WHERE datname = current_database();
```

Do not terminate sessions automatically without explicit approval.

## Idle Transactions

`idle in transaction` sessions can hold:

* locks
* old snapshots
* vacuum progress
* connection slots

Keep transactions short.

Do not perform user interaction or external API calls while a transaction remains open.

## Testing

Add tests for:

* successful insert
* successful update
* rollback on failure
* unique constraint violation
* foreign key violation
* missing record
* concurrent update
* duplicate request
* transaction atomicity
* connection loss handling
* retry limits
* idempotency
* pagination ordering
* tenant isolation
* soft deletion
* timezone behavior
* migration compatibility

Use a real PostgreSQL test database for PostgreSQL-specific behavior when practical.

SQLite is not a complete substitute for PostgreSQL because behavior differs for:

* JSONB
* enums
* locking
* isolation
* UUIDs
* constraints
* partial indexes
* concurrent behavior
* SQL syntax

## Verification Commands

Inspect the project configuration before choosing commands.

Typical checks:

```bash
ruff check .
ruff format --check .
mypy .
pyright
pytest
```

Migration checks:

```bash
alembic current
alembic heads
alembic history
alembic upgrade head
```

Detect multiple migration heads:

```bash
alembic heads
```

Generate SQL without applying where supported:

```bash
alembic upgrade head --sql
```

Do not apply production migrations automatically unless explicitly authorized.

## Review Checklist

When reviewing SQLAlchemy or PostgreSQL changes, check:

### Session lifecycle

* Is the session scoped correctly?
* Is it always closed?
* Is rollback performed after failure?
* Is a failed session reused?
* Is a request session passed to background work?

### Transactions

* Are atomic operations inside one transaction?
* Are commits hidden inside lower layers?
* Are external calls made inside transactions?
* Can partial writes occur?
* Can retries duplicate writes?

### Concurrency

* Is there a check-then-act race?
* Is the update atomic?
* Is row locking required?
* Is idempotency enforced?
* Are database constraints present?

### Queries

* Are tenant filters present?
* Is pagination deterministic?
* Are queries bounded?
* Is there an N+1 pattern?
* Are relationships loaded safely?

### Schema

* Do models and migrations match?
* Are nullability and defaults correct?
* Are constraints enforced in PostgreSQL?
* Are indexes justified?
* Is the migration safe for existing data?

### Production

* Is pool sizing realistic?
* Are connection limits respected?
* Are timeouts configured?
* Are failures observable?
* Is there a rollback plan?

## Required Review Output

When reviewing database code, present findings in descending severity.

Use:

```text
[Severity] Finding title

Location:
path/to/file.py:line-range

Problem:
Describe the database defect and the realistic trigger.

Impact:
Describe the data-integrity, reliability, security or performance impact.

Recommended fix:
Describe the smallest safe correction.

Verification:
Describe the test, query or command that confirms the fix.
```

Severity levels:

* Blocker
* High
* Medium
* Low
* Suggestion

## Debugging Workflow

When debugging a database issue:

1. Capture the complete original error.
2. Identify the failing query or transaction.
3. Inspect session state.
4. Check whether rollback occurred.
5. Check whether the session was reused.
6. Inspect connection pool behavior.
7. Check PostgreSQL logs and activity.
8. Reproduce with a focused test.
9. Determine whether the failure is:

   * application logic
   * transaction state
   * connection failure
   * pool exhaustion
   * database constraint
   * concurrency
   * migration mismatch
   * infrastructure timeout
10. Apply the smallest safe fix.
11. Add a regression test.
12. Run focused verification.

Do not begin by increasing pool size or adding retries without finding the root cause.

## Modification Rules

When modifying database code:

* Keep changes focused.
* Preserve public API behavior where possible.
* Avoid unrelated model refactoring.
* Do not delete production data.
* Do not reset migrations automatically.
* Do not drop tables or columns without explicit authorization.
* Do not change connection credentials.
* Do not expose secrets.
* Add tests for transaction and failure behavior.
* Update migrations when schema changes.
* Report manual production steps clearly.

## Completion Criteria

A SQLAlchemy or PostgreSQL task is complete only when:

* sync or async architecture is respected
* session lifecycle is correct
* failed transactions are rolled back
* broken sessions are not reused
* transaction boundaries are explicit
* concurrency risks are handled
* critical invariants are enforced by PostgreSQL
* queries are bounded and tenant-safe
* models and migrations match
* pool configuration is realistic
* relevant tests pass
* migration safety is understood
* remaining risks are reported honestly
