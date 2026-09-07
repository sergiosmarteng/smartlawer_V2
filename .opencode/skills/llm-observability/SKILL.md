---
name: llm-observability
description: Design and implement observability for LLM applications, including structured logging, tracing, metrics collection, cost tracking, evaluation pipelines, alerting and dashboarding.
license: MIT
compatibility: opencode
metadata:
  category: ai-engineering
  stack: llm-observability
  version: "1.0.0"
orchestration:
  lead_for:
    - llm-observability
  support_for: []
  conflicts_with:
    - ai-evaluation
---

# LLM Observability

Use this skill when adding observability to an LLM application — tracking token usage, logging prompts and completions, instrumenting guardrails, monitoring generation quality in production, and alerting on anomalies.

The objective is to make every LLM call observable: you can trace what prompt was sent, what response was returned, how many tokens were used, how long it took, whether it was safe, and how its quality compares against baselines.

This skill covers LLM-specific observability. It does not cover general infrastructure monitoring (CPU, memory, disk, request throughput) — use `model-serving-production` for that. It does not cover offline evaluation methodology — use `ai-evaluation` for that.

## When to Use This Skill

Load this skill when the task involves any of the following:

- instrumenting LLM calls with structured logging and tracing
- selecting and integrating an LLM observability platform (Langfuse, LangSmith, W&B, MLflow)
- tracking token usage and cost per model, per user, or per tenant
- monitoring generation quality metrics in production (faithfulness, relevance, refusal rate)
- setting up alerting for LLM-specific anomalies (latency spikes, refusal rate changes, cost surges)
- building dashboards to visualize LLM behavior across models, users, and time
- evaluating LLM output in production (online evaluation vs. offline evaluation)
- instrumenting safety guardrails (content classifiers, PII detectors) for observability
- detecting data drift in LLM inputs and outputs
- auditing LLM usage for compliance, billing, or debugging

Do not load this skill for:

- general application logging or infrastructure monitoring (use model-serving-production skill)
- offline evaluation methodology, test sets, or golden datasets (use ai-evaluation skill)
- LLM security hardening (use llm-app-security skill)
- prompt injection defense (use prompt-injection-defense skill)
- RAG pipeline evaluation (use rag-quality-review skill)

## Observability Architecture

### Three Pillars of LLM Observability

| Pillar | What It Tracks | Why It Matters |
|--------|---------------|----------------|
| **Tracing** | Full request lifecycle: prompt, completion, model, latency, tokens, errors | Debug poor responses, identify regressions, audit model behavior |
| **Metrics** | Aggregated measurements: token count, cost, latency percentiles, refusal rate, quality scores | Trends, alerts, capacity planning, cost attribution |
| **Logging** | Structured records of every LLM interaction | Compliance, billing disputes, post-mortem analysis |

### What Sets LLM Observability Apart

LLM observability differs from traditional application observability in four ways:

1. **Prompt and response data is high-cardinality and sensitive.** Every request carries different text; logs must exclude PII. Traditional logging treats payloads as opaque blobs; LLM observability treats them as first-class, analyzable data.
2. **Quality is not binary.** An LLM call can succeed technically (200 OK, valid JSON) but produce a low-quality or unsafe response. Observability must track quality metrics, not just uptime and latency.
3. **Cost is non-uniform.** Token prices differ by model, input vs. output, and provider. Observability must attribute cost accurately.
4. **Drift is semantic.** Input distributions and output quality shift over time as user behavior changes or models update. Observability must detect semantic drift, not just numeric threshold violations.

## Structured Logging

### Log Format for LLM Calls

Every LLM call should produce a structured log record with these fields:

