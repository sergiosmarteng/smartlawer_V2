# Microharness — Tasks

> **How to use this file:**
> - This is the sub-task checklist for implementing microharness.
> - Each phase has sub-tasks that should be completed in order (phases can be parallelized where noted).
> - **After completing a sub-task**: change `[ ]` to `[x]` and add a brief note if anything deviated from PLAN.md.
> - **After completing a phase**: run the evaluation steps in `EVALUATION.md` for that phase.
> - **After passing evaluation**: add a `CHANGELOG.md` entry.
> - **If blocked**: add a `[BLOCKED]` note explaining why and move to the next non-dependent task.
> - **Reference**: see `PLAN.md` for full specs, `CONSTITUTION.md` for rules, `EVALUATION.md` for acceptance criteria.
>
> **Status legend:** `[ ]` = todo, `[/]` = in progress, `[x]` = done, `[BLOCKED]` = blocked

---

## Phase 1: Core Data Models

- [x] Create `src/microharness/task_context.py`
  - [x] `TaskStatus` enum: `idle`, `initializing`, `building`, `evaluating`, `complete`, `failed`, `paused`, `waiting`, `waiting_for_input`, `shutting_down`
  - [x] `ChangeEntry` dataclass: `iteration`, `agent`, `timestamp`, `action`, `output`, `verdict`, `feedback`
  - [x] `TaskContext` dataclass: `task_id`, `role`, `plan`, `subtasks`, `constitution`, `changelog`, `current_iteration`, `status`, `max_retries`, `evaluator_feedback`, `user_input_response`
  - [x] `Verdict` dataclass: `decision` (success/failure/waiting_for_input), `confidence`, `subtasks_completed`, `subtasks_remaining`, `feedback`, `question` (for waiting)
  - [x] Note: Changed `ChangeEntry` from TypedDict to dataclass per CONSTITUTION rule #11. Changed `Message` from TypedDict to dataclass.
- [x] Create `src/microharness/transport.py`
  - [x] `Message` dataclass: `id`, `type`, `task_id`, `harness_id`, `role`, `iteration`, `payload`, `timestamp`
  - [x] `Transport` ABC with methods: `start()`, `stop()`, `receive()`, `send()`, `publish_event()`, `publish_status()`, `publish_heartbeat()`
  - [x] Note: Added `publish_waiting()` and `await_user_input()` methods as required by PLAN.md for user input handling.

---

## Phase 2: Agent Configuration Loader

- [x] Create `src/microharness/agent_loader.py`
  - [x] `AgentConfig` dataclass: `name`, `description`, `system_prompt`, `capabilities`, `tools`, `model`, `priority`, `hooks`
  - [x] `load_agent_configs(agents_dir)` function: scan `.claude/agents/*.md`, parse YAML frontmatter + markdown body
  - [x] Error handling: skip malformed files with warning, require at least `task_builder` and `task_evaluator`
- [x] Create `.claude/agents/task_builder.md` with YAML frontmatter + system prompt
- [x] Create `.claude/agents/task_evaluator.md` with YAML frontmatter + system prompt
  - [x] System prompt MUST enforce XML response format (`<success>`, `<failure>`, or `<waiting_for_user_input>` tags)
  - [x] Include examples of each XML tag in the system prompt

---

## Phase 3: Memory Mock Service

- [x] Create `services/memory-mock/` directory structure
- [x] Create `services/memory-mock/main.py` — FastAPI app implementing:
  - [x] `GET /tasks/{task_id}` — return full task context (plan, constitution, subtasks, changelog, metadata)
  - [x] `GET /tasks/{task_id}/plan` — return plan.md content
  - [x] `GET /tasks/{task_id}/constitution` — return constitution.md content
  - [x] `GET /tasks/{task_id}/subtasks` — return tasks.md content
  - [x] `GET /tasks/{task_id}/changelog` — return changelog entries
  - [x] `POST /tasks/{task_id}/changelog` — append changelog entry
  - [x] `PUT /tasks/{task_id}/subtasks` — update subtasks
  - [x] `PUT /tasks/{task_id}/status` — update task status
  - [x] `POST /memory/search` — stub RAG search (return empty for now)
  - [x] `POST /tasks` — create a new task (for seeding test data)
  - [x] File-based storage: JSON files under `/data/memory/{task_id}/`
- [x] Create `services/memory-mock/Dockerfile`
- [x] Create `services/memory-mock/requirements.txt` (fastapi, uvicorn)
- [x] Seed script or fixture: create a sample task with plan, constitution, subtasks

---

## Phase 4: Memory Client

