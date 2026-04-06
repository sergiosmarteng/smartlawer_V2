# Microharness — Evaluation Criteria

> **How to use this file:**
> - After completing a phase from `TASKS.md`, run the evaluation steps below for that phase.
> - Every criterion must pass before marking the phase as complete.
> - If a criterion fails, document it in `CHANGELOG.md` and fix before proceeding.
> - Some evaluations require infrastructure (Docker, Mosquitto). Skip those until Phase 9 is complete,
>   then re-run all integration/E2E evaluations.
>
> **Evaluation types:**
> - 🔍 **Code review** — verify structure, types, patterns by reading the code
> - ⚡ **Unit test** — run an automated test
> - 🔌 **Integration test** — requires a running service (mock or real)
> - 🚀 **E2E test** — requires full docker-compose stack

---

## Phase 1: Core Data Models

### Files: `task_context.py`, `transport.py`

🔍 **Code review:**
- [ ] `TaskStatus` enum has exactly these values: `idle`, `initializing`, `building`, `evaluating`, `complete`, `failed`, `paused`, `waiting`, `waiting_for_input`, `shutting_down`
- [ ] `TaskContext` dataclass has `task_id: str` (UUID), no `feature_id` field
- [ ] `TaskContext.subtasks` field (not `tasks`) — naming must match PLAN.md
- [ ] `TaskContext.user_input_response: str | None` field exists
- [ ] `Verdict.decision` supports three values: `success`, `failure`, `waiting_for_input`
- [ ] `Verdict.question: str | None` field exists (populated only for `waiting_for_input`)
- [ ] `Transport` is an ABC (inherits `abc.ABC`), not a concrete class
- [ ] `Transport` has abstract methods: `start()`, `stop()`, `receive()`, `send()`, `publish_event()`, `publish_status()`, `publish_heartbeat()`
- [ ] All public attributes have type annotations
- [ ] No imports of `dotenv` anywhere

⚡ **Unit test:**
```bash
# Run from project root
python -c "
from microharness.task_context import TaskContext, TaskStatus, ChangeEntry, Verdict

# Verify enum values
assert 'waiting_for_input' in [s.value for s in TaskStatus], 'Missing waiting_for_input status'
assert 'idle' in [s.value for s in TaskStatus], 'Missing idle status'

# Verify TaskContext creation
ctx = TaskContext(
    task_id='a1b2c3d4-5678-4ef0-abcd-1234567890ab',
    role='backend-engineering',
    plan='# Plan',
    subtasks='- [ ] subtask 1',
    constitution='# Rules',
    changelog=[],
    current_iteration=0,
    status=TaskStatus.IDLE,
    max_retries=5,
    evaluator_feedback=None,
    user_input_response=None,
)
assert ctx.task_id == 'a1b2c3d4-5678-4ef0-abcd-1234567890ab'

# Verify Verdict
v = Verdict(decision='waiting_for_input', confidence=0.0, subtasks_completed=[], subtasks_remaining=[], feedback='', question='What should I do?')
assert v.question == 'What should I do?'

print('✅ Phase 1: All data model checks passed')
"
```

---

## Phase 2: Agent Configuration Loader

### Files: `agent_loader.py`, `.claude/agents/task_builder.md`, `.claude/agents/task_evaluator.md`

🔍 **Code review:**
- [ ] `agent_loader.py` uses `python-frontmatter` to parse YAML frontmatter from `.md` files
- [ ] `AgentConfig` dataclass has at minimum: `name`, `system_prompt`
- [ ] `load_agent_configs()` returns a dict keyed by agent name (e.g., `{"task_builder": ..., "task_evaluator": ...}`)
- [ ] Missing `.claude/agents/` directory raises a clear error, not a silent failure
- [ ] Malformed `.md` files are skipped with a warning log, not a crash
- [ ] `task_builder.md` has YAML frontmatter with `name: task_builder`
- [ ] `task_evaluator.md` has YAML frontmatter with `name: task_evaluator`
- [ ] `task_evaluator.md` system prompt contains examples of ALL THREE XML tags: `<success>`, `<failure>`, `<waiting_for_user_input>`
- [ ] `task_builder.md` system prompt mentions `<waiting_for_user_input>` as an option