```python
{
    "timestamp": "2026-07-09T10:30:00.000Z",
    "trace_id": "abc123",
    "span_id": "def456",
    "model": "gpt-4o-mini",
    "provider": "openai",
    "request": {
        "system_prompt_hash": "sha256:...",     # hash of system prompt, not content
        "user_prompt_hash": "sha256:...",        # hash of user input, not content
        "input_tokens": 145,
        "temperature": 0.7,
        "max_tokens": 1024
    },
    "response": {
        "output_tokens": 89,
        "total_tokens": 234,
        "latency_ms": 1234,
        "finish_reason": "stop",
        "response_hash": "sha256:..."            # hash of response content
    },
    "metadata": {
        "user_id": "user_42",
        "session_id": "sess_abc",
        "application": "chat-support",
        "model_version": "gpt-4o-mini-2026-05-01",
        "environment": "production"
    },
    "errors": null,
    "guardrail_results": {
        "content_safe": true,
        "pii_detected": false,
        "toxicity_score": 0.002
    }
}
```

### Logging Rules

- **Hash prompt and response content** instead of storing raw text. Use SHA-256. Store full content only in a restricted-access trace store.
- **Never log raw PII.** Strip or hash emails, phone numbers, API keys, and addresses before logging.
- **Include trace context** (trace_id, span_id) to correlate logs with traces and metrics.
- **Include model version** to detect regressions after model updates.
- **Include environment** (production, staging, canary) to distinguish test traffic.
- **Log at the application boundary**, not inside the model provider SDK.

### Python Structured Logging Setup

```python
import logging
import json
from datetime import datetime, timezone

class LLMLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        record.timestamp = datetime.now(timezone.utc).isoformat()
        return json.dumps({
            "timestamp": record.timestamp,
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            **(getattr(record, "extra_fields", {})),
        })

logger = logging.getLogger("llm_observability")
handler = logging.StreamHandler()
handler.setFormatter(LLMLogFormatter())
logger.addHandler(handler)
logger.setLevel(logging.INFO)

def log_llm_call(
    model: str,
    input_tokens: int,
    output_tokens: int,
    latency_ms: float,
    user_id: str | None = None,
    error: str | None = None,
):
    logger.info("llm_call", extra={
        "extra_fields": {
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "latency_ms": latency_ms,
            "user_id": user_id,
            "error": error,
        }
    })
```

## Tracing

### Tracing an LLM Call

Use OpenTelemetry with semantic conventions for LLM spans:

```python
from opentelemetry import trace
from opentelemetry.semconv.ai import GenAIAttributes

tracer = trace.get_tracer("llm-app", tracer_provider=tracer_provider)

with tracer.start_as_current_span("llm.chat", kind=trace.SpanKind.CLIENT) as span:
    span.set_attribute(GenAIAttributes.GENAI_REQUEST_MODEL, "gpt-4o-mini")
    span.set_attribute(GenAIAttributes.GENAI_REQUEST_TEMPERATURE, 0.7)
    span.set_attribute(GenAIAttributes.GENAI_REQUEST_MAX_TOKENS, 1024)
    span.set_attribute(GenAIAttributes.GENAI_USAGE_INPUT_TOKENS, 145)
    span.set_attribute(GenAIAttributes.GENAI_USAGE_OUTPUT_TOKENS, 89)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
    )

    span.set_attribute(GenAIAttributes.GENAI_RESPONSE_FINISH_REASON, response.choices[0].finish_reason)
    span.set_status(trace.StatusCode.OK)
```

### Span Attributes for LLM Calls

Each LLM trace span should include:

| Attribute | Value | Required |
|-----------|-------|----------|
| `gen_ai.request.model` | e.g. `gpt-4o-mini` | Yes |
| `gen_ai.request.max_tokens` | Max output tokens | Yes |
| `gen_ai.request.temperature` | Temperature setting | Yes |
| `gen_ai.usage.input_tokens` | Input token count | Yes |
| `gen_ai.usage.output_tokens` | Output token count | Yes |
| `gen_ai.response.finish_reason` | `stop`, `length`, `content_filter`, `error` | Yes |
| `gen_ai.response.id` | Provider response ID | Recommended |
| `app.user_id` | User identifier | Recommended |
| `app.session_id` | Session identifier | Recommended |
| `app.environment` | `production`, `staging`, `canary` | Recommended |

