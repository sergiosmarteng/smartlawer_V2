---
name: ai-system-architecture
description: Design, review and document AI system architecture, covering problem framing, model vs. rule decisions, LLM/RAG/ML pipelines, ingestion, retrieval, orchestration, evaluation, serving, safety, privacy, lifecycle and failure modes.
license: MIT
compatibility: opencode
metadata:
  category: ai-engineering
  stack: ai-architecture
  version: "1.0.0"
orchestration:
  lead_for:
    - ai-system-architecture
  support_for: []
  conflicts_with:
    - system-architecture
---

# AI System Architecture

Use this skill when designing, reviewing, or documenting the end-to-end architecture of an AI-powered system — including problem framing, model selection, data pipelines, orchestration, evaluation, serving, safety, observability, and lifecycle management.

The objective is to produce a coherent architecture that balances capability, cost, latency, safety, privacy, and maintainability across every layer of the AI system.

## When to Use This Skill

Load this skill when the task involves any of the following:

- deciding whether AI or a rule-based solution is appropriate for a problem
- designing an end-to-end LLM, RAG, or ML system architecture
- planning data ingestion, chunking, embedding, and retrieval pipelines
- orchestrating multi-step AI workflows, tool use, and agent loops
- routing requests between models based on cost, latency, or capability
- designing structured output pipelines with validation and repair
- planning evaluation, observability, and drift detection
- designing inference serving with latency and cost budgets
- defining fallback behavior, circuit breakers, and human approval gates
- controlling hallucination, prompt injection, and data privacy risks
- managing model versions, lifecycle, and rollback strategies
- analyzing AI failure modes and designing mitigations

Do not load this skill for:
- detailed FastAPI serving implementation (use model-serving-production)
- RAG pipeline tuning or chunking details (use rag-quality-review)
- structured output parsing and retry loops (use structured-output-reliability)
- LLM evaluation methodology or judge setup (use ai-evaluation)
- prompt injection defense implementation (use prompt-injection-defense)
- LLM application security review (use llm-app-security)
- model fine-tuning or training (use fine-tuning)
- production deployment specifics (use production-readiness)

## AI Problem Framing

Before designing any AI system, frame the problem precisely.

### Is AI the Right Solution?

| Consideration | Favor AI | Favor Rule-Based |
|---|---|---|
| Decision boundary | Fuzzy, subjective, evolving | Clear, fixed, enumerable |
| Input variability | High — free text, images, audio | Low — structured fields, enums |
| Cost of error | Low — wrong answer is recoverable | High — wrong answer causes harm |
| Explainability required | Low — answer quality is sufficient | High — decisions must be audited |
| Data available | Sufficient labeled or unlabeled data | Rules can be written by experts |
| Latency requirement | Loose — seconds acceptable | Tight — milliseconds required |

### Scope Definition

- Define the exact boundary of what the AI system will and will not do.
- Document excluded scenarios explicitly — they become negative test cases.
- Specify the minimum acceptable quality bar before the system is useful.
- Identify the deployment environment constraints (latency, hardware, privacy).

## Model vs. Rule-Based Decisions

Many AI systems are best designed as a hybrid: rules handle predictable cases, models handle ambiguous ones.

### Decision Framework

```text
1. Can the decision be expressed as a deterministic lookup or formula?
   → Use a rule. (e.g., "reject email from blocked domain")

2. Can the decision be derived from a small set of labeled heuristics?
   → Use a decision tree or lookup table. (e.g., "route to support tier based on plan")

3. Does the decision require understanding unstructured content?
   → Use an ML or LLM model. (e.g., "classify customer sentiment")

4. Does the decision require synthesis or generation?
   → Use an LLM. (e.g., "summarize a conversation")

5. Does the decision need to consider long-tail edge cases?
   → Use an LLM with RAG. (e.g., "answer questions from a policy manual")
```

### Hybrid Architecture

- Use rules as a pre-filter or guardrail before model invocation.
- Use rules as a post-filter to validate or override model output.
- Cascade: try rule → try small model → try large model on failure.
- Log which path was taken for observability and tuning.

## LLM / RAG / ML Architecture