- [x] Create `src/microharness/memory.py`
  - [x] `MemoryClient` class with `aiohttp.ClientSession`
  - [x] `fetch_task_context(task_id)` → `TaskContext`
  - [x] `append_changelog(task_id, entry)` → None
  - [x] `update_subtasks(task_id, subtasks_md)` → None
  - [x] `update_status(task_id, status)` → None
  - [x] `search(query, top_k)` → list
  - [x] Retry policy: exponential backoff (configurable via env vars `MEMORY_RETRY_COUNT`, `MEMORY_RETRY_BACKOFF`)
  - [x] Proper error types: `MemoryServiceError`, `MemoryServiceUnavailable`
- [x] Create `tests/test_memory.py` with unit tests for MemoryClient (TDD requirement — must be written before implementation, but must be added now to complete phase)
- [x] Test against running memory-mock (memory-mock service started for evaluation; integration test passed)

---

## Phase 5: MQTT Transport

- [x] Create `infra/mosquitto/mosquitto.conf`
  - [x] MQTT listener on :1883
  - [x] WebSocket listener on :9001
  - [x] `allow_anonymous true` for dev
  - [x] Persistence enabled
- [x] Create `src/microharness/mqtt_transport.py` implementing `Transport` ABC
  - [x] Constructor: read all config from env vars
  - [x] `start()`: connect to broker, subscribe to `swarm/{role}/tasks` and `swarm/{harness_id}/control`
  - [x] `stop()`: unsubscribe, disconnect cleanly
  - [x] `receive()`: async queue, deserialize JSON → `Message`
  - [x] `send(message)`: publish to output topic, QoS 2
  - [x] `publish_event(event_type, data)`: publish to events topic
  - [x] `publish_status(state, iteration, agent)`: publish to status topic
  - [x] `publish_heartbeat()`: periodic heartbeat with `harness_id`, `role`, `state`, `task_id`
  - [x] `publish_waiting(question, context)`: publish to waiting topic when agent needs user input
  - [x] `await_user_input()`: listen on control topic for `type: "user_input"` response
  - [x] Reconnection with exponential backoff
  - [x] Ignore incoming tasks when not idle (concurrent task handling = option C)

---

## Phase 6: Context Builder

- [ ] Create `src/microharness/context_builder.py`
  - [ ] `ContextBuilder` class with configurable `max_changelog_entries`
  - [ ] `build_builder_prompt(ctx)` → string
    - [ ] Sections: CONSTITUTION → PLAN → SUBTASKS → CHANGELOG (summarized) → EVALUATOR FEEDBACK
    - [ ] Constitution delimited as non-negotiable
  - [ ] `build_evaluator_prompt(ctx, builder_output)` → string
    - [ ] Sections: CONSTITUTION → PLAN → SUBTASKS → BUILDER OUTPUT
    - [ ] Must instruct evaluator to respond with `<success>`, `<failure>`, or `<waiting_for_user_input>` XML
  - [ ] `build_resume_prompt(ctx, original_prompt, user_response)` → string
    - [ ] Re-injects the original prompt with the user's response appended
  - [ ] `_summarize_changelog(changelog)` → string
    - [ ] Last N entries in full, older entries as one-line summaries

---

## Phase 7: Orchestrator

- [ ] Create `src/microharness/orchestrator.py`
  - [ ] `Orchestrator` class with `transport`, `memory`, `agents`, `context_builder`
  - [ ] State machine: `idle` → `initializing` → `building` → `evaluating` → (loop or complete/failed)
  - [ ] `run()`: main event loop — await task assignments, call `_run_task_loop()`
  - [ ] `_run_task_loop()`: the iteration loop per PLAN.md
    - [ ] Fetch context from memory (with retry → waiting state)
    - [ ] Build prompt → run TaskBuilder (new SDK session) → store output
    - [ ] Build prompt → run TaskEvaluator (new SDK session) → parse XML verdict
    - [ ] On `<success>`: publish final output, mark complete
    - [ ] On `<failure>`: re-fetch context, iterate
    - [ ] On max iterations: publish failure output, go idle
  - [ ] `_run_agent(agent_name, prompt, ctx)`: fresh `ClaudeSDKClient` session, stream events, collect output, dispose
  - [ ] Handle `<waiting_for_user_input>` from either agent:
    - [ ] Publish question to `swarm/{harness_id}/waiting` topic
    - [ ] Transition to `waiting_for_input` state
    - [ ] Await response on control topic (`type: "user_input"`)
    - [ ] Re-run same agent with user response injected (does not count as iteration)
  - [ ] `_parse_verdict(agent_output)` → `Verdict`: XML parser for `<success>`, `<failure>`, `<waiting_for_user_input>`
  - [ ] On XML parse failure: re-run agent once with explicit XML instruction
  - [ ] `shutdown()`: SIGTERM handler — finish current session, store partial, exit
  - [ ] Signal handler setup: `SIGTERM`, `SIGINT`