### Trace Hierarchy

Structure traces to reflect your application architecture:

```
POST /api/chat                    # Root span (backend request)
├── authenticate                  # Auth sub-span
├── retrieve_context              # RAG retrieval sub-span
│   ├── vector_search
│   └── rerank
├── llm.chat                      # LLM call sub-span
│   ├── prepare_prompt
│   └── provider_request          # External API call
├── guardrail.check               # Safety check sub-span
│   ├── toxicity_classification
│   └── pii_scan
└── format_response
```

## Metrics

### LLM-Specific Metrics

Track these metric categories:

**Usage Metrics:**
- `llm.tokens.input` — input tokens per request (histogram)
- `llm.tokens.output` — output tokens per request (histogram)
- `llm.tokens.total` — total tokens per request (histogram)
- `llm.requests.total` — total request count (counter), by model, user, status

**Cost Metrics:**
- `llm.cost.per_request` — cost per request (histogram)
- `llm.cost.total` — cumulative cost (counter), by model, user, tenant
- `llm.cost.budget_remaining` — remaining budget for period (gauge)

**Performance Metrics:**
- `llm.latency` — request latency in ms (histogram), p50/p95/p99
- `llm.latency.ttft` — time to first token in ms (histogram)
- `llm.latency.provider` — provider-side latency (histogram)

**Quality Metrics:**
- `llm.quality.refusal_rate` — proportion of refusals (gauge), by model, prompt category
- `llm.quality.error_rate` — proportion of errors (gauge), by error type
- `llm.quality.faithfulness` — average faithfulness score (gauge), when evaluator available
- `llm.quality.relevance` — average relevance score (gauge), when evaluator available

**Guardrail Metrics:**
- `llm.guardrail.flagged` — alerts triggered (counter), by guardrail type
- `llm.guardrail.blocked` — requests blocked (counter), by guardrail type
- `llm.guardrail.latency` — guardrail evaluation latency (histogram)

### Python Metrics Setup

```python
from prometheus_client import Histogram, Counter, Gauge

llm_tokens = Histogram(
    "llm_tokens_total",
    "Total tokens per LLM request",
    labelnames=["model", "user_id"],
    buckets=[100, 500, 1000, 2000, 4000, 8000, 16000],
)

llm_latency = Histogram(
    "llm_latency_ms",
    "LLM request latency in milliseconds",
    labelnames=["model"],
    buckets=[100, 500, 1000, 2000, 5000, 10000, 30000],
)

llm_requests = Counter(
    "llm_requests_total",
    "Total LLM requests",
    labelnames=["model", "status"],
)

refusal_rate = Gauge(
    "llm_refusal_rate",
    "Current refusal rate as a proportion of requests",
    labelnames=["model"],
)

def record_llm_metrics(
    model: str,
    input_tokens: int,
    output_tokens: int,
    latency_ms: float,
    status: str = "success",
    user_id: str | None = None,
):
    labels = {"model": model, "user_id": user_id or "unknown"}
    llm_tokens.labels(**labels).observe(input_tokens + output_tokens)
    llm_latency.labels(model=model).observe(latency_ms)
    llm_requests.labels(model=model, status=status).inc()
```

### Metric Collection Best Practices

- Add `model` as a label to every metric for per-model breakdowns
- Add `user_id` or `tenant_id` as a label only when cardinality is bounded (<1000 distinct values)
- For high-cardinality labels (user IDs in a SaaS app), use log-based metrics instead of Prometheus labels
- Use log-based metrics for cost tracking (Prometheus does not handle monetary values well)
- Set retention policies: raw metrics for 30 days, aggregated (hourly/daily) for 1 year

## Cost Tracking

### Per-Request Cost Calculation