### LLM-Only Architecture

```
User Input → System Prompt → LLM → Output Validation → Response
```

Use when: the model's training data is sufficient and no external data is needed.

Constraints:
- Prompt length and cost grow with context.
- No access to private or recent data beyond the training cut-off.
- Hallucination risk is higher on niche topics.

### RAG Architecture

```
User Input → Query Rewriting → Embedding → Vector Search
                                          ↓
Response ← Generation ← Context Assembly ← Reranking
```

Use when: answers must be grounded in specific documents, private data, or frequently updated content.

### ML Classifier + LLM Architecture

```
User Input → ML Classifier → Route to LLM (for generation)
                            → Route to Rule (for known cases)
```

Use when: routing decisions (intent classification, moderation) can be handled faster/cheaper by a smaller model.

### Multi-Agent Architecture

```
User Input → Orchestrator → Specialist Agent A ←→ Tool A
                          → Specialist Agent B ←→ Tool B
                          → Reviewer Agent → Final Response
```

Use when: tasks require multiple distinct capabilities, tools, or verification steps.

## Ingestion

### Document Processing Pipeline

| Stage | Purpose | Considerations |
|---|---|---|
| Extraction | Text extraction from PDFs, HTML, images | OCR quality, encoding, formatting preservation |
| Cleaning | Remove noise: headers, footers, ads, boilerplate | Preserve document structure and meaning |
| Splitting | Chunk documents into processable units | Chunk size, overlap, boundaries (section, paragraph) |
| Metadata | Capture source, date, author, section path | Filtering, provenance, citation |
| Embedding | Convert chunks to vectors | Model choice, dimensionality, normalization |
| Indexing | Store vectors + metadata in vector store | Index type (HNSW, IVF), filters, namespaces |

### Ingestion Quality Checks

- Track chunk count, average chunk size, and embedding dimension per document.
- Detect and quarantine documents that fail extraction (empty, corrupt, unreadable).
- Validate that every chunk has sufficient content for retrieval.
- Log embedding failures with document ID and error reason.

## Retrieval

### Search Strategy

| Strategy | Recall | Latency | Best For |
|---|---|---|---|
| Dense vector search | High | Medium | Semantic similarity |
| Keyword (BM25) | Medium | Low | Exact term matching |
| Hybrid (dense + keyword) | Highest | Higher | General purpose |
| Multi-vector (MMR, RRF) | Controlled | Higher | Diversity, deduplication |

### Retrieval Quality

- Measure hit rate: fraction of queries where the relevant document appears in top-k.
- Measure MRR (Mean Reciprocal Rank): ranks position of the first relevant result.
- Tune chunk size, overlap, top-k, and similarity threshold per domain.
- Implement query rewriting: expand, reformulate, or decompose the user query.
- Add metadata filtering (date range, source type, access scope) to narrow search.

### Reranking

- Apply a cross-encoder reranker to the top-N results from the retriever.
- Reranking improves relevance but adds latency — budget accordingly.
- Fall back to retriever order if reranker is unavailable or slow.

## Orchestration

### Pipeline Types

- **Sequential**: Step A → Step B → Step C. Simple, predictable.
- **Conditional**: Branch based on intent, confidence, or validation result.
- **Parallel**: Fan-out to multiple models/agents, aggregate results.
- **Loop**: Iterate with feedback (e.g., self-critique, reflection, refinement).
- **Tool-use**: Model calls external functions, receives results, continues.

### Orchestration Principles

- Define a maximum step count to bound cost and latency.
- Log every step with input, output, duration, and model used.
- Use structured state that persists across steps for observability.
- Set per-step timeouts — a single stuck step should not hang the pipeline.
- Distinguish between retryable and non-retryable step failures.

## Structured Outputs

- Define a JSON Schema or Pydantic model for every structured output.
- Use constrained generation (JSON mode, grammar, tool calls) where supported.
- Validate output against schema before returning to caller.
- On validation failure: retry with the validation error in the prompt.
- On repeated failure: fall back to a default safe response.
- Never use `eval()` to parse model output.

## Model Routing

### Routing Strategies