⚡ **Unit test:**
```bash
python -c "
from microharness.agent_loader import load_agent_configs

configs = load_agent_configs('.claude/agents')

# Must have both agents
assert 'task_builder' in configs, 'Missing task_builder config'
assert 'task_evaluator' in configs, 'Missing task_evaluator config'

# Must have system prompts
assert len(configs['task_builder'].system_prompt) > 50, 'task_builder system prompt too short'
assert len(configs['task_evaluator'].system_prompt) > 50, 'task_evaluator system prompt too short'

# Evaluator must mention XML tags
ep = configs['task_evaluator'].system_prompt
assert '<success' in ep, 'Evaluator missing <success> example'
assert '<failure' in ep, 'Evaluator missing <failure> example'
assert '<waiting_for_user_input' in ep, 'Evaluator missing <waiting_for_user_input> example'

print('✅ Phase 2: All agent loader checks passed')
"
```

---

## Phase 3: Memory Mock Service

### Files: `services/memory-mock/main.py`, `Dockerfile`, `requirements.txt`

🔍 **Code review:**
- [ ] FastAPI app with all endpoints from PLAN.md (9 endpoints total)
- [ ] File-based storage under `/data/memory/{task_id}/`
- [ ] `GET /tasks/{task_id}` returns all artifacts in a single response: `plan`, `constitution`, `subtasks`, `changelog`, `metadata`
- [ ] `POST /tasks` endpoint exists for seeding test data
- [ ] `POST /memory/search` returns an empty list (stub)
- [ ] Dockerfile uses `python:3.13-slim` and installs FastAPI + uvicorn
- [ ] No hardcoded task data — everything stored on disk

🔌 **Integration test** (requires running service):
```bash
# Start the mock service
cd services/memory-mock && docker build -t memory-mock . && docker run -d -p 8001:8001 --name memory-mock-test memory-mock

# Seed a test task
curl -s -X POST http://localhost:8001/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "test-uuid-001",
    "role": "backend-engineering",
    "plan": "# Build a REST API\n\nCreate CRUD endpoints for users.",
    "constitution": "# Rules\n\n1. Use async/await\n2. Type hints required",
    "subtasks": "- [ ] Create /users endpoint\n- [ ] Add validation",
    "metadata": {"status": "pending"}
  }' | python -m json.tool

# Verify full context fetch
curl -s http://localhost:8001/tasks/test-uuid-001 | python -m json.tool
# Expected: JSON with plan, constitution, subtasks, changelog (empty), metadata

# Verify individual endpoints
curl -s http://localhost:8001/tasks/test-uuid-001/plan
# Expected: "# Build a REST API..."

curl -s http://localhost:8001/tasks/test-uuid-001/subtasks
# Expected: "- [ ] Create /users endpoint..."

# Append changelog
curl -s -X POST http://localhost:8001/tasks/test-uuid-001/changelog \
  -H "Content-Type: application/json" \
  -d '{"iteration": 1, "agent": "task-builder", "action": "build", "output": "Created endpoints", "verdict": null, "feedback": null}'

# Verify changelog
curl -s http://localhost:8001/tasks/test-uuid-001/changelog | python -m json.tool
# Expected: array with 1 entry

# Update subtasks
curl -s -X PUT http://localhost:8001/tasks/test-uuid-001/subtasks \
  -H "Content-Type: application/json" \
  -d '{"content": "- [x] Create /users endpoint\n- [ ] Add validation"}'

# Verify update
curl -s http://localhost:8001/tasks/test-uuid-001/subtasks
# Expected: "- [x] Create /users endpoint..."

# Update status
curl -s -X PUT http://localhost:8001/tasks/test-uuid-001/status \
  -H "Content-Type: application/json" \
  -d '{"status": "building"}'

# Search stub
curl -s -X POST http://localhost:8001/memory/search \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "top_k": 5}' | python -m json.tool
# Expected: empty array []

# Cleanup
docker stop memory-mock-test && docker rm memory-mock-test

echo "✅ Phase 3: All memory-mock checks passed"
```

---

## Phase 4: Memory Client

### Files: `memory.py`

🔍 **Code review:**
- [ ] `MemoryClient` uses `aiohttp.ClientSession` (not `requests`)
- [ ] All methods are `async`
- [ ] `fetch_task_context()` returns a `TaskContext` dataclass (not raw dict)
- [ ] Retry logic with exponential backoff exists (check for `MEMORY_RETRY_COUNT` env var usage)
- [ ] Custom exceptions: `MemoryServiceError`, `MemoryServiceUnavailable`
- [ ] `aiohttp.ClientSession` is properly opened/closed (context manager or explicit close)

