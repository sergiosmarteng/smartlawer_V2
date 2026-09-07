---
name: skill-orchestrator
description: Select the right lead skill and supporting skills for a task, reduce overlapping instructions, control verbosity, and prevent unnecessary skill activation.
license: MIT
compatibility: opencode
metadata:
  category: meta
  stack: cross-stack
  version: "1.0.0"
orchestration:
  lead_for: []
  support_for: []
  conflicts_with: []
---

# Skill Orchestrator

Use this skill when starting any task that requires choosing which skills to activate. The objective is to select the correct skill combination while avoiding excessive overlap, verbosity, and over-cautious output.

## Core Rule

Follow these four rules for every task:

1. **Use exactly one lead skill.** The lead defines the workflow, output format, and verification depth.
2. **Use supporting skills only for their specialized checks.** A supporting skill contributes only the sections that the lead does not cover.
3. **Do not repeat the same guidance from multiple skills.** If two active skills overlap on a topic, the lead skill's instructions take precedence.
4. **Do not activate all skills by default.** Activate only what the task needs. Exclude skills whose domain is not touched.

## Skill Roles

### Lead Skill

One per task. Defines the task structure, output format, inspection depth, and verification scope. The lead is loaded first and its instructions take precedence over supporting skills on overlapping topics.

### Supporting Skill

Zero or more skills that fill domain-specific gaps the lead does not cover. A supporting skill activates only its unique sections and does not re-state guidance the lead already provides. It is excluded when its domain is not touched.

### Guardrail Skill

Zero or more skills activated only when specific conditions are met. Guardrails add checklist items and verification steps but do not change the lead skill's workflow or output format.

Common guardrails:

| Guardrail | Activate When |
|-----------|---------------|
| `security-review` | Task touches auth, authorization, user input, file upload, secrets, PII, external APIs, or AI/LLM output |
| `production-readiness` | Task is a release, deployment, migration, or infrastructure change |
| `token-saver` | Repository is large (>500 files) or session is long (>10 turns) |
| `context-engineering` | Task spans multiple sessions, requires handoff, or involves >5 interconnected files |

### Verification Skill

The skill responsible for running tests, linting, type checking, and builds. Usually `testing-and-debugging` when active. The lead skill defines the verification depth (focused, module, full). The verification skill does not add its own workflow unless it is the lead.

### Documentation Skill

A skill that defines output formatting, finding structure, or summary templates. The lead skill's output format takes precedence. Documentation skills are `code-review` (finding format) and `token-saver`/`context-engineering` (summary format).

## Task-to-Skill Routing

### Bug Fix

| Role | Skill | Notes |
|------|-------|-------|
| Lead | `testing-and-debugging` | |
| Support | Relevant stack skill | e.g. `fastapi-backend`, `sqlalchemy-postgres`, `nextjs-frontend` |
| Guardrail | `security-review` | Only if auth, secrets, user data, files, SQL, or external calls are involved |

### Python Cleanup

| Role | Skill | Notes |
|------|-------|-------|
| Lead | `python-quality` | |
| Support | `testing-and-debugging` | Only if tests or failures are involved |

### FastAPI Feature

| Role | Skill | Notes |
|------|-------|-------|
| Lead | `fastapi-backend` | |
| Support | `python-quality` | General Python quality |
| Support | `sqlalchemy-postgres` | Only if database code is touched |
| Guardrail | `security-review` | Only if auth, authorization, file upload, tenant, secrets, or untrusted input |

### Database Issue

| Role | Skill | Notes |
|------|-------|-------|
| Lead | `sqlalchemy-postgres` | |
| Support | `testing-and-debugging` | |
| Support | `fastapi-backend` | Only if API or session dependency is involved |

### Next.js Feature

| Role | Skill | Notes |
|------|-------|-------|
| Lead | `nextjs-frontend` | |
| Support | `ui-ux-design` | Only for visual, responsive, accessibility, or UX changes |
| Guardrail | `security-review` | Only if auth, cookies, tokens, secrets, server actions, route handlers, or private data are involved |

### UI Review

| Role | Skill | Notes |
|------|-------|-------|
| Lead | `ui-ux-design` | |
| Support | `nextjs-frontend` | Only for implementation feasibility |

### Code Review

| Role | Skill | Notes |
|------|-------|-------|
| Lead | `code-review` | |
| Guardrail | `security-review` | Only for security-sensitive areas |
| Support | Stack-specific skill | Only for the changed stack |

### Security Review

| Role | Skill | Notes |
|------|-------|-------|
| Lead | `security-review` | |
| Support | `code-review` | |
| Support | Stack-specific skill | Only for technical context |

### Production Review