| Strategy | Trigger | Effect |
|---|---|---|
| Capability-based | Task type (summarization, coding, chat) | Route to best-fit model |
| Cost-aware | Budget tier, input/output size | Cheaper model for simple tasks |
| Latency-sensitive | SLA requirement | Faster model for time-critical paths |
| Fallback cascade | Primary failure or timeout | Degrade to cheaper/faster model |
| Quality gate | Confidence or score below threshold | Escalate to more capable model |

### Routing Implementation

- Define a routing table with model name, capability, cost per token, and latency profile.
- Implement routing as a middleware or pipeline step, not scattered across business logic.
- Log the routing decision and the alternative that was not chosen.
- Allow dynamic overrides via feature flag or configuration.

## Evaluation

### Evaluation Layers

| Layer | What It Measures | Method |
|---|---|---|
| Component | Individual model, retriever, or chunker | Golden test set, unit metrics |
| Pipeline | End-to-end flow quality | Integration test with judged output |
| Production | Live system behavior | A/B comparison, user feedback, drift detection |

### Offline Evaluation

- Maintain a golden test set with inputs and expected outputs.
- Run evaluation on every model candidate before deployment.
- Compare metrics against the current production baseline.
- Reject candidates that regress on any critical metric.

### Online Evaluation

- Track response quality via user feedback (thumbs, ratings, corrections).
- Monitor for quality degradation over time (drift).
- Sample responses for human review on a regular cadence.
- Log all responses with enough context for offline evaluation.

## Inference Serving

### Serving Patterns

| Pattern | Latency | Throughput | Cost |
|---|---|---|---|
| Real-time (sync API) | Low | Moderate | Per-request |
| Batch (async job) | High | High | Per-batch, amortized |
| Streaming (SSE) | First-token low | Moderate | Per-token |
| Edge / local | Lowest | Device-limited | Zero marginal |

### Latency Budget

Define a per-request latency budget breakdown:

| Component | Budget | % of Total |
|---|---|---|
| Input validation | 5ms | 1% |
| Preprocessing | 20ms | 4% |
| Retrieval | 100ms | 20% |
| Reranking | 50ms | 10% |
| Model inference | 250ms | 50% |
| Output validation | 25ms | 5% |
| Overhead | 50ms | 10% |

### Cost Budget

- Track cost per request by model, token count, and tier.
- Set a maximum cost per request and per user per day.
- Use cheaper models for high-volume, low-complexity requests.
- Cache frequent or identical requests to reduce cost.

## Fallback Behavior

### Fallback Tiers

| Tier | Trigger | Response Quality |
|---|---|---|
| Primary | Normal operation | Best |
| Secondary | Primary timeout or error | Reduced (smaller model) |
| Tertiary | All models unavailable | Static: "Unable to process" |
| Offline | System degraded | Cached or queued for later |

### Implementation Rules

- Every failure must produce a user-visible response, not a silent error.
- Log every fallback invocation with trigger, tier, and duration.
- Alert when fallback usage exceeds 5% of total requests.
- Never retry a fallback that has already failed.

## Human Approval

### When to Require Approval

| Scenario | Risk | Approval |
|---|---|---|
| Automated action affecting user data | High | Required |
| Content generation in regulated domain | Medium | Recommended |
| Low-risk classification (e.g., spam) | Low | Optional |
| Non-consequential internal use | Minimal | None |

### Approval Patterns

- **Queue-based**: Actions are queued for review, approved or rejected in batches.
- **Inline**: Response waits for human review before delivery (high latency).
- **Post-hoc**: Action is taken and logged; human reviews after the fact.
- **Escalation**: Automated approval for low-risk, human approval for high-risk.

### Approval Infrastructure

- Every decision that requires approval must be logged with full context.
- Approval must be explicit (button click, API call) — not implicit (timeout).
- Track approval rate, rejection rate, and average review time.
- Provide reviewers with enough context to make an informed decision.

## Hallucination Controls

### Detection

- **Grounding check**: Does the response cite a retrieved document?
- **Factual consistency**: Use an LLM judge or NLI model to score response against source.
- **Contradiction detection**: Does the response contradict itself or known facts?
- **Confidence threshold**: Reject responses below a calibrated confidence score.