🔌 **Integration test** (requires memory-mock running on :8001):
```bash
python -c "
import asyncio
from microharness.memory import MemoryClient
from microharness.task_context import TaskContext

async def test():
    client = MemoryClient('http://localhost:8001')

    # Fetch context (assumes test task seeded from Phase 3)
    ctx = await client.fetch_task_context('test-uuid-001')
    assert isinstance(ctx, TaskContext), f'Expected TaskContext, got {type(ctx)}'
    assert ctx.task_id == 'test-uuid-001'
    assert 'REST API' in ctx.plan
    assert ctx.constitution is not None
    assert ctx.subtasks is not None

    # Append changelog
    from microharness.task_context import ChangeEntry
    entry = ChangeEntry(iteration=1, agent='test', timestamp='now', action='test', output='output', verdict=None, feedback=None)
    await client.append_changelog('test-uuid-001', entry)

    # Update status
    await client.update_status('test-uuid-001', 'evaluating')

    await client.close()
    print('✅ Phase 4: All memory client checks passed')

asyncio.run(test())
"
```

---

## Phase 5: MQTT Transport

### Files: `infra/mosquitto/mosquitto.conf`, `mqtt_transport.py`

🔍 **Code review:**
- [ ] `mosquitto.conf` has listeners on `:1883` (MQTT) and `:9001` (WebSocket)
- [ ] `mosquitto.conf` has `allow_anonymous true`
- [ ] `MQTTTransport` implements `Transport` ABC
- [ ] All config read from env vars: `MQTT_BROKER_HOST`, `MQTT_BROKER_PORT`, etc.
- [ ] `publish_waiting(question, context)` method exists
- [ ] `await_user_input()` method exists — listens on control topic for `type: "user_input"`
- [ ] Heartbeat uses `asyncio.create_task` for periodic background publishing
- [ ] QoS 2 used for all publish/subscribe calls
- [ ] Incoming tasks ignored when harness is not idle (no acknowledgment)

🔌 **Integration test** (requires Mosquitto running on :1883):
```bash
# Start Mosquitto
docker run -d -p 1883:1883 -p 9001:9001 --name mosquitto-test \
  -v $(pwd)/infra/mosquitto/mosquitto.conf:/mosquitto/config/mosquitto.conf \
  eclipse-mosquitto:2

python -c "
import asyncio, os, json

os.environ['MQTT_BROKER_HOST'] = 'localhost'
os.environ['MQTT_BROKER_PORT'] = '1883'
os.environ['HARNESS_ROLE'] = 'test-role'
os.environ['HARNESS_ID'] = 'test-harness-001'

from microharness.mqtt_transport import MQTTTransport

async def test():
    transport = MQTTTransport()
    await transport.start()

    # Publish a status
    await transport.publish_status('idle', 0, None)

    # Publish a heartbeat
    await transport.publish_heartbeat()

    # Publish waiting_for_user_input
    await transport.publish_waiting('What database should I use?', 'tech_decision')

    await transport.stop()
    print('✅ Phase 5: MQTT transport basic checks passed')

asyncio.run(test())
"

docker stop mosquitto-test && docker rm mosquitto-test
```

---

## Phase 6: Context Builder

### Files: `context_builder.py`

🔍 **Code review:**
- [ ] `ContextBuilder` accepts `max_changelog_entries` parameter (defaults to 5)
- [ ] `build_builder_prompt()` output has sections in order: CONSTITUTION → PLAN → SUBTASKS → CHANGELOG → EVALUATOR FEEDBACK
- [ ] `build_evaluator_prompt()` output has sections in order: CONSTITUTION → PLAN → SUBTASKS → BUILDER OUTPUT
- [ ] `build_resume_prompt()` method exists — appends user response to original prompt
- [ ] Constitution section is clearly delimited (e.g., `=== CONSTITUTION (NON-NEGOTIABLE) ===`)
- [ ] `_summarize_changelog()` keeps last N entries in full, summarizes older ones to one line each
- [ ] Evaluator prompt explicitly instructs XML response format with all 3 tags