```python
MODEL_PRICING = {
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},   # per 1M tokens
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "claude-3-5-sonnet": {"input": 3.00, "output": 15.00},
    "llama-3.1-70b": {"input": 0.90, "output": 0.90},
}

def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    pricing = MODEL_PRICING.get(model)
    if not pricing:
        return 0.0
    input_cost = (input_tokens / 1_000_000) * pricing["input"]
    output_cost = (output_tokens / 1_000_000) * pricing["output"]
    return round(input_cost + output_cost, 6)
```

### Cost Attribution Dimensions

- Per model — which models cost the most
- Per user or tenant — fair chargeback or billing
- Per application or feature — cost per feature
- Per time period — daily, weekly, monthly spend
- Per request type — chat vs. summarization vs. classification

### Cost Log

Maintain a cost log separate from the general observability pipeline:

```python
{
    "timestamp": "...",
    "model": "gpt-4o",
    "input_tokens": 5000,
    "output_tokens": 200,
    "input_cost": 0.0125,
    "output_cost": 0.002,
    "total_cost": 0.0145,
    "user_id": "user_42",
    "application": "chat-support",
    "environment": "production"
}
```

Export cost logs to a data warehouse or billing system. Do not rely on Prometheus for cost data — it cannot reconstruct exact monetary values from histogram buckets.

## Observability Platforms

### Platform Comparison

| Platform | Strengths | Best For | Self-Hostable |
|----------|-----------|----------|---------------|
| **Langfuse** | Open-source, trace-first UI, prompt management, evaluation | Full LLM observability stack | Yes |
| **LangSmith** | LangChain integration, dataset management, online evaluation | Teams already using LangChain | No |
| **Weights & Biases** | Experiment tracking, model registry, dataset versioning | ML teams, fine-tuning pipelines | Yes |
| **MLflow** | Open-source, model registry, deployment tracking | General ML lifecycle management | Yes |
| **OpenTelemetry Collector** | Vendor-neutral, integrates with any backend | Organizations with existing observability infrastructure | Yes |
| **Helicone** | Proxy-based, no code changes, simple setup | Quick setup, lightweight tracking | No |
| **Arize AI** | Drift monitoring, LLM evaluation, embedding analysis | Production monitoring, data quality | No |

### Choosing a Strategy

| Situation | Recommended Approach |
|-----------|---------------------|
| Existing OpenTelemetry + Datadog/Grafana stack | Custom OTel instrumentation + Prometheus metrics + log-based cost |
| Small team, want observability fast | Langfuse (self-hosted) or Helicone (proxy) |
| Heavy LangChain usage | LangSmith |
| Need experiment tracking + production | W&B for experiments + Langfuse for production |
| Compliance-heavy industry | Self-hosted Langfuse or custom OTel with strict PII controls |

### Instrumenting with Langfuse

```python
from langfuse import Langfuse

langfuse = Langfuse()

@langfuse.observe()
def chat_with_trace(user_message: str, user_id: str) -> str:
    generation = langfuse.generation(
        name="chat-response",
        model="gpt-4o-mini",
        input=user_message,
        metadata={"user_id": user_id},
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": user_message}],
    )

    generation.end(
        output=response.choices[0].message.content,
        usage={
            "input": response.usage.prompt_tokens,
            "output": response.usage.completion_tokens,
        },
    )
    return response.choices[0].message.content
```

## Alerting

### LLM-Specific Alert Rules

| Alert | Condition | Severity | Example Threshold |
|-------|-----------|----------|-------------------|
| High refusal rate | Refusal rate > baseline + 3σ | Critical | > 15% for 5 minutes |
| Latency p99 spike | p99 latency > baseline + 50% | Warning | > 5000ms for 5 minutes |
| Error rate spike | Error rate > 5% in 5-minute window | Critical | > 5% for 5 minutes |
| Cost anomaly | Daily cost > 2x previous 7-day average | Warning | Per-day comparison |
| Token surge | Total tokens > 3x previous hour | Warning | Per-hour comparison |
| Guardrail hit rate change | Flag rate change > 20% in 1 hour | Warning | Could be attack or false positive change |
| Hallucination / low faithfulness | Average faithfulness score < 0.6 | Critical | Requires quality evaluator in loop |
| Empty response rate | Empty responses > 1% of requests | Warning | Indicates model or prompt issue |

