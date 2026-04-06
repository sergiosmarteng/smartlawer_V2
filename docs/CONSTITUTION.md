# Microharness — Constitution

> **Non-negotiable rules.** These decisions are final and must be followed by any agent
> implementing this project. Do NOT deviate from these rules without explicit human approval.
> If a rule conflicts with implementation reality, document the conflict in `CHANGELOG.md`
> and ask the human for a decision.

---

## Architecture Rules

1. **Microharness is a stateless worker.** Each agent invocation (TaskBuilder, TaskEvaluator) creates a NEW `ClaudeSDKClient` session. No persistent conversation state. All continuity comes from the Memory API.

2. **Microharness only knows tasks and sub-tasks.** It does NOT know about stories, features, epics, sprints, or any other project management concept. It receives a `task_id` UUID and that's it.

3. **MQTT for coordination, Memory API for data.** MQTT messages carry only identifiers and lightweight metadata. All task artifacts (plan.md, constitution.md, tasks.md, changelog) are owned by memory-service and fetched via REST API.

4. **Output topic is terminal only.** The `swarm/{harness_id}/output` MQTT topic is published to **exactly once** per task — when the task reaches a terminal state (success or failure after max iterations). Never publish intermediate results to the output topic.

5. **Re-fetch context every iteration.** Before each builder→evaluator cycle, the orchestrator must fetch fresh context from memory-service. Other swarm workers may have modified shared artifacts.

6. **Container specialization via volume mounts.** The Docker image is always the same. Behavior changes by mounting different `config/agents/*.md` files and setting `HARNESS_ROLE`. Note: `.claude/agents/` is for Claude Code dev-time agents only — runtime configs go in `config/agents/`.

7. **Auth and memory are separate services.** The harness container does NOT contain authentication logic or a token endpoint. These are separate microservices (mocked in dev).

---

## Coding Standards

8. **Python 3.13.** Use modern Python features: `type` unions (`str | None`), dataclasses, `match` statements where appropriate.

9. **Async everywhere.** All I/O operations use `async/await`. No blocking calls in the event loop.

10. **Type hints on all public APIs.** Every public function, method, and class attribute must have type annotations.

11. **Dataclasses for data, ABCs for interfaces.** Use `@dataclass` for value objects. Use `ABC` with abstract methods for interfaces (Transport, MemoryClient).

12. **No hardcoded values.** All configuration comes from environment variables with sensible defaults. See PLAN.md for the full env var table.

13. **Structured logging.** Use Python's `logging` module. Log at INFO for state transitions, DEBUG for detailed events, ERROR for failures. Include `task_id`, `harness_id`, and `iteration` in log context.

14. **Test-Driven Development (TDD).** Write tests BEFORE implementation. Every module in `src/microharness/` must have a corresponding `tests/test_<module>.py`. The cycle is: write test → run (expect fail) → implement → run (expect pass). All tests must pass (`python -m pytest tests/ -v`) before handing off to the evaluator. Use `pytest` as the test framework.

---

## MQTT Rules

15. **QoS 2 for all topics.** Exactly-once delivery. No exceptions.

16. **Topic hierarchy: `swarm/`** prefix for all topics. See PLAN.md for the full topic design.

17. **Heartbeats every 30 seconds.** Include: `harness_id`, `role`, `state`, `task_id` (null if idle), `uptime_seconds`, `timestamp`.

---

## Agent Rules

18. **Both agents can return XML tags.** TaskBuilder and TaskEvaluator can return `<success>`, `<failure>`, or `<waiting_for_user_input>`. The agent's system prompt must enforce this with examples of each tag.

19. **Constitution injected first.** In every prompt sent to an agent, the task's constitution.md is the FIRST section, clearly delimited as non-negotiable.

20. **Changelog summarization.** Only the last N iterations (default 5, configurable via `MAX_CHANGELOG_ENTRIES`) are included in full. Older iterations are condensed to one-line summaries.

21. **`<waiting_for_user_input>` pauses, never burns.** When an agent returns `<waiting_for_user_input>`, the orchestrator publishes the question to the `waiting` MQTT topic, transitions to `waiting_for_input` state, and waits indefinitely for a `user_input` message on the control topic. This does NOT count as a failed iteration. The same agent is re-run with the user's response injected.

22. **`<waiting_for_user_input>` has a `context` attribute.** The XML tag must include a `context` attribute (e.g., `context="architecture_decision"`) so the dashboard/external tool can categorize the question.

---

## Error Handling Rules

23. **Infrastructure failures don't burn iterations.** If memory-service or MQTT is unreachable, the orchestrator enters a `waiting` state. It does NOT count this as a failed iteration.

24. **Graceful shutdown on SIGTERM.** The container must handle `SIGTERM` by finishing the current SDK session (timeout 60s), storing partial results, publishing shutdown status, and exiting cleanly.

25. **Concurrent tasks are ignored.** If a task arrives while busy, the harness ignores it (does not acknowledge). No queue, no rejection message. The task-manager handles re-routing.

---

## Dependency Rules

26. **Minimal dependencies.** The harness container uses ONLY: `claude-agent-sdk`, `colorama`, `aiomqtt`, `aiohttp`, `pyyaml`, `python-frontmatter`. Dev dependencies: `pytest`, `pytest-asyncio`. No FastAPI, no JWT libraries — those belong to mock services.

27. **No `python-dotenv`.** Environment variables are managed by Docker. Do not use or import `dotenv` anywhere.

28. **`uv` for dependency management.** Use `uv sync --frozen` in Docker builds. Do not use `pip install` directly.
