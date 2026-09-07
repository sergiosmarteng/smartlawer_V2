---
name: token-saver
description: Reduce token usage during OpenCode sessions by reading files selectively, summarizing context, avoiding unnecessary output, and preserving only task-critical information.
license: MIT
compatibility: opencode
metadata:
  category: context-optimization
  stack: cross-stack
  version: "1.0.0"
orchestration:
  lead_for:
    - token-compression
  support_for: []
  conflicts_with:
    - context-engineering
---

# Token Saver

Use this skill during any OpenCode session where context limits or costs are a concern, especially for large repositories, long-running tasks, or sessions with many file reads.

The objective is to minimize token consumption without losing the information needed for correctness, safety, and effective decision-making.

## Selective File Reading

* Read only the files you need for the current task step.
* Prefer reading specific sections of a file over the entire file.
* Use `grep` to locate relevant symbols, imports, or function definitions before reading.
* Use `glob` to find relevant files before opening them.
* When a file is very large, read a limited range of lines around the relevant area.
* Read the file's imports and type signatures first; only read the full body when necessary.
* For config files, read only the sections relevant to the current change.
* For test files, read only the test cases related to the failing behavior.

## Lazy Context Loading

* Load context incrementally as the task progresses, not all at once.
* Start with the task description and the most directly relevant file.
* Read dependent files only when you have identified what you need from them.
* Do not read every file in a directory before deciding where to make changes.
* Do not load every skill at the start of a session. Load only skills relevant to the current step.
* When a file's content is predictable from its name or imports, skip reading it unless the content is needed for correctness.

## Avoid Full-File Dumps

* Do not output the entire content of a file in your response unless the user explicitly asks.
* When showing changes, output only the modified sections, not the whole file.
* Prefer `edit` tool usage with targeted replacements over showing large blocks of context.
* When referencing a location, use `file_path:line_number` instead of reprinting the line.
* When debugging, show only the relevant stack frames, not the entire traceback.

## Use grep and glob Before Reading Large Files

* Before reading a large file, use `grep` to find the exact function, class, or variable name you need.
* Use `glob` to find files by pattern without reading directory listings.
* Search for error messages or log patterns to pinpoint the failing location before reading surrounding code.
* When exploring an unknown codebase, start with `grep` for key terms instead of reading files sequentially.

## Summarize Discovered Context

* After reading and understanding a file, store a concise summary of what it contains and why it is relevant.
* Keep a running task context summary in your internal state, not in the response stream.
* Include in the summary:
  * files inspected
  * key facts discovered
  * decisions made
  * open questions
  * next actions
* Update the summary as new information replaces or refines old information.

## Maintain a Task Context Summary

* Keep an internal summary that grows as the task progresses.
* Remove information that is no longer relevant as you narrow down the problem.
* Replace vague descriptions with precise facts once confirmed.
* At each response, include a compact context block that lets the user (and future turns) pick up without re-reading earlier exchanges.

## Avoid Repeated Explanations

* Do not re-explain the same concept, architecture, or decision across multiple responses.
* Once you have described a fact or decision, reference it briefly without re-listing all supporting details.
* When the user asks a follow-up, do not reprint all previous context.
* Use references like "as established in the previous step" instead of restating.

## Compact Reporting

* Keep responses concise. Prefer one paragraph or a brief list over long prose.
* Do not include preamble, disclaimers, or meta-commentary about what you are about to do.
* Use lists instead of paragraphs when listing multiple items.
* Use code blocks only when showing exact code, commands, or errors.
* Do not repeat the user's question or request back to them.
* Do not add concluding summaries unless the task is complete.

## Do Not Load All Skills Unnecessarily

* Load only the skills relevant to the current step.
* For a Python bug fix, you likely need `python-quality` and `testing-and-debugging`. You do not need `nextjs-frontend`, `ui-ux-design`, or `production-readiness`.
* When switching tasks, unload irrelevant skills from your active set.
* If a skill's guidance overlaps with another, prefer the more specific one.

## Do Not Read Generated Files Unless Required