### Alerting Setup with Prometheus + Alertmanager

```yaml
# prometheus rules
groups:
  - name: llm_observability
    rules:
      - alert: HighRefusalRate
        expr: rate(llm_refusal_rate[5m]) > 0.15
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Refusal rate > 15% for {{ $value | humanizePercentage }} of requests"

      - alert: HighLatencyP99
        expr: histogram_quantile(0.99, rate(llm_latency_bucket[5m])) > 5000
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "p99 latency > 5000ms for model {{ $labels.model }}"
```

### Alert Fatigue Prevention

- Set dynamic baselines: alert on deviation from rolling 7-day window, not static thresholds
- Silence alerts during planned rollouts (mark with `canary=true` label)
- Rate-limit alerts: no more than 1 alert per metric per 15 minutes
- Distinguish warning vs. critical: warning can wait for business hours; critical pages on-call
- Use multi-window, multi-burn-rate alerts for SLO-based alerting

## Online Evaluation

### Online vs. Offline Evaluation

| Aspect | Offline Evaluation | Online Evaluation |
|--------|-------------------|-------------------|
| When | Before deployment | During production |
| Data | Labeled test set | Real user traffic |
| Comparison | Against golden answers | A/B tests, pre/post model change |
| Metrics | Accuracy, F1, BLEU, ROUGE | Refusal rate, user satisfaction, latency |
| Cost | Low (compute only) | High (must maintain evaluator) |
| Risk | Low (no user impact) | Low if canary pattern used |

### Instrumenting Online Evaluation

```python
EVALUATION_CRITERIA = {
    "faithfulness": "Does the response stay faithful to the provided context?",
    "relevance": "Is the response relevant to the user's question?",
    "helpfulness": "Is the response helpful and actionable?",
}

async def evaluate_response(
    question: str,
    context: str,
    response: str,
    evaluator_model: str = "gpt-4o-mini",
) -> dict[str, float]:
    """Evaluate an LLM response using an LLM judge.

    Use a smaller, cheaper model to evaluate a larger model's output.
    Store results as observability metrics.
    """
    scores = {}
    for criterion, instruction in EVALUATION_CRITERIA.items():
        judge_prompt = f"""You are evaluating an AI assistant's response.

Context: {context}
User question: {question}
Assistant response: {response}

Criterion: {instruction}

Rate the response on a scale of 1-5 where:
1 = completely fails, 5 = perfectly meets the criterion.

Respond with only a single number (1-5)."""

        judge_response = await judge_client.completions.create(
            model=evaluator_model,
            prompt=judge_prompt,
            max_tokens=2,
            temperature=0,
        )
        try:
            scores[criterion] = int(judge_response.choices[0].text.strip())
        except (ValueError, IndexError):
            scores[criterion] = 0.0

    return scores
```

### Online Evaluation Sampling

Do not evaluate every response. Use stratified sampling:

- Sample 100% of responses during canary rollouts
- Sample 10-20% of responses during steady-state production
- Over-sample edge cases: long responses, high-latency responses, guardrail flags
- Ensure sample includes diversity of users, prompt categories, and models

## Guardrail Observability

### Instrumenting Guardrails

Every guardrail evaluation should produce a structured record:

```python
{
    "guardrail_type": "toxicity",
    "model": "roberta-toxicity-classifier",
    "input_text_hash": "sha256:...",
    "score": 0.002,
    "threshold": 0.5,
    "flagged": false,
    "latency_ms": 45
}
```

### Guardrail Metrics to Track