⚡ **Unit test:**
```bash
python -c "
from microharness.context_builder import ContextBuilder
from microharness.task_context import TaskContext, TaskStatus, ChangeEntry

ctx = TaskContext(
    task_id='test-uuid',
    role='backend',
    plan='# Build an API',
    subtasks='- [ ] endpoint\n- [ ] tests',
    constitution='# Rules\n1. Use async',
    changelog=[
        ChangeEntry(iteration=i, agent='builder', timestamp=f't{i}', action='build', output=f'output {i}', verdict='failure', feedback=f'fix {i}')
        for i in range(1, 8)  # 7 entries
    ],
    current_iteration=8,
    status=TaskStatus.BUILDING,
    max_retries=10,
    evaluator_feedback='Missing tests',
    user_input_response=None,
)

cb = ContextBuilder(max_changelog_entries=3)

# Builder prompt
bp = cb.build_builder_prompt(ctx)
assert '# Rules' in bp, 'Constitution missing from builder prompt'
assert '# Build an API' in bp, 'Plan missing from builder prompt'
assert '- [ ] endpoint' in bp, 'Subtasks missing from builder prompt'
assert 'Missing tests' in bp, 'Evaluator feedback missing from builder prompt'

# Constitution must come first
constitution_pos = bp.find('# Rules')
plan_pos = bp.find('# Build an API')
assert constitution_pos < plan_pos, 'Constitution must come before plan'

# Changelog summarization: last 3 in full, first 4 summarized
assert 'output 7' in bp, 'Latest changelog entry should be in full'
assert 'output 6' in bp, 'Second-latest changelog entry should be in full'
assert 'output 5' in bp, 'Third-latest changelog entry should be in full'
# Entries 1-4 should be summarized (one-liners, not full output)

# Evaluator prompt
ep = cb.build_evaluator_prompt(ctx, 'Builder produced this code...')
assert '# Rules' in ep, 'Constitution missing from evaluator prompt'
assert 'Builder produced this code' in ep, 'Builder output missing from evaluator prompt'
assert '<success' in ep or 'success' in ep.lower(), 'Evaluator prompt should mention XML format'

# Resume prompt
rp = cb.build_resume_prompt(ctx, 'original prompt here', 'User says: use PostgreSQL')
assert 'original prompt here' in rp, 'Original prompt missing from resume'
assert 'use PostgreSQL' in rp, 'User response missing from resume'

print('✅ Phase 6: All context builder checks passed')
"
```

---

## Phase 7: Orchestrator

### Files: `orchestrator.py`

🔍 **Code review:**
- [ ] `Orchestrator` class accepts: `transport`, `memory`, `agents`, `context_builder`
- [ ] State machine has all states from `TaskStatus` enum
- [ ] `_run_agent()` creates a NEW `ClaudeSDKClient` session each time (verify no session reuse)
- [ ] `_parse_verdict()` handles all three XML tags: `<success>`, `<failure>`, `<waiting_for_user_input>`
- [ ] On `<waiting_for_user_input>`: calls `transport.publish_waiting()`, then `transport.await_user_input()`
- [ ] On `<waiting_for_user_input>`: does NOT increment iteration counter
- [ ] On `<failure>`: re-fetches context from memory before next iteration
- [ ] On XML parse failure: re-runs agent ONCE (does not count as iteration), then logs error
- [ ] Memory-service failure → `waiting` state (not `failed`), does not burn iteration
- [ ] SIGTERM handler: sets `shutting_down` flag, finishes current session with 60s timeout
- [ ] Final output published to MQTT only on `<success>` or max iterations exhausted (never intermediate)
- [ ] Max iterations read from `MAX_ITERATIONS` env var

⚡ **Unit test** (with mocks):
```bash
python -c "
# This test uses mock transport and mock memory
# Verify the state machine transitions and verdict parsing

from microharness.orchestrator import Orchestrator

# Test verdict parsing
orch = Orchestrator.__new__(Orchestrator)  # bypass __init__

# Parse success
v = orch._parse_verdict('<success subtasks_completed=\"s1,s2\" confidence=\"0.9\">All good</success>')
assert v.decision == 'success', f'Expected success, got {v.decision}'
assert 's1' in v.subtasks_completed
assert v.confidence == 0.9

# Parse failure
v = orch._parse_verdict('<failure subtasks_completed=\"s1\" subtasks_remaining=\"s2\" confidence=\"0.7\">Fix s2</failure>')
assert v.decision == 'failure', f'Expected failure, got {v.decision}'
assert 's2' in v.subtasks_remaining

# Parse waiting_for_user_input
v = orch._parse_verdict('<waiting_for_user_input context=\"db_choice\">Which database?</waiting_for_user_input>')
assert v.decision == 'waiting_for_input', f'Expected waiting_for_input, got {v.decision}'
assert 'Which database?' in v.question

# Parse invalid XML
v = orch._parse_verdict('This is not XML at all, just plain text.')
assert v is None, 'Should return None for unparseable output'

print('✅ Phase 7: All orchestrator verdict parsing checks passed')
"
```

