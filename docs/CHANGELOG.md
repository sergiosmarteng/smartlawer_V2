# Microharness — Changelog

> **How to use this file:**
> - Add an entry after completing each phase (or significant sub-task) from `TASKS.md`.
> - Each entry should record: what was done, by whom/what, any deviations from PLAN.md.
> - Newest entries at the top.
> - This file serves as continuity between agent sessions — if a session is cleared,
>   the next agent reads this to understand what's already been done.

---

## Format

```
### [DATE] — Phase N: [Phase Name]
**Agent/Session**: [identifier or "human"]
**Files changed**: list of files created or modified
**What was done**: brief summary
**Deviations from PLAN.md**: any changes or issues encountered
**Blockers**: anything that prevented completion
```

---

## Entries

### 2026-04-01 — Phase 4: Memory Client — ✅ APPROVED

**Agent/Session**: task-builder
**Files changed**: tests/test_memory.py (created), src/microharness/memory.py (bug fixes), TASKS.md (updated), CHANGELOG.md (updated), pyproject.toml (added dev dependencies)
**What was done**:
- Created comprehensive unit test suite `tests/test_memory.py` with 27 tests covering:
  - All MemoryClient methods (fetch_task_context, append_changelog, update_subtasks, update_status, search)
  - Success and error scenarios (HTTP errors, missing fields, invalid data)
  - Retry logic with exponential backoff and max retries
  - Context manager behavior (`__aenter__`, `__aexit__`)
  - Error types (`MemoryServiceError`, `MemoryServiceUnavailable`)
- Fixed two bugs in `src/microharness/memory.py`:
  - `__aenter__` incorrectly awaited synchronous `_ensure_session()` method
  - `fetch_task_context` did not catch `TypeError` when constructing `ChangeEntry` from incomplete data
- Added dev dependencies (`pytest`, `pytest-asyncio`, `pytest-aioresponses`, `aioresponses`) to `pyproject.toml`
- All 27 tests pass

**Deviations from PLAN.md**: None. The unit tests fulfill TDD requirement; integration test (sub-task 77) remains for evaluator to run against memory-mock service.

**Blockers**: None

---

### 2026-04-01 — Phase 4: Memory Client — ✅ APPROVED (Evaluator Validation)

**Agent/Session**: task-evaluator
**Files changed**: TASKS.md (marked integration test complete)

**What was done**: Independent evaluation of Phase 4 against EVALUATION.md criteria.

**Checks passed** (8/8):
- [x] Constitution compliance (all rules verified)
- [x] Plan compliance (file locations, class/method names, data structures)
- [x] Test suite: all 27 tests pass
- [x] EVALUATION.md scripts: passed
- [x] Integration test: passed (memory-mock service started, full CRUD cycle verified)
- [x] TDD compliance: test file exists with meaningful tests

**Evaluator notes**:
- Code quality: clean, well-documented, proper exception handling
- Both previously identified bugs are fixed (`__aenter__` synchronous call, TypeError catching)
- Retry logic works correctly with exponential backoff and configurable parameters
- All environment variable configuration in place
- No hardcoded values

**Deviations from PLAN.md**: None.

**Blockers**: None

---
### 2026-04-01 — Phase 4: Memory Client — ❌ REJECTED

**Agent/Session**: task-evaluator
**Files changed**: TASKS.md (added missing test sub-task)
**What was done**: Evaluated Phase 4 against evaluation criteria.
**Failures**:
1. TDD VIOLATION: `tests/test_memory.py` does not exist. CONSTITUTION Rule #14 requires every module in `src/microharness/` to have a corresponding test file.
2. No test suite present: `pytest` not installed, no tests directory found.
**Required fixes**:
1. Create `tests/test_memory.py` with unit tests covering MemoryClient methods (fetch_task_context, append_changelog, update_subtasks, update_status, search) including error handling and retry logic.
2. Ensure `pytest` and `pytest-asyncio` are installed (`uv add --dev pytest pytest-asyncio`) and all tests pass (`python -m pytest tests/ -v`).
**Rejection count**: 1 (first rejection for Phase 4)

---

### 2026-04-01 — Phase 4: Memory Client

**Agent/Session**: task-builder (Claude Code)
**Files changed**:
- `src/microharness/memory.py` (created)

**What was done**:
- Implemented `MemoryClient` class with async methods:
  - `fetch_task_context(task_id)` → `TaskContext`
  - `append_changelog(task_id, entry)`
  - `update_subtasks(task_id, subtasks_md)`
  - `update_status(task_id, status)`
  - `search(query, top_k)`
- Implemented exponential backoff retry via `_request_with_retry()` helper
- Configurable via env vars: `MEMORY_RETRY_COUNT` (default 3), `MEMORY_RETRY_BACKOFF` (default 1)
- Defined custom exceptions: `MemoryServiceError`, `MemoryServiceUnavailable`
- Supports context manager usage (`async with`) for automatic session management

**Deviations from PLAN.md**: None.

**Blockers**: Could not perform runtime testing against memory-mock service as it is not currently running. The evaluator will run the integration test when the service is available.

---

### 2026-04-01 — Phase 3: Memory Mock Service