- Latency per guardrail — guardrails should not dominate total request time
- Flag rate — proportion of requests that trigger each guardrail
- Block rate — proportion of requests blocked by each guardrail
- False positive rate — when a human reviewer confirms the flag was incorrect
- Distribution of scores — shifts may indicate changing input distributions

### Guardrail Comparison Dashboard

Compare guardrail behavior across model versions:

| Metric | v1.0 | v1.1 | Change |
|--------|------|------|--------|
| Toxicity flag rate | 1.2% | 0.8% | -33% |
| PII detection rate | 0.3% | 0.5% | +67% |
| Avg guardrail latency | 120ms | 85ms | -29% |
| Requests blocked | 0.5% | 0.4% | -20% |

## Drift Detection

### Types of Drift

| Drift Type | What Changes | Detection Method |
|------------|-------------|------------------|
| Input length drift | Average prompt length increases or decreases | Track p50/p95 input length over time |
| Output length drift | Average response length changes | Track p50/p95 output length over time |
| Embedding drift | Semantic distribution of inputs shifts | Track embedding distance from reference distribution |
| Quality drift | Faithfulness, relevance, or helpfulness scores decline | Track LLM-judge scores over time |
| Topic drift | Users ask about different subjects | Track topic classification distribution |
| Refusal drift | Refusal rate changes without code changes | Track refusal rate per prompt category |

### Embedding Drift Detection

```python
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

def detect_embedding_drift(
    recent_embeddings: list[np.ndarray],
    reference_embeddings: list[np.ndarray],
    threshold: float = 0.05,
) -> dict:
    """Detect if recent input embeddings have drifted from reference."""
    ref_mean = np.mean(reference_embeddings, axis=0)
    recent_mean = np.mean(recent_embeddings, axis=0)
    similarity = cosine_similarity([ref_mean], [recent_mean])[0][0]
    drift_score = 1 - similarity
    return {
        "drift_score": float(drift_score),
        "drifted": drift_score > threshold,
        "threshold": threshold,
    }
```

## Dashboard Layout

### LLM Observability Dashboard

Organize dashboards by audience:

**Developer Dashboard:**
- Real-time trace explorer — search by trace_id, user_id, model, error
- Error rate and latency — sparklines for the last hour
- Token usage per model — stacked area chart
- Recent errors — table with model, error message, timestamp

**Operations Dashboard:**
- Cost per model — daily bar chart
- Request volume — hourly line chart, broken down by model
- P50/P95/P99 latency — multi-line chart
- Alert status — current firing alerts with duration

**Business Dashboard:**
- Cost per user/tenant — stacked bar chart
- Total monthly spend — gauge with budget line
- Request volume trend — 30-day rolling average
- Top users by token consumption — table

**Quality Dashboard:**
- Refusal rate over time — line chart with baseline
- Faithfulness score trend — line chart with threshold line
- Guardrail hit rate — stacked bar by guardrail type
- Drift scores — single-value gauges per drift type

## Testing

### Unit Tests

```python
def test_cost_calculation():
    cost = calculate_cost("gpt-4o-mini", input_tokens=1000, output_tokens=500)
    expected = (1000 / 1_000_000) * 0.15 + (500 / 1_000_000) * 0.60
    assert cost == pytest.approx(expected, rel=1e-6)

def test_log_format_includes_all_required_fields():
    """Verify LLM log records contain required fields."""
    import json
    from io import StringIO

    log_stream = StringIO()
    handler = logging.StreamHandler(log_stream)
    logger.addHandler(handler)

    log_llm_call(
        model="gpt-4o-mini",
        input_tokens=100,
        output_tokens=50,
        latency_ms=500.0,
        user_id="user_1",
    )

    handler.flush()
    record = json.loads(log_stream.getvalue().strip())
    assert record["message"] == "llm_call"
    assert record["extra_fields"]["model"] == "gpt-4o-mini"
    assert record["extra_fields"]["total_tokens"] == 150
```

### Integration Tests