---

## Phase 8: Wire Everything

### Files: `core.py`, `cli.py`, `__init__.py`

🔍 **Code review:**
- [ ] `core.py` has no `import dotenv` statement
- [ ] `core.py` has `run_mqtt()` function that wires all components
- [ ] `core.py` keeps `run_repl()` for backward compatibility
- [ ] `cli.py` uses `argparse` with `--mode {repl, mqtt}`, `--role`, `--max-iterations`
- [ ] `cli.py` defaults to `mqtt` mode when `HARNESS_ROLE` env var is set
- [ ] `__init__.py` exports key classes: `Orchestrator`, `MQTTTransport`, `MemoryClient`, `TaskContext`, `ContextBuilder`

⚡ **Unit test:**
```bash
# Verify imports work
python -c "
from microharness import Orchestrator, MQTTTransport, MemoryClient, TaskContext, ContextBuilder
print('✅ Phase 8: All imports work')
"

# Verify CLI help
python main.py --help
# Expected: shows --mode, --role, --max-iterations options
```

---

## Phase 9: Infrastructure

### Files: `Dockerfile`, `docker-compose.yml`, `pyproject.toml`

🔍 **Code review:**
- [ ] `Dockerfile` uses `python:3.13-slim` base
- [ ] `Dockerfile` installs `uv` and uses `uv sync --frozen`
- [ ] `Dockerfile` does NOT use `pip install`
- [ ] `docker-compose.yml` has services: `mosquitto`, `memory-mock`, `harness`
- [ ] `mosquitto` service has health check
- [ ] `harness` service has `depends_on: mosquitto: condition: service_healthy`
- [ ] `pyproject.toml` has all 6 dependencies from PLAN.md
- [ ] `pyproject.toml` does NOT list `python-dotenv`
- [ ] `pyproject.toml` has `requires-python = ">=3.13"`

🚀 **E2E test:**
```bash
# Build everything
docker compose build
# Expected: all services build without errors

# Start everything
docker compose up -d
# Expected: all services start

# Verify services are healthy
docker compose ps
# Expected: mosquitto (healthy), memory-mock (running), harness (running)

# Verify MQTT broker
docker compose exec mosquitto mosquitto_sub -t 'swarm/heartbeat' -C 1 -W 35
# Expected: receives a heartbeat JSON message within 35 seconds

# Verify memory-mock
curl -s http://localhost:8001/tasks/nonexistent
# Expected: 404 response

# Cleanup
docker compose down -v

echo "✅ Phase 9: Infrastructure checks passed"
```

---

## Phase 10: Auth Mock

### Files: `services/auth-mock/`

🔍 **Code review:**
- [ ] FastAPI app with `POST /auth/token` endpoint
- [ ] Returns a JWT (can be a static/dummy token for dev)
- [ ] Dockerfile builds and runs

🔌 **Integration test:**
```bash
cd services/auth-mock && docker build -t auth-mock . && docker run -d -p 8002:8002 --name auth-mock-test auth-mock

curl -s -X POST http://localhost:8002/auth/token \
  -H "Content-Type: application/json" \
  -d '{"client_id": "harness-001", "role": "backend-engineering"}' | python -m json.tool
# Expected: JSON with "token" field

docker stop auth-mock-test && docker rm auth-mock-test
echo "✅ Phase 10: Auth mock checks passed"
```

---

## Phase 11: Full End-to-End Validation

🚀 **E2E test — the complete flow:**

### Setup
```bash
docker compose up -d
sleep 5  # wait for services to stabilize
```

### 1. Seed a test task
```bash
curl -s -X POST http://localhost:8001/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "e2e-test-uuid-001",
    "role": "backend-engineering",
    "plan": "# Build User API\n\nCreate a REST API with CRUD endpoints for user management.\n\n## Requirements\n- GET /users - list all users\n- POST /users - create user\n- GET /users/:id - get user by ID",
    "constitution": "# Constitution\n\n1. All endpoints must use async/await\n2. Input validation required on all POST/PUT endpoints\n3. Return proper HTTP status codes\n4. Include error handling",
    "subtasks": "- [ ] Create GET /users endpoint\n- [ ] Create POST /users endpoint\n- [ ] Create GET /users/:id endpoint\n- [ ] Add input validation\n- [ ] Add error handling",
    "metadata": {"status": "pending", "priority": "high"}
  }'
```

