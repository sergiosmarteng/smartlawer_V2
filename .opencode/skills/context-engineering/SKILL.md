---
name: context-engineering
description: Build, preserve, compress, and reuse task context across complex OpenCode sessions without losing decisions, constraints, risks, or verification state.
license: MIT
compatibility: opencode
metadata:
  category: context-management
  stack: cross-stack
  version: "1.0.0"
orchestration:
  lead_for:
    - token-compression
    - session-handoff
  support_for: []
  conflicts_with:
    - token-saver
---

# Context Engineering

Use this skill when working on long-running or complex tasks that span multiple responses, files, or sessions. This includes:

* multi-file refactors
* bug investigations with many moving parts
* feature implementation across backend and frontend
* production-readiness reviews
* handoff between sessions or agents
* tasks where context limits are a constraint

The objective is to build and maintain a high-quality internal context model that preserves every decision, constraint, risk, and verification result without requiring the user to repeat information or re-reading large sections of prior conversation.

## When to Load This Skill

Load `context-engineering` whenever the task is likely to:

* require more than five file reads
* involve multiple interconnected components
* span more than one conversation turn
* need handoff to another session or agent
* involve decisions that affect later steps

Do not load this skill for trivial single-file edits or simple questions.

## Context Model

Maintain an internal context model with the following fields. Update it after every meaningful discovery or decision.

```text
Goal:
The single objective of the current task. Do not change mid-task without explicit user direction.

Constraints:
Time, tool, permission, environment, or policy limits that affect how the task can be solved.

Repository facts:
Project structure, framework version, database schema, API contracts, configuration files, and relevant architecture decisions.

Files inspected:
Every file read, with a one-line summary of what it contains and why it was relevant.

Decisions made:
Every choice between alternatives, including the rejected option and the reason.

Current hypotheses:
Active theories about the cause of a bug or the best implementation approach. Label each as "confirmed", "likely", or "unconfirmed".

Rejected hypotheses:
Theories that were tested and disproven, with the evidence that ruled them out.

Commands run:
Every command executed, its output summary, and whether it passed or failed.

Verification status:
What has been verified, what has not, and what specific command would confirm correctness.

Remaining risks:
Anything that could go wrong, including edge cases, untested paths, environment differences, or unvalidated assumptions.

Next action:
The single next step. If blocked, explain why and what would unblock.
```

## Building Context

* Start by reading the entry point and configuration files to establish the architecture.
* Record the framework version, database dialect, testing tools, and build system.
* Identify the relevant models, routes, services, and tests.
* As you read each file, update `Files inspected` and `Repository facts`.
* When you find an error, record it verbatim in `Key facts`.
* When you find a constraint, add it to `Constraints`.
* Before making a decision, enumerate the alternatives and the criteria for choosing.

## Context Compression

When running out of context or preparing a handoff, compress aggressively while preserving essential information.

### Preserve Exactly

* Exact error messages and stack frames from your own code.
* File paths and line numbers for every relevant location.
* Commands run and their exit status.
* API contracts, request and response shapes.
* Schema definitions, migration names, and constraint details.
* Configuration values that differ from defaults.
* Test names and their pass/fail status.

### Summarize Aggressively

* Repeated log lines. Replace with "Logged N times: [pattern]".
* Exploration that led nowhere. Keep only the rejected hypothesis and the evidence that ruled it out.
* Framework-internal stack frames. Keep only the first relevant application frame.
* Long lists of similar items. Summarize with counts and representative examples.
* Verbatim code that you have already inspected. Replace with file:line references.

### Never Remove

* The task goal and active constraints.
* Unresolved questions or assumptions.
* Commands that still need to be run.
* Error messages you do not yet understand.
* Evidence that contradicts your current hypothesis.

## Context Refresh

Before making the final changes or running final verification:

* Re-read files that may have changed since you first inspected them.
* Run `git diff` or `git status` to detect uncommitted changes.
* Re-run the relevant test command to get fresh output.
* Check whether any constraints changed (environment, permissions, dependencies).
* Do not rely on stale summaries for the final edit.

After a context refresh, update `Files inspected` with fresh read times and mark any stale entries.

## Handoff Preparation

When a task will continue in another session or by another agent, produce a handoff document using the context snapshot template below.

The handoff must allow the recipient to start working without reading any prior conversation.

## Required Output Template

When reporting the current state at any point, use this compact format:

```text
Context snapshot:

Goal:
[Single sentence describing the objective.]

Constraints:
[Time, tool, environment, or policy limits still in effect.]

Files inspected:
[file:path — one-line summary]
[file:path — one-line summary]

Key facts:
[Error messages, configuration values, framework versions, architecture facts.]

Decisions:
[What was decided, what was rejected, and why.]

Open questions:
[Unresolved issues or assumptions that need validation.]

Verification:
[What passed, what failed, what has not been tested, and the command to confirm.]

Next action:
[The single next step and, if blocked, what is needed to proceed.]
```

## Do Not

* Do not modify the context model by removing constraints, risks, or open questions without evidence.
* Do not delete error messages or failed command output from the context.
* Do not assume a hypothesis is confirmed without evidence.
* Do not keep hypotheses that have been disproven.
* Do not skip context refresh before final edits or verification.
* Do not produce a handoff that omits commands that need to be re-run.
* Do not summarize away information that could affect correctness.
* Do not keep exploration history that no longer serves the current goal.

## Completion Criteria

Context engineering is complete only when:

* the context model accurately reflects the current state of the task
* every decision is supported by evidence
* all commands run and their results are recorded
* remaining risks and open questions are explicit
* a handoff can be produced from the context model without re-reading prior turns
* no essential information was discarded during compression
* stale summaries have been refreshed before the final action
* the next action is clear and actionable
