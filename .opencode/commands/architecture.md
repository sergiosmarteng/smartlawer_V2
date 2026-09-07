---
description: Produce an architecture design with context, components, data flow, trade-offs, assumptions, and an implementation sequence — without writing code unless explicitly requested.
---

Produce an architecture design using the relevant architecture skill and `repo_map` for repository exploration.

Use the `repo_map` custom tool to map the repository structure, detect languages and frameworks, and identify relevant directories. Use `prompt_budget` to estimate context size of files that need inspection.

If the custom tool is unavailable, use the Python script directly from the cloned repository:
- python tools/repo_map.py [path]
- python tools/prompt_budget.py --dir <path>

Do not write code unless explicitly asked. The output is architecture only.

## Overlap control

Keep output proportional to task risk. Prefer concise findings over broad checklists.
Do not activate skills unrelated to the task scope.
Use supporting skills only when the lead skill does not cover the area.

Skill selection — Lead: Support: Guardrail: Excluded: Reason:

## Process

### 1. Classify the architecture task

| Task Type | Lead Skill | When |
|---|---|---|
| General system architecture | `system-architecture` | System context, components, data flow, deployment, reliability, scaling, cost |
| AI system architecture | `ai-system-architecture` | AI problem framing, LLM/RAG/ML pipelines, model routing, safety, evaluation |
| API or service design | `fastapi-backend` | API contracts, service boundaries, validation, auth |
| Frontend architecture | `nextjs-frontend` | Component tree, data fetching, state management, routing |
| Data layer architecture | `sqlalchemy-postgres` | Schema design, migration strategy, query patterns, connection pooling |

Select the lead skill that best matches the task. Add supporting skills for domain-specific gaps. Add guardrail skills only when their conditions are met.

### 2. Gather constraints

Ask for or infer:

- **Latency**: expected p50/p95/p99 response times
- **Throughput**: requests per second, concurrent users, data volume
- **Availability**: uptime target (e.g., 99.9%), RTO, RPO
- **Budget**: infrastructure cost constraints, team size, timeline
- **Security**: compliance requirements (SOC2, HIPAA, GDPR), auth model
- **Environment**: cloud provider, region, existing infrastructure
- **Scale horizon**: current load vs. 6-month and 12-month projections
- **Team**: team size, deployment frequency, ownership boundaries

Document which constraints are confirmed and which are assumed.

### 3. Produce the architecture

Use the lead skill to generate each section that applies:

- **System context**: scope, actors, external dependencies.
- **Components**: decomposition with responsibilities and boundaries.
- **Data flow**: diagrams, request paths, data at rest and in transit.
- **Communication**: sync vs. async decisions, queues, events.
- **Key decisions**: explicit decisions with rationale and date.
- **Alternatives considered**: for each key decision, list what was rejected and why.

### 4. Document assumptions

List every assumption the architecture depends on:

```
Assumptions:
- Throughput will not exceed 1,000 req/s for the next 12 months.
- Team has operational experience with Kubernetes.
- External API latency is under 200ms p95.
- Budget allows for multi-region deployment.
```

Flag any assumption that, if wrong, would invalidate the architecture.

### 5. Include trade-offs

For each significant decision, document:

- **Option chosen** with rationale.
- **Options rejected** with reason for rejection.
- **Impact** on cost, complexity, latency, scalability, or maintainability.

### 6. Create the implementation sequence

Produce ordered build steps from foundation to delivery:

```text
Implementation sequence:

Phase 1 — Foundation (week 1-2):
  - Set up repository structure and CI pipeline
  - Define shared schemas and contracts
  - Implement core data model and migrations

Phase 2 — Core (week 3-4):
  - Implement service A with basic auth
  - Implement service B with queue integration
  - Integration tests and contract verification

Phase 3 — Delivery (week 5-6):
  - Observability (logging, metrics, tracing)
  - Performance testing and tuning
  - Documentation and runbooks
```

Each phase should be independently testable and deployable.

### 7. Do not write code

Produce architecture only. If the user asks for code, ask whether they want implementation separately. Do not generate code inline with architecture.

Return:

## Architecture

### Task classification

Context:
[Brief description of what needs architecture.]

Lead skill:
[Selected lead skill.]

Supporting skills:
[Selected supporting skills or none.]

Guardrail skills:
[Selected guardrail skills or none.]

### Constraints

[Confirmed or inferred constraints.]

### System context

[Scope, actors, external dependencies.]

### Components

[Component decomposition with responsibilities and boundaries.]

### Data flow

[Request paths, data at rest and in transit.]

### Communication

[Sync vs. async decisions, queue and event design.]

### Key decisions

[Decisions made with rationale.]

### Alternatives considered

[Rejected options with reasons.]

### Assumptions

[Assumptions the architecture depends on.]

### Trade-offs

[Impact of significant decisions on cost, complexity, latency, etc.]

### Implementation sequence

[Ordered phases from foundation to delivery.]

$ARGUMENTS