### Mitigation

- Require citations for every factual claim.
- Limit generation to content present in retrieved documents (closed-book → open-book).
- Use constrained decoding (logit bias, token blocking) to prevent disallowed tokens.
- Set model temperature low (0.0–0.3) for factual tasks.
- Validate output against a known-good schema or knowledge base.

## Prompt-Injection Boundaries

### Architecture-Level Defenses

- **Structural separation**: System instructions and user input are in separate, clearly delimited message roles.
- **Input classification**: Classify user input for injection patterns before it reaches the model.
- **Output validation**: Scan model output for leaked prompts, system instructions, or unauthorized content.
- **Least privilege**: The model has the minimum tool access needed for the task.
- **Human review**: Sensitive actions require human approval regardless of model output.

### Boundary Enforcement

- Define a clear trust boundary: user input is untrusted, system prompt is trusted.
- Never concatenate untrusted input into system instructions.
- Validate tool call arguments before execution — do not rely on the model to enforce safety.
- Log injection attempts (detected pattern, input, model) for incident response.

## Data Privacy

### Privacy Principles

- Minimize: send the minimum data necessary to the model.
- Redact: remove PII, secrets, and internal identifiers before model invocation.
- Isolate: tenant data must be isolated at every layer (embedding, retrieval, generation).
- Audit: every data access must be logged with user, action, and timestamp.

### PII Handling

| Data Type | Action Before LLM |
|---|---|
| Names, emails, phones | Redact with placeholder tokens |
| Internal IDs | Hash or replace with opaque ID |
| Free text containing PII | Scan and redact before sending |
| Credentials / secrets | Block — never send to any model |

### Tenant Isolation

- Use separate vector store namespaces or collections per tenant.
- Filter retrieval results to the tenant's document scope.
- Never cache responses across tenants.
- Validate tenant context in every orchestration step.

## Model / Version Lifecycle

### Lifecycle Stages

| Stage | Description | Actions |
|---|---|---|
| Development | Model is being trained or configured | Iteration, evaluation, human review |
| Staging | Model is deployed in staging for validation | Automated evaluation, canary testing |
| Production | Model serves live traffic | Monitoring, alerting, fallback configured |
| Deprecated | Model is superseded | Traffic moved to new version, old version archived |
| Retired | Model is no longer available | Artifacts removed, documentation updated |

### Versioning

- Tag every model artifact with a unique, immutable version.
- Record version in response headers, logs, and metrics.
- Keep at least the last N production versions accessible for rollback.
- Never overwrite a published version — publish a new version.

### Rollback

- Deploy model changes behind a feature flag or traffic split.
- Define automatic rollback criteria: error rate + latency + quality metrics.
- Canary: route 5% traffic to new version, monitor for 5 minutes, auto-rollback on degradation.
- Keep the previous version loaded during canary for instant rollback.

## Drift

### Drift Types

| Drift Type | What Changes | Detection |
|---|---|---|
| Data drift | Input distribution | Statistical tests on input features |
| Concept drift | Input → output relationship | Performance metric monitoring |
| Model decay | Model quality over time | Periodic evaluation vs golden set |
| Embedding drift | Vector distribution | Cluster distance, outlier detection |

### Drift Response

- Alert on drift with severity based on magnitude.
- Re-evaluate against golden set when drift is detected.
- Route affected traffic to fallback if drift is severe.
- Log drift samples (sanitized) for analysis and retraining.

## Observability

### Every AI Request Must Produce

- Trace with unique request ID across all pipeline steps
- Per-step duration and model used
- Input and output token counts
- Which model tier served the request
- Whether the response was cached
- Validation results (passed, failed, repaired)
- Cost per step and total cost

### Metrics to Export

| Metric | Source | Purpose |
|---|---|---|
| Request rate | Gateway | Traffic volume |
| p50/p95/p99 latency | Application | Latency distribution |
| Token throughput | Application | Generation speed |
| Cost per request | Application | Budget tracking |
| Retrieval hit rate | Retriever | Search quality |
| Fallback rate | Orchestrator | System health |
| Hallucination score | Judge model | Response quality |
| Approval rate | Human review | Workflow efficiency |
| Error rate by step | Orchestrator | Failure detection |