| Role | Skill | Notes |
|------|-------|-------|
| Lead | `production-readiness` | |
| Guardrail | `security-review` | |
| Support | `sqlalchemy-postgres` | Only if database, migrations, or pool are relevant |

### Large Refactor

| Role | Skill | Notes |
|------|-------|-------|
| Lead | `code-review` | |
| Support | `testing-and-debugging` | |
| Support | Relevant stack skill | |
| Guardrail | `production-readiness` | Only if deployment behavior changes |

### Token Compression

| Role | Skill | Notes |
|------|-------|-------|
| Lead | `token-saver` | |
| Support | `context-engineering` | |
| Support | `repository-navigation` | Only if repo exploration is needed |

### AI Engineering

The lead skill depends on the specific AI task:

| Task Type | Lead Skill |
|-----------|------------|
| JSON / schema output | `structured-output-reliability` |
| LLM security | `llm-app-security` |
| Prompt injection risks | `prompt-injection-defense` |
| RAG pipeline | `rag-quality-review` |
| Evaluation | `ai-evaluation` |
| Model serving / deployment | `model-serving-production` |

Support: `python-quality` for Python implementation.
Guardrail: `security-review` always activated for AI features touching untrusted input.

## Verbosity Control

| Level | Description | Used For |
|-------|-------------|----------|
| `concise` | Summary only, no preamble | Small changes, confirmed quick fixes |
| `standard` | Key findings with brief context | Normal tasks, feature implementation |
| `detailed` | Full findings with severity, impact, fix | Reviews, debugging, security, production, or user request |

Default verbosity is `standard`. Escalate to `detailed` only for reviews, debugging, security, production, or when the user asks for detail.

## Overlap Suppression Rules

1. **Do not repeat generic testing rules from every skill.** Only `testing-and-debugging` (when lead or support) provides test workflow guidance. Other skills contribute only domain-specific test expectations.
2. **Do not repeat generic security rules unless `security-review` is lead or guardrail.** Stack-specific skills provide minimal security notes. Deep security analysis comes only from `security-review`.
3. **Do not repeat generic Python quality rules when a stack-specific skill already covers them.** `python-quality` provides broad Python guidance. `fastapi-backend` and `sqlalchemy-postgres` provide their own type and error-handling rules for their domain.
4. **Do not produce full checklists unless asked for a review.** For implementation or debugging tasks, produce findings as they arise rather than scanning a checklist.
5. **Prefer action-specific findings over broad advice.** Instead of "ensure proper error handling", state "catch `ValueError` from `parse_input()` and return 422".

## Output Format

When starting a task, produce a skill plan:

```text
Skill plan:
- Lead skill: [name]
- Supporting skills: [names or none]
- Guardrail skills: [names or none]
- Skills intentionally not used: [names]
- Reason: [why this combination was chosen]
- Verbosity: [concise / standard / detailed]
- Verification depth: [none / focused / module / full]
```

If the user asks for skill selection without a specific task, produce a standalone skill plan using the routing tables above.

## Completion Criteria

- the task has a lead skill
- supporting skills are scoped to their specialty
- overlap is minimized — no two active skills repeat the same guidance
- important safety checks are not skipped
- final output is not unnecessarily verbose

## New Skill Distinctness Test

Whenever proposing a new skill, command, tool, pack, or integration:

1. **Inventory existing capabilities first.**

2. **Compare by responsibility, not name.**

3. **A separate skill should normally have all of:**
   - a distinct trigger
   - a distinct primary responsibility
   - a distinct workflow
   - a distinct output format
   - distinct completion criteria
   - enough reusable guidance to justify independent loading

4. **Evaluate candidate overlap:**

   - **Low:** Less than roughly one-quarter of core responsibility overlaps.
   - **Medium:** Some shared concerns exist, but workflow and outputs are distinct.
   - **High:** Most responsibilities already exist elsewhere.

   These are qualitative judgments, not exact mathematical measurements.

5. **Decision rules:**

   - **Low overlap:** Separate skill may be appropriate.
   - **Medium overlap:** Consider a focused skill or extend the existing skill.
   - **High overlap:** Extend or improve the existing skill. Do not create a duplicate.

6. **Require this analysis:**

   ```
   Candidate:
   Primary responsibility:
   Existing nearest skill:
   Shared responsibilities:
   Distinct responsibilities:
   Distinct trigger:
   Distinct workflow:
   Distinct output:
   Overlap:
   Recommendation:
   - Create new skill
   - Extend existing skill
   - Merge proposal
   - Reject duplicate
   ```

7. **Do not recommend existing capabilities merely because their names match the current topic.**

8. **During discovery tasks, suppress loaded skill names as candidate recommendations until they pass the distinctness test.**