### 2. Subscribe to all harness topics (in a separate terminal)
```bash
# Terminal 2: watch all swarm traffic
docker compose exec mosquitto mosquitto_sub -t 'swarm/#' -v
```

### 3. Assign the task
```bash
docker compose exec mosquitto mosquitto_pub \
  -t 'swarm/backend-engineering/tasks' \
  -m '{"id": "msg-001", "type": "assign_task", "task_id": "e2e-test-uuid-001", "payload": {"priority": "high"}}'
```

### 4. Verify expected behavior

**Status updates (on `swarm/{harness_id}/status`):**
- [ ] Received `state: "initializing"` after task assignment
- [ ] Received `state: "building"` with `iteration: 1`
- [ ] Received `state: "evaluating"` with `iteration: 1`
- [ ] Received either `state: "complete"` or `state: "building"` (iteration 2)

**Events (on `swarm/{harness_id}/events`):**
- [ ] Received streaming events during builder execution
- [ ] Received streaming events during evaluator execution

**Heartbeats (on `swarm/heartbeat`):**
- [ ] Receiving periodic heartbeats with correct `role`, `state`, `task_id`

**Final output (on `swarm/{harness_id}/output`):**
- [ ] Received exactly ONE message on output topic
- [ ] Message has `type: "task_result"` with `outcome: "success"` or `outcome: "failure"`

**Memory-service verification:**
```bash
# Verify changelog was written
curl -s http://localhost:8001/tasks/e2e-test-uuid-001/changelog | python -m json.tool
# Expected: at least 2 entries (1 builder + 1 evaluator per iteration)

# Verify status was updated
curl -s http://localhost:8001/tasks/e2e-test-uuid-001 | python -m json.tool | grep status
# Expected: "complete" or "failed"
```

### 5. Test graceful shutdown
```bash
docker compose stop harness
# Then check memory-mock for partial results if harness was mid-iteration
```

### 6. Test concurrent task rejection (option C)
```bash
docker compose up -d harness
sleep 2

# Assign first task
docker compose exec mosquitto mosquitto_pub \
  -t 'swarm/backend-engineering/tasks' \
  -m '{"id": "msg-002", "type": "assign_task", "task_id": "e2e-test-uuid-001", "payload": {}}'

sleep 1

# Assign second task while first is running
docker compose exec mosquitto mosquitto_pub \
  -t 'swarm/backend-engineering/tasks' \
  -m '{"id": "msg-003", "type": "assign_task", "task_id": "e2e-test-uuid-002", "payload": {}}'

# Expected: second task is IGNORED (no status update for e2e-test-uuid-002)
# Heartbeat should still show e2e-test-uuid-001 as current task
```

### Cleanup
```bash
docker compose down -v
echo "✅ Phase 11: Full E2E validation complete"
```

---

## Quick Reference: Evaluation Checklist

| Phase | Type | Pass Condition |
|---|---|---|
| **1** | 🔍 ⚡ | Data models instantiate, enums have all values, no dotenv |
| **2** | 🔍 ⚡ | Agent configs load, YAML parses, XML tags in system prompts |
| **3** | 🔍 🔌 | All 9 endpoints work, file storage persists, seed/fetch/update cycle works |
| **4** | 🔍 🔌 | Async client fetches `TaskContext`, retry logic present, custom exceptions |
| **5** | 🔍 🔌 | MQTT pub/sub works, QoS 2, heartbeat publishes, waiting topic works |
| **6** | 🔍 ⚡ | Prompts assembled correctly, constitution first, changelog summarized |
| **7** | 🔍 ⚡ | All 3 XML tags parsed, state transitions correct, no iteration burn on waiting |
| **8** | 🔍 ⚡ | Imports work, CLI help shows options, no dotenv |
| **9** | 🔍 🚀 | Docker builds, compose up works, services healthy |
| **10** | 🔍 🔌 | Auth endpoint returns token |
| **11** | 🚀 | Full flow: assign → build → evaluate → output. Shutdown, concurrency handled |