### Alerting Thresholds

- p95 latency exceeds budget by 2x for 5 minutes.
- Fallback rate exceeds 5% in any 10-minute window.
- Error rate exceeds 1% for any pipeline step.
- Cost per request exceeds budget by 2x in a day.
- No drift check has run in 24 hours.

## AI Failure Modes

### Common Failure Modes

| Failure Mode | Symptom | Mitigation |
|---|---|---|
| Hallucination | Response invents facts | Grounding checks, citations, low temperature |
| Prompt injection | Model ignores instructions | Structural separation, input classification, output validation |
| Data leakage | Model reveals private data | PII redaction, tenant isolation, output scanning |
| Model bias | Unfair or stereotyped output | Evaluation on diverse test sets, bias detection |
| Model decay | Quality degrades over time | Periodic evaluation, drift monitoring, retraining |
| Cost explosion | Unbudgeted token usage | Token limits, cost budgets, caching, fallback models |
| Latency spike | Response time exceeds SLA | Timeouts, fallback to faster model, async processing |
| Cascade failure | One failure triggers more | Circuit breakers, graceful degradation, per-step isolation |
| Stale data | Model uses outdated information | Freshness checks, data versioning, cache invalidation |
| Retry storm | Repeated failures amplify load | Bounded retries, circuit breaker, dead-letter queue |

### Failure Mode Analysis Process

For each identified failure mode:
1. Document the trigger condition.
2. Estimate severity and likelihood.
3. Design prevention (architectural guard).
4. Design detection (metric, log, alert).
5. Design response (mitigation, fallback, escalation).
6. Test the failure scenario to verify the response.

## Required Review Output

When reviewing an AI system architecture, produce this summary:

```text
System:
[Name, purpose, deployment environment.]

Problem framing:
[Why AI was chosen, scope boundaries, excluded scenarios.]

Architecture:
[Pattern: LLM-only / RAG / ML+LLM / Multi-agent. Diagram description.]

Data ingestion:
[Source types, extraction method, chunking strategy, embedding model, storage.]

Retrieval:
[Search strategy, top-k, reranking, metadata filtering, hit rate.]

Orchestration:
[Pipeline steps, branching logic, max iterations, timeout, state management.]

Model routing:
[Routing table, fallback cascade, cost/latency budgets.]

Evaluation:
[Golden set size, metrics, evaluation cadence, comparison baseline.]

Serving:
[Pattern (real-time/batch/streaming), latency budget, concurrency limits.]

Safety:
[Hallucination controls, injection boundaries, PII handling, human approval gates.]

Observability:
[Tracing, metrics, logging, alerting thresholds.]

Lifecycle:
[Model versioning, canary deployment, rollback criteria, deprecation policy.]

Drift detection:
[Drift types monitored, detection method, response procedure.]

Failure modes:
[Identified risks with prevention, detection, and response for each.]

Issues found:
[List each finding with severity, location, impact, and recommended fix.]

Recommendations:
[Prioritized list of improvements with expected impact.]
```

## Completion Criteria

An AI system architecture review is complete only when:

- the problem framing includes clear justification for AI vs. rule-based approach
- the architecture pattern is documented with rationale
- data ingestion and retrieval are specified with expected quality metrics
- orchestration is defined with step count, timeout, and retry limits
- model routing is defined with fallback cascade and cost/latency budgets
- evaluation strategy covers component, pipeline, and production layers
- serving pattern matches latency and throughput requirements
- hallucination controls are designed and testable
- prompt-injection boundaries are enforced at the architecture level
- data privacy measures (redaction, isolation, auditing) are documented
- model lifecycle includes versioning, canary, rollback, and deprecation
- drift detection is configured with alerting and response procedures
- observable request tracing spans every pipeline step
- failure modes are analyzed with prevention, detection, and response
- human approval gates are defined for high-risk actions
- all recommendations are documented with severity and expected impact