* Skip `node_modules/`, `__pycache__/`, `.next/`, `dist/`, `build/`, `.venv/`, `*.pyc`, `*.lock`, and similar generated or transient files.
* Read lockfiles only when diagnosing dependency issues.
* Read compiled or minified files only when source maps are unavailable and the issue cannot be reproduced from source.
* Read log files only when they contain the exact error you are diagnosing.

## Avoid Huge Logs

* Do not read entire log files. Use `grep` or `tail` to find the relevant entries.
* When logs are very large, read a bounded window around the error timestamp.
* Summarize log patterns instead of reproducing them verbatim.
* Use `rg --context` to show only a few lines around each match.

## Handling Large Stack Traces

* Read only the first relevant application frame and the error message.
* Ignore framework-internal frames unless the issue is in the framework itself.
* Present only the essential frames in your response.
* State the exception type and message, then point to the relevant line in your own code.

## Read Only Relevant Test Failures

* When a test suite fails, do not read every failure message.
* Identify the test that is relevant to your current change.
* Read only the assertion and the relevant setup for that test.
* When running tests, capture only the failing output, not the full pass/fail summary.
* Use `pytest -k` or `--failed-first` to run only relevant tests.

## Using Repository Maps

* Build a mental map of the repository structure as you explore.
* Record the location of key entry points, data models, API routes, and configuration files.
* Use this map to navigate directly to relevant code instead of scanning directories.
* Update the map when you discover new important locations.

## Produce Concise Final Reports

* When the task is complete, produce a short summary.
* Include only:
  * what was changed
  * why it was changed
  * verification performed
  * any remaining limitations
* Do not include step-by-step replay of the work, rejected approaches, or verbose explanations.

## Preserve Important Decisions

* When you make a design decision, record the rationale briefly.
* Keep a compact log of:
  * major decisions
  * rejected alternatives and why
  * assumptions that could be invalidated later
  * configuration, environment, or dependency constraints
* This log helps avoid re-deriving the same conclusions in future turns.

## Context Handoff Between Sessions

* When a task spans multiple sessions, prepare a handoff summary.
* The handoff should include:
  * current state of the task
  * files changed so far
  * decisions made
  * open issues
  * next action
  * any commands to re-run
* Keep the handoff to one paragraph if possible.

## Safe Limitations

* Do not skip required verification just to save tokens.
* Do not delete context that is needed for correctness.
* Do not ignore errors or assume they are safe.
* Do not stop reading a file before you have found the information you need.
* When summarizing, preserve exact file names, line numbers, error messages, and command output.
* Keep the full text of any error message that you do not yet understand.

## Do Not

* Do not skip required verification to save tokens.
* Do not ignore errors or assume they are safe.
* Do not guess instead of reading the relevant code.
* Do not hide uncertainty.
* Do not summarize away exact file names, commands, or failing errors.
* Do not output a file's entire content unless the user explicitly requests it.
* Do not re-read files you have already summarized unless the summary is stale.
* Do not load every skill at the start of a session.
* Do not truncate or omit information that changes the meaning of a result.
* Do not make assumptions about code you have not read.
* Do not present a summary as a substitute for reading critical code paths.

## Required Output Format

When reporting status or completing a step, produce output in this compact format:

```text
Context used:
[Which skills are active and which files are currently loaded in context.]

Files inspected:
[List of files read in this session, with a one-line summary of what each contains.]

Important facts retained:
[Key findings, decisions, error messages, and configuration values that remain relevant.]

Details intentionally skipped:
[What was not read or was summarized away, and why it was safe to skip.]

Next minimal action:
[The single next step, expressed as a command or a specific file to read or edit.]

Verification status:
[What has been verified, what has not, and what command would confirm correctness.]
```

## Completion Criteria

A token-efficient session is complete only when:

* every file read was necessary
* no important context was discarded
* all decisions are supported by evidence from read files
* no errors were ignored
* the response uses minimal tokens for the information conveyed
* the user can understand the current state without re-reading earlier turns
* remaining uncertainty is disclosed
* verification was not skipped to save context
