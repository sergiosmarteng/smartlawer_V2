---
name: repository-navigation
description: Navigate unfamiliar repositories efficiently by building a compact repo map, finding relevant files, tracing callers, and avoiding unnecessary context loading.
license: MIT
compatibility: opencode
metadata:
  category: repository-analysis
  stack: cross-stack
  version: "1.0.0"
orchestration:
  lead_for: []
  support_for:
    - token-compression
  conflicts_with: []
---

# Repository Navigation

Use this skill when exploring a new or unfamiliar repository to understand its structure before making changes.

The objective is to build a compact repository map that identifies entry points, framework configuration, important directories, test conventions, and the exact files relevant to the current task — without reading every file.

## Start with Repository Map

Before reading any code, build a high-level map by inspecting the top-level directory.

```text
/
├── README.md
├── AGENTS.md
├── pyproject.toml / package.json
├── src/ or app/
├── tests/ or __tests__/
├── migrations/
├── .github/workflows/
└── config/ or settings/
```

Record:
- project structure at the top two directory levels
- src layout (monorepo? flat? domain-organized?)
- test directory location and naming convention
- migration directory and naming convention
- config or settings file location

## Inspect Package Manifests

Read the project's package manifest first. It tells you:

- language and runtime version
- framework and major dependency versions
- test framework and test runner
- linting and formatting tools
- build and dev scripts
- project scripts and entry points

Check these files in order:

- `pyproject.toml` — Python projects
- `package.json` — Node.js projects
- `Cargo.toml` — Rust projects
- `go.mod` — Go projects
- `Gemfile` — Ruby projects
- `requirements.txt` or `Pipfile` — Python fallback

Extract and record:
- runtime version constraint
- web framework and version
- database ORM and version
- test framework
- linter and formatter
- build tool
- available scripts (dev, build, test, lint, typecheck, migrate)

## Inspect AGENTS.md and README First

Always read `AGENTS.md` and `README.md` before any other file. They contain:

- project-specific instructions for the agent
- architecture overview
- setup and run instructions
- test commands
- deployment procedures
- coding conventions
- prohibited patterns

Do not skip these files even if the repository looks familiar.

## Use glob and grep Before Reading Large Files

Before opening a large file:

1. Use `glob` to find files by pattern.
2. Use `grep` to locate the specific function, class, or symbol you need.
3. Read only the relevant lines or a small window around the match.

Examples:

```text
# Find all route files
glob "**/*route*"
glob "**/*router*"
glob "**/routes/**"

# Find a model definition
grep "class User" --include="*.py"

# Find where a function is called
grep "calculate_score" --include="*.py"

# Find test files for a module
glob "**/test*user*"
glob "**/test*score*"
```

## Trace Entry Points to Services to Tests

When investigating a feature, trace the full path:

1. **Entry point** — route handler, API endpoint, CLI command, or event consumer.
2. **Schema/validation** — request and response models.
3. **Service layer** — business logic.
4. **Data access** — repository, ORM query, or database call.
5. **Tests** — test file for the feature.

For each layer, record the file path and a one-line summary of its responsibility.

## Identify Generated Files and Avoid Reading Them

Do not read generated, compiled, or transient files unless the bug is in the build output.

Skip by default:

* `node_modules/`
* `__pycache__/`
* `.next/`
* `dist/`
* `build/`
* `.venv/` or `venv/`
* `*.pyc`
* `*.pyo`
* `package-lock.json` (read only for dependency resolution bugs)
* `yarn.lock`
* `poetry.lock`
* minified or bundled assets
* generated protobuf or GraphQL files
* auto-generated API clients

When you must read a generated file, confirm it cannot be reproduced from source first.

## Identify Framework Versions

Record the exact versions of:

* language runtime (Python 3.11, Node 20, etc.)
* web framework (FastAPI 0.110, Next.js 14, etc.)
* database ORM (SQLAlchemy 2.0, Prisma 5, etc.)
* test framework (pytest 8, Vitest 1, etc.)
* major libraries (Pydantic 2, React 18, etc.)

Use this information to apply version-appropriate guidance.

## Identify Test Commands

Find and record the exact test commands used in the project:

```text
# Common locations to check:
# - pyproject.toml [tool.pytest.ini_options]
# - package.json scripts
# - Makefile
# - README
# - AGENTS.md
# - CI workflow files
# - Justfile
# - tox.ini
# - pytest.ini
# - .github/workflows/*.yml
```

Record at least:
- command to run all tests
- command to run a single test file
- command to run a single test case
- command to run linting
- command to run type checking
- command to build the project

## Identify Similar Features

Before implementing a new feature, find similar existing features and read their implementation. This reveals:

- project conventions for structure and naming
- reusable patterns and abstractions
- expected test coverage
- error handling patterns
- permission and authorization patterns

Search by:

```text
# Find similar endpoints
grep "router" --include="*.py"

# Find existing CRUD for a similar entity
glob "**/*student*"
glob "**/*assignment*"

# Find existing test patterns
glob "**/test*crud*"
```

## Inspect git diff Before Reviewing

Before reviewing changes, always run:

```bash
git diff
git diff --cached
git status
git log --oneline -5
```

This reveals exactly what changed and helps focus on the modified code rather than the entire file.

## Maintain a Compact File Relevance Table