```python
@pytest.mark.asyncio
async def test_online_evaluation_valid_scores():
    """Verify evaluator returns scores in the expected range."""
    scores = await evaluate_response(
        question="What is the capital of France?",
        context="France is a country in Europe. Its capital is Paris.",
        response="The capital of France is Paris.",
    )
    for criterion, score in scores.items():
        assert 1 <= score <= 5, f"{criterion} score {score} out of range"

def test_embedding_drift_detection():
    """Verify drift detection flags shifted distributions."""
    ref = [np.random.rand(384) for _ in range(100)]
    drifted = [np.random.rand(384) + 0.5 for _ in range(100)]
    result = detect_embedding_drift(drifted, ref, threshold=0.1)
    assert result["drifted"] is True
```

### Observability Pipeline Tests

- [ ] Log records contain all required fields (timestamp, trace_id, model, tokens, latency)
- [ ] Log records with PII have content hashed correctly
- [ ] Metrics produce correct values for known token counts
- [ ] Cost calculation matches provider pricing for all tracked models
- [ ] Trace spans have correct parent-child relationships
- [ ] Prometheus metrics are registered and serve at /metrics
- [ ] Alert rules parse and evaluate correctly

## Anti-Patterns

| Anti-Pattern | Problem | Fix |
|---|---|---|
| Logging raw prompts everywhere | PII exposure, storage costs, compliance risk | Hash prompt content; store full content only in restricted trace store |
| No sampling in production | Trace store grows unbounded; too noisy to be useful | Sample 10-20% of traffic; sample 100% of errors and edge cases |
| Only tracking latency, not quality | 200 OK with bad response is invisible | Add quality metrics (faithfulness, relevance, refusal rate) |
| Prometheus for cost tracking | Histogram buckets lose exact cost; cannot bill per user | Use log-based cost attribution with exact token counts |
| No baseline for alerting | Static thresholds trigger during natural traffic patterns | Use dynamic baselines from rolling 7-day window |
| Ignoring guardrail observability | Cannot tell if guardrails are too aggressive or too permissive | Track flag rate, block rate, and false positive rate |
| Evaluating every response online | High cost, increased latency, potential bias | Use stratified sampling with over-sampling of edge cases |
| Single dashboard for all audiences | Operations team sees developer-level trace detail | Separate dashboards by audience (developer, ops, business, quality) |
| No model version tracking | Cannot correlate regressions with model updates | Log model version on every request |

## Completion Criteria

An LLM observability implementation is complete only when:

- [ ] every LLM call produces a structured log record with model, tokens, latency, and status
- [ ] prompt and response content are hashed; raw content is in restricted storage
- [ ] trace context spans every LLM call and is correlated with application logs
- [ ] metrics for token usage, latency, errors, and refusal rate are exported
- [ ] cost is calculated per request and attributed by model and user
- [ ] an observability platform (Langfuse, LangSmith, or custom OTel) is integrated
- [ ] alerts exist for refusal rate spikes, latency spikes, error rate spikes, and cost anomalies
- [ ] guardrail evaluations are instrumented with their own metrics
- [ ] online evaluation is configured with stratified sampling
- [ ] drift detection monitors input/output length, embeddings, and quality scores
- [ ] dashboards exist for development, operations, business, and quality audiences
- [ ] alert fatigue prevention is configured (dynamic baselines, rate limiting, severity levels)
- [ ] unit and integration tests verify logging, metrics, cost, and drift detection

## Related Skills

- `model-serving-production` — for infrastructure monitoring, health checks, and serving configuration
- `ai-evaluation` — for offline evaluation methodology, test sets, and golden datasets
- `rag-quality-review` — for RAG-specific evaluation and retrieval quality monitoring
- `llm-app-security` — for security threat modeling and hardening
- `prompt-injection-defense` — for prompt injection detection and defense
- `ai-cost-optimization` — for cost reduction strategies that complement cost tracking