---

## Phase 8: Wire Everything

- [ ] Modify `src/microharness/core.py`
  - [ ] Extract current config building into `build_options()` function
  - [ ] Add `run_mqtt()`: AgentLoader → MemoryClient → MQTTTransport → ContextBuilder → Orchestrator
  - [ ] Keep existing `run_repl()` for backward compatibility
  - [ ] Remove unused `import dotenv`
- [ ] Modify `src/microharness/cli.py`
  - [ ] Add `argparse`: `--mode {repl, mqtt}`, `--role`, `--max-iterations`, `--memory-url`
  - [ ] Default to `mqtt` when `HARNESS_ROLE` env var is set
  - [ ] Export `main()` function that calls `asyncio.run()`
- [ ] Modify `src/microharness/__init__.py`
  - [ ] Export: `Orchestrator`, `MQTTTransport`, `MemoryClient`, `AgentConfig`, `TaskContext`, `ContextBuilder`

---

## Phase 9: Infrastructure

- [ ] Modify `Dockerfile`
  - [ ] Base: `python:3.13-slim`
  - [ ] Install `uv` for dependency management
  - [ ] Copy `pyproject.toml` + `uv.lock` first (layer caching)
  - [ ] `EXPOSE 8000`
  - [ ] `HEALTHCHECK` using curl
  - [ ] `CMD ["python", "main.py", "--mode", "mqtt"]`
- [ ] Create `docker-compose.yml`
  - [ ] `mosquitto` service with health check
  - [ ] `memory-mock` service with volume
  - [ ] `harness` service with env vars, depends_on mosquitto healthy
  - [ ] Volumes: `memory-data`
- [ ] Modify `pyproject.toml`
  - [ ] Add dependencies: `aiomqtt`, `aiohttp`, `pyyaml`, `python-frontmatter`
  - [ ] Remove `dotenv` if listed
  - [ ] Ensure `requires-python = ">=3.13"`
- [ ] Test: `docker compose build` succeeds
- [ ] Test: `docker compose up` starts all services

---

## Phase 10: Auth Mock (low priority)

- [ ] Create `services/auth-mock/main.py` — FastAPI: `POST /auth/token` → JWT
- [ ] Create `services/auth-mock/Dockerfile`
- [ ] Create `services/auth-mock/requirements.txt` (fastapi, uvicorn, python-jose)
- [ ] Add to `docker-compose.yml`

---

## Phase 11: Testing & Verification

### Unit Tests
- [ ] `test_task_context.py`: serialization/deserialization, status transitions
- [ ] `test_agent_loader.py`: parse valid/invalid frontmatter, missing required agents
- [ ] `test_context_builder.py`: prompt assembly, changelog summarization, constitution injection
- [ ] `test_verdict_parser.py`: parse valid XML (`<success>`, `<failure>`, `<waiting_for_user_input>`), handle malformed XML

### Integration Tests
- [ ] `test_memory_client.py`: against running memory-mock (CRUD operations)
- [ ] `test_mqtt_transport.py`: against running Mosquitto (pub/sub, QoS 2)

### End-to-End Test
- [ ] `docker compose up` all services
- [ ] Connect MQTT client to `localhost:9001` (WebSocket)
- [ ] Seed memory-mock with test task (plan + constitution + sub-tasks)
- [ ] Subscribe to `swarm/+/status`, `swarm/+/events`, `swarm/+/output`
- [ ] Publish `assign_task` to `swarm/backend-engineering/tasks` with task_id UUID
- [ ] Verify: harness fetches context, runs builder, runs evaluator, iterates
- [ ] Verify: final result published on output topic
- [ ] Verify: results stored in memory-mock
- [ ] Verify: heartbeats publishing with correct state
- [ ] Test graceful shutdown: `docker compose stop harness`, verify partial result stored

---

## Phase 12: Multi-Agent Squad Setup (SmartLawer V2)

- [ ] Modify `src/microharness/agent_loader.py` to auto-load 8 specialized agents
- [ ] Implement Orchestrator iteration limits and routing (`project_leader`)
- [ ] Configure `software_architect`, `frontend_engineer`, `backend_engineer`, `integration_engineer`, `db_specialist`, `designer`, `reviewer` in `config/agents/`
- [ ] Test the pipeline routing task assignments among multiple agents