Keep a running table of every file you read and its relevance:

```text
File                          Relevance
────────────────────────────────────────────────────
src/routes/users.py           Entry point for user CRUD
src/schemas/user.py           Request/response validation
src/services/user_service.py  Business logic
src/models/user.py            Database model
tests/test_users.py           Test coverage
```

Update this table as you discover new files. Remove files that turned out to be irrelevant.

## Examples

### FastAPI Endpoint Tracing

```text
Goal:  Find the handler for POST /api/v1/assignments

1. glob "**/*route*" "**/*router*" "**/routes/**"
   → src/routes/assignments.py

2. grep "def create" "src/routes/assignments.py"
   → async def create_assignment(...)

3. Read the route to find the service call.
   → src/services/assignment_service.py

4. grep "class.*Create" "src/schemas/assignment.py"
   → class AssignmentCreate(BaseModel)

5. glob "**/test*assignment*"
   → tests/test_assignments.py

Files:
  src/routes/assignments.py    — route handler
  src/schemas/assignment.py    — request schema
  src/services/assignment_service.py  — business logic
  tests/test_assignments.py    — tests
```

### SQLAlchemy Model and Migration Tracing

```text
Goal:  Find the User model and its latest migration

1. grep "class User" --include="*.py"
   → src/models/user.py: class User(Base)

2. Read the model to find the table name and columns.

3. glob "migrations/versions/*.py"
   → migrations/versions/2024-01-15_create_users.py

4. grep "create_table.*user" "migrations/versions/*.py"
   → def upgrade(): op.create_table("users", ...)

Files:
  src/models/user.py                     — model definition
  migrations/versions/2024-01-15_*.py    — migration
```

### Next.js Page and Component Tracing

```text
Goal:  Find the dashboard page and its data fetching

1. glob "app/dashboard/**"
   → app/dashboard/page.tsx
   → app/dashboard/layout.tsx

2. Read page.tsx to find data fetching.
   → fetch('/api/dashboard/stats')

3. glob "app/api/dashboard/**"
   → app/api/dashboard/stats/route.ts

4. Read the API route to find the service call.

5. glob "**/components/dashboard/**"
   → components/dashboard/StatsCard.tsx

Files:
  app/dashboard/page.tsx              — page component
  app/dashboard/layout.tsx            — layout
  app/api/dashboard/stats/route.ts    — API route
  components/dashboard/StatsCard.tsx  — UI component
```

### Test Discovery

```text
Goal:  Find all tests related to the assignment module

1. glob "**/test*assignment*"
   → tests/test_assignments.py
   → tests/test_assignment_service.py

2. Read test file headers to understand test structure.

3. Record test command:
   pytest tests/test_assignments.py -q
   pytest tests/test_assignments.py::test_create_assignment -q

Files:
  tests/test_assignments.py           — route tests
  tests/test_assignment_service.py    — service tests
```

### Bug Trace from Stack Trace

```text
Stack trace (condensed):
  File "src/routes/assignments.py", line 42, in create_assignment
    result = await service.create(db_session, data)
  File "src/services/assignment_service.py", line 88, in create
    db_session.add(assignment)
  File "src/models/assignment.py", line 25, in __init__
    self.score = calculate_score(self.answers)
  File "src/utils/scoring.py", line 14, in calculate_score
    return sum(points.values())

Tracing:

1. Read src/utils/scoring.py around line 14 first
   → root cause is likely here (calculate_score)

2. Read src/models/assignment.py around line 25
   → verify the call site

3. Read src/services/assignment_service.py around line 88
   → verify the caller

4. Read src/routes/assignments.py around line 42
   → verify the entry point

5. Find related tests:
   glob "**/test*score*"
   glob "**/test*assignment*"

Files:
  src/utils/scoring.py           — likely root cause
  src/models/assignment.py        — model
  src/services/assignment_service.py  — service
  src/routes/assignments.py       — entry point
  tests/test_scoring.py           — tests
```

## Required Output

After initial exploration, produce this compact map:

```text
Repository map:

Runtime:
[Python 3.11, Node 20, etc.]

Frameworks:
[FastAPI 0.110, SQLAlchemy 2.0, Next.js 14, etc.]

Important directories:
[src/, app/, tests/, migrations/, config/]

Entry points:
[src/routes/users.py:user_router, app/api/[...]/route.ts, etc.]

Relevant files:
[src/services/user_service.py — business logic for user CRUD]

Tests:
[tests/test_users.py — pytest, run with: pytest tests/test_users.py -q]

Unknowns:
[What is not yet known that might affect the task.]

Next file to inspect:
[The single most important file to read next.]
```

## Do Not

* Do not read files before checking the project manifest.
* Do not skip AGENTS.md or README.md.
* Do not read generated or compiled files unless there is no alternative.
* Do not read every file in a directory. Use glob and grep first.
* Do not invent file paths. Verify every file exists before reading.
* Do not skip git diff when reviewing changes.
* Do not keep irrelevant files in your file relevance table.
* Do not guess framework versions. Read the manifest.

## Completion Criteria

Repository navigation is complete only when:

* the project manifest has been read and framework versions are known
* AGENTS.md and README.md have been read
* entry points, services, models, and tests are identified for the current task
* the test command is recorded
* generated files have been excluded from inspection
* a compact file relevance table exists
* the next file to read is known
