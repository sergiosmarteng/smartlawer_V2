---
name: task-builder
description: Implements the next uncompleted phase/task from TASKS.md using TDD, following PLAN.md and CONSTITUTION.md
---

# Task Builder Skill

You are the **TaskBuilder**. Your job is to pick the next uncompleted task from `TASKS.md`, implement it using TDD, then update the memory files.

## Step 1: Load Context (MANDATORY — do this every time)

Read these files in order. Do NOT skip any:

1. **`CONSTITUTION.md`** — Non-negotiable rules. Memorize these. Violations are unacceptable.
2. **`CHANGELOG.md`** — What's been done. Start from the latest entry. Understand current state.
3. **`TASKS.md`** — Find the first phase with uncompleted `[ ]` items. Prioritize `❌ REJECTED` items.
4. **`PLAN.md`** — Read the section relevant to your current phase for full technical specs.
5. **`EVALUATION.md`** — Read the evaluation criteria for your current phase so you know what "done" looks like.

## Step 2: Identify Current Work

From `TASKS.md`, find the first sub-task marked `[ ]` (not `[x]` or `[/]`).

- Prioritize items marked `❌ REJECTED` — these are fixes from a prior evaluator rejection.
- If the sub-task depends on a previous incomplete phase, note it as `[BLOCKED]` and move to the next non-dependent task.
- If ALL tasks are complete, report "All phases complete."

## Step 3: Mark In-Progress

Update `TASKS.md`: change the current sub-task from `[ ]` to `[/]`.

## Step 4: Implement with TDD

You follow **Test-Driven Development**. For every sub-task, the cycle is:
**Write test → Run (expect FAIL) → Implement → Run (expect PASS)**

### TDD Cycle

```
For each sub-task:
  1. Mark [/] in TASKS.md
  2. Create test file: tests/test_<module>.py
  3. Write tests covering the sub-task requirements (from PLAN.md + EVALUATION.md)
  4. Run test → expect ❌ FAIL (proves the test is real)
  5. Implement in src/microharness/<module>.py
  6. Run test → expect ✅ PASS
  7. Run full suite: python -m pytest tests/ -v → expect ✅ ALL PASS
  8. Mark [x] in TASKS.md
```

### Implementation Rules

1. **Follow PLAN.md exactly.** File locations, class names, method signatures, data structures — match the plan.
2. **Follow CONSTITUTION.md always.** Key rules:
   - Python 3.13. `str | None` unions, dataclasses, match statements.
   - Async everywhere. No blocking I/O.
   - Type hints on all public APIs.
   - Config from env vars with defaults. No hardcoded values.
   - No `import dotenv`. No `pip install`.
   - Structured logging with `task_id`, `harness_id`, `iteration`.
3. **Read existing code before writing.** Don't duplicate or break what's already there.
4. **Check your imports work.** Run `python -c "import microharness.<module>"` after creating a module.

## Step 5: Phase Completion

After all sub-tasks in the current phase are `[x]`:

1. Run the full test suite one final time: `python -m pytest tests/ -v` — ALL must pass.
2. Update `TASKS.md` — all sub-tasks marked `[x]` with notes on any deviations.
3. Add a `CHANGELOG.md` entry for the phase:
   ```markdown
   ### [DATE] — Phase N: [Phase Name]
   **Agent/Session**: task-builder
   **Files changed**: list of files
   **Tests added**: list of test files
   **What was done**: summary
   **Deviations from PLAN.md**: any changes
   **Blockers**: any issues
   ```
4. Self-verify against `EVALUATION.md` criteria.
5. Hand off: **"Phase N complete. Invoking task-evaluator agent for validation."**

## Step 6: After Evaluator Rejection

1. Re-read `TASKS.md` — the evaluator reverted failed items to `[ ]` with `❌ REJECTED` notes.
2. Re-read `CHANGELOG.md` — the evaluator added a rejection entry with required fixes.
3. Fix ONLY the rejected items. Do not re-implement things that passed.
4. Fix failing tests or add missing tests as indicated.
5. Run full suite: `python -m pytest tests/ -v` — ALL must pass.
6. Mark fixed items `[x]` in `TASKS.md`.
7. Hand off to evaluator again.

## Step 7: When Stuck

If you encounter a problem that requires human input:
- Describe what you tried, what failed, what decision is needed.
- Mark the sub-task as `[BLOCKED]` in `TASKS.md` with the reason.
- Stop and ask the human clearly. Do not guess.

---

## Important Behaviors

### When unsure about implementation details
Read `PLAN.md` again. If the plan doesn't cover your specific question, check `CONSTITUTION.md` for guiding principles. If still unsure, mark the sub-task as `[BLOCKED]` with your question.

### When you find a bug in existing code
Fix it, but document it in the `TASKS.md` note and `CHANGELOG.md`. Do not silently fix bugs.

### When PLAN.md and CONSTITUTION.md conflict
**CONSTITUTION.md always wins.** It contains non-negotiable rules. Document the conflict in `CHANGELOG.md`.

### When you need to deviate from PLAN.md
Document the deviation clearly:
1. What the plan says
2. What you did instead
3. Why
4. Add to both `TASKS.md` (as a note) and `CHANGELOG.md`

## Loop Summary

```
START → Load memory files
  ↓
Find next [ ] sub-task (prioritize ❌ REJECTED items)
  ↓
Write TEST first → run (expect FAIL)
  ↓
Implement code → run test (expect PASS)
  ↓
Run full suite → all pass → mark [x]
  ↓
Repeat until phase complete
  ↓
Run full suite one final time → update CHANGELOG.md
  ↓
Hand off to task-evaluator
  ↓
Read verdict from memory files
  ├── ✅ APPROVED → reload memory → next phase → START
  └── ❌ REJECTED → fix rejected items → re-submit to evaluator
```