**Agent/Session**: task-builder (Claude Code)
**Files changed**:
- `services/memory-mock/main.py` (created)
- `services/memory-mock/Dockerfile` (created)
- `services/memory-mock/requirements.txt` (created)
- `TASKS.md` (marked Phase 3 sub-tasks complete)

**What was done**:
- Created FastAPI-based memory mock service with all required endpoints:
  - `GET /tasks/{task_id}` - returns full task context (plan, constitution, subtasks, changelog, metadata)
  - `GET /tasks/{task_id}/plan` - returns plan.md content
  - `GET /tasks/{task_id}/constitution` - returns constitution.md content
  - `GET /tasks/{task_id}/subtasks` - returns tasks.md content
  - `GET /tasks/{task_id}/changelog` - returns changelog entries
  - `POST /tasks/{task_id}/changelog` - appends changelog entry
  - `PUT /tasks/{task_id}/subtasks` - updates subtasks
  - `PUT /tasks/{task_id}/status` - updates task status
  - `POST /memory/search` - stub RAG search (returns empty list)
  - `POST /tasks` - creates new task for seeding
- Implemented file-based storage under `/data/memory/{task_id}/` using JSON files for changelog and metadata, markdown files for plan/constitution/subtasks
- Added health check endpoint at `/health`
- Created Dockerfile using python:3.13-slim base with FastAPI + uvicorn
- Created requirements.txt with fastAPI, uvicorn, pydantic

**Deviations from PLAN.md**: None. All requirements met exactly as specified.

**Blockers**: None

---

### 2026-03-31 — Phase 0: Planning

**Agent/Session**: Human + AI planning session
**Files changed**: `PLAN.md`, `TASKS.md`, `CONSTITUTION.md`, `CHANGELOG.md`
**What was done**:
- Designed full architecture for microharness as a specialized swarm worker
- Defined MQTT topic design (QoS 2, swarm/{role}/tasks for assignment, swarm/{harness_id}/* for status/events/output)
- Defined Memory Service API contract (REST, task-scoped artifacts)
- Defined TaskEvaluator XML verdict format (`<success>` / `<failure>`)
- Defined error handling: memory retry policy with waiting state, SIGTERM graceful shutdown
- Defined concurrent task handling: option C (task-manager awareness, harness ignores when busy)
- Defined domain model: microharness only knows tasks (UUID) and sub-tasks (markdown checkboxes)
- Created 4 project memory files: PLAN.md, TASKS.md, CONSTITUTION.md, CHANGELOG.md
**Deviations from PLAN.md**: N/A (this IS the plan creation)
**Blockers**: None

---

### 2026-04-01 — Phase 2: Agent Configuration Loader (rejection fix)

**Agent/Session**: task-builder
**Files changed**: `.claude/agents/task-builder.md`
**What was done**:
- Added "Response Format (XML Verdict)" section to task-builder.md system prompt
- Documented all three XML tags: `<success>`, `<failure>`, and `<waiting_for_user_input>`
- Included attribute explanations and usage examples for each tag
- Fixed evaluator rejection: system prompt now documents `<waiting_for_user_input>` as required

**Deviations from PLAN.md**: None. This was a missing documentation element that has now been added.

**Blockers**: None

---

### 2026-04-01 — Phase 2: Agent Configuration Loader

**Agent/Session**: task-builder
**Files changed**:
- `.claude/agents/task-builder.md` (added YAML frontmatter)
- `.claude/agents/task-evaluator.md` (added YAML frontmatter + XML response format section with examples)
- `TASKS.md` (marked Phase 2 sub-tasks complete)

**What was done**:
- Verified `src/microharness/agent_loader.py` was already correctly implemented
- Added YAML frontmatter (`---name: task_builder---`) to `task-builder.md`
- Added YAML frontmatter (`---name: task_evaluator---`) to `task-evaluator.md`
- Enhanced `task-evaluator.md` system prompt with explicit "Response Format (XML Verdict)" section containing examples of `<success>`, `<failure>`, and `<waiting_for_user_input>` tags with attribute explanations

**Deviations from PLAN.md**: None. All requirements met.

**Blockers**: None

---

### 2026-04-01 — Phase 1: Core Data Models

**Agent/Session**: task-builder (Claude Code)
**Files changed**: `src/microharness/task_context.py`, `src/microharness/transport.py`, `TASKS.md`
**What was done**:
- Implemented all data models for Phase 1:
  - `TaskStatus` enum with all required values (idle, initializing, building, evaluating, complete, failed, paused, waiting, waiting_for_input, shutting_down)
  - `ChangeEntry` dataclass for changelog entries
  - `TaskContext` dataclass with all required fields
  - `Verdict` dataclass for agent verdict parsing (success/failure/waiting_for_input)
  - `Message` dataclass for MQTT messages
  - `Transport` abstract base class with required methods
- Added `publish_waiting()` and `await_user_input()` to Transport ABC (per PLAN.md user input handling)

**Deviations from PLAN.md**:
- Initially, `ChangeEntry` and `Message` were implemented as `TypedDict`. Fixed to use `@dataclass` per CONSTITUTION rule #11 ("Dataclasses for data").
- Added `publish_waiting()` and `await_user_input()` to Transport ABC — not explicitly listed in TASKS.md sub-task but required by PLAN.md's waiting_for_user_input flow.

**Blockers**: None
