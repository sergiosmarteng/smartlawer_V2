---
name: ai-cost-optimization
description: Optimize LLM and AI application cost through prompt efficiency, caching, model routing, batching, retrieval control, evaluation and safe fallback strategies.
license: MIT
compatibility: opencode
metadata:
  category: ai-engineering
  stack: ai-cost-optimization
  version: "1.0.0"
orchestration:
  lead_for:
    - cost-optimization
  support_for: []
  conflicts_with: []
---

# AI Cost Optimization

Use this skill when reviewing, designing, or optimizing the cost of an LLM-powered application without blindly reducing quality.

The objective is to reduce token consumption, API costs, and compute usage through systematic strategies that are validated, measured, and reversible.

## When to Use This Skill

Load this skill when the task involves any of the following:

- reducing LLM API costs without degrading output quality
- designing a token budget for an AI feature
- implementing caching for LLM responses or embeddings
- routing between small and large models based on task difficulty
- setting user-level or tenant-level usage quotas
- optimizing a RAG pipeline for cost
- building cost monitoring and alerting
- reviewing the cost efficiency of an existing AI system

Do not load this skill for:
- general production cost optimization without AI components
- security budget or rate limiting decisions (use llm-app-security)
- evaluation methodology (use ai-evaluation skill)

## Principles

### Every Optimization Has a Quality Risk

Cost optimization is a tradeoff. Every change that reduces cost has the potential to reduce quality. Before implementing any optimization, document:

- **Expected saving**: estimated cost reduction per request, per day, or per month
- **Possible quality risk**: what could go wrong (lower accuracy, more refusals, worse formatting)
- **Validation method**: how you will measure whether quality degraded
- **Rollback strategy**: how to revert if quality drops below threshold

```python
class CostOptimization:
    name: str
    expected_saving: Cost
    quality_risk: str
    validation_method: str
    rollback_strategy: str
```

### Measure Before Optimizing

Do not optimize without first measuring current cost and quality. Without a baseline, you cannot tell whether an optimization helped or harmed.

### Optimize the Most Expensive Paths First

A 20% saving on a path that accounts for 80% of cost is far more valuable than a 50% saving on a path that accounts for 2% of cost. Profile before prioritizing.

### Production Safety

Cost optimizations should not break production. Every change must be:
- deployed behind a feature flag
- monitored for quality regression
- reversible without data loss
- tested against a golden evaluation set before rollout

## Token Budgeting

A token budget defines the maximum number of tokens a feature, user, or process can consume.

### Budget Dimensions

| Dimension | What It Limits | Example |
|---|---|---|
| Per-request input | Max input tokens per API call | 4000 tokens per user message |
| Per-request output | Max output tokens per API call | 1000 tokens per response |
| Per-session | Tokens per user session | 50000 tokens per conversation |
| Per-user daily | Tokens per user per day | 200000 tokens per user per day |
| Per-tenant monthly | Tokens per tenant per month | 10M tokens per tenant per month |
| Per-background-job | Tokens per batch job | 1M tokens per nightly aggregation |

### Setting Budgets

- Base budgets on observed usage for the 90th or 95th percentile user, not the maximum.
- Set hard limits that the application enforces, not just soft guidelines.
- Allow budget increases through an explicit review process.
- Monitor budget utilization and alert when approaching limits.
- Budget should account for both input and output tokens, at their respective costs.

### Budget Enforcement

```python
class TokenBudget:
    def __init__(self, max_input: int, max_output: int, max_daily: int):
        self.max_input = max_input
        self.max_output = max_output
        self.max_daily = max_daily
        self.daily_used = 0

    def check_request(self, input_tokens: int, output_tokens: int) -> bool:
        if input_tokens > self.max_input:
            return False
        if output_tokens > self.max_output:
            return False
        if self.daily_used + input_tokens + output_tokens > self.max_daily:
            return False
        return True

    def record_usage(self, tokens: int):
        self.daily_used += tokens

    def reset_daily(self):
        self.daily_used = 0
```

## Prompt Compression

Reduce the size of prompts by removing unnecessary content without losing the information needed for correct responses.

### Compression Techniques

| Technique | Saving | Quality Risk | Best For |
|---|---|---|---|
| Remove redundant instructions | Low (5-15%) | None | All prompts |
| Shorten few-shot examples | Medium (20-40%) | Low if examples are trimmed unsafely | Classification, extraction |
| Remove conversation history pruning policy | High (50-80%) | Medium — may lose context | Chat, multi-turn |
| Summarize conversation history | High (60-80%) | Medium — summarization loses detail | Long chat sessions |
| Use shorter system instructions | Low (5-10%) | Low | All prompts |
| Remove boilerplate from retrieved documents | Medium (20-40%) | Low if structure is preserved | RAG pipelines |
| Strip formatting (Markdown, HTML) from context | Medium (20-40%) | Low for plain-text models | RAG with raw documents |
| Deduplicate retrieved chunks | Medium (10-30%) | None | RAG pipelines |

### Validation for Prompt Compression

For every compression change:
1. Run the compressed and uncompressed prompts on a test set.
2. Compare output quality using the project's evaluation metrics.
3. Accept the compression only if quality stays within tolerance (e.g., faithfulness drops less than 0.02).
4. Monitor quality after deployment with a feature flag.

```python
def validate_compression(
    original_prompt: str,
    compressed_prompt: str,
    test_set: list[TestCase],
    metric: Callable[[str, str], float],
    tolerance: float = 0.02,
) -> bool:
    original_scores = [metric(ex.input, call(original_prompt, ex)) for ex in test_set]
    compressed_scores = [metric(ex.input, call(compressed_prompt, ex)) for ex in test_set]
    avg_original = sum(original_scores) / len(original_scores)
    avg_compressed = sum(compressed_scores) / len(compressed_scores)
    return avg_compressed >= avg_original - tolerance
```

## Model Routing

Use different models for different requests based on task difficulty, required quality, and cost.

### Routing Strategies

| Strategy | How It Works | Saving | Quality Risk |
|---|---|---|---|
| Task-based routing | Simple tasks use small/cheap models, complex ones use large/expensive models | High | Medium — incorrect routing may give poor results |
| Confidence-based routing | Small model tries first; if confidence is low, escalate to larger model | Medium | Low — fallback catches errors |
| Tier-based routing | Free users get small model, paid users get large model | High | Low — consistent per tier |
| Content-based routing | Short inputs use small model, long inputs use expensive model | Medium | Low — length correlates with complexity but not always |
| Cascade routing | Try cheapest model first; if output fails validation, retry with larger model | High | Low — validation gates catch failures |

### Cascade Routing Example

```python
MODEL_TIERS = [
    {"model": "fast-cheap", "max_retries": 1, "cost_per_call": 0.001},
    {"model": "balanced", "max_retries": 1, "cost_per_call": 0.005},
    {"model": "best", "max_retries": 2, "cost_per_call": 0.02},
]

def cascade_generate(prompt: str, validator: Callable[[str], bool]) -> tuple[str, str]:
    for tier in MODEL_TIERS:
        for attempt in range(tier["max_retries"]):
            response = call_model(tier["model"], prompt)
            if validator(response):
                return response, tier["model"]
    raise CascadeFailure("All model tiers failed validation")
```

### Routing Constraints

- Define clear criteria for each route (task type, input length, user tier, required latency).
- Monitor routing decisions to detect routing quality drift.
- Test routing logic on a representative sample from each route.
- Ensure routing is deterministic for the same input and user (no random routing).

## Small-Model-First Strategies

Use the smallest model that can produce acceptable output for a given task.

### When Small Models Work

| Task Type | Suitable Small Model? | Risk |
|---|---|---|
| Classification (few labels) | Yes | Low — simple tasks |
| Structured extraction (known schema) | Yes | Medium — needs schema adherence |
| Summarization (short) | Yes | Low for short, high for long |
| Translation (common languages) | Yes | Low with good training data |
| Code generation (simple patterns) | Yes | Medium for domain-specific code |
| Reasoning (multi-step) | No | High — small models struggle |
| Creative writing | No | Low creative quality |
| RAG generation | Depends on retrieval quality | Medium — needs good retrieval |
| Safety classification | Yes | Low — specialized small models excel |

### Quality Validation for Small Models

Before routing any task to a small model:

1. Run the small model on a sample of production traffic (500-1000 examples).
2. Measure the primary quality metric (faithfulness, accuracy, relevance).
3. Compare against the current model's scores.
4. Accept only if the small model meets the quality threshold for that task.
5. Monitor per-task quality after deployment.

### Model Tier Definitions

| Tier | Example Models | Relative Cost | Use Case |
|---|---|---|---|
| Micro | `gemini-2.0-flash-lite`, `gpt-4o-mini` | 0.1x - 0.3x | Classification, simple extraction |
| Fast | `gemini-2.0-flash`, `gpt-4o-mini` | 0.3x - 0.5x | Chat, structured output, summarization |
| Balanced | `gpt-4o`, `claude-3.5-sonnet` | 1x (baseline) | General purpose, RAG |
| Best | `claude-opus`, `gpt-4.5` | 5x - 20x | Complex reasoning, safety-critical |

## Caching

Cache results to avoid repeated API calls for identical or similar inputs.

### Cacheable Content

| Content | Cache Key | TTl | Saving | Quality Risk |
|---|---|---|---|---|
| LLM response (identical query) | Exact input + system prompt hash | Minutes to hours | High | None for exact matches |
| LLM response (similar query) | Semantic embedding of query | Minutes | Medium | Medium — may serve stale or mismatched response |
| Embedding vector | Input text hash | Days to permanent | High | None for exact matches |
| Reranker score | (Query hash, chunk hash) | Hours | Medium | Low |
| Retrieval results | Query + filters hash | Minutes | Medium | Low — stale results |
| Classifier output | Input text hash | Hours | Medium | Medium — drift over time |

### Cache Implementation

```python
class ResponseCache:
    def __init__(self, backend: CacheBackend, default_ttl: int = 3600):
        self.backend = backend
        self.default_ttl = default_ttl

    def make_key(self, system_prompt: str, user_input: str) -> str:
        return hashlib.sha256(
            (system_prompt + user_input).encode()
        ).hexdigest()

    async def get(self, system_prompt: str, user_input: str) -> str | None:
        key = self.make_key(system_prompt, user_input)
        return await self.backend.get(key)

    async def set(self, system_prompt: str, user_input: str, response: str):
        key = self.make_key(system_prompt, user_input)
        await self.backend.set(key, response, ttl=self.default_ttl)
```

### Cache Invalidation

- Cache must be invalidated when the underlying data changes (documents are updated, models change).
- Set appropriate TTLs based on data freshness requirements.
- Use cache busting for system-level changes (prompt updates, model version changes).
- Monitor cache hit rate — low hit rate suggests poor cache key design or inappropriate caching.

## Retrieval Limiting

Reduce retrieval costs by fetching only as many documents as needed and no more.

### Strategies

| Strategy | Saving | Quality Risk |
|---|---|---|
| Reduce top_k | High (linear with k) | Medium — may miss relevant documents |
| Adaptive top_k | Medium | Low — adjusts based on query needs |
| Metadata pre-filtering | Medium | Low — reduces candidates before search |
| Query rewriting for precision | Medium | Medium — may narrow too much |
| Chunk refinement (smaller chunks) | Medium | Medium — may fragment information |

### Adaptive top_k

Do not increase top_k blindly. Instead, determine the optimal number of documents to retrieve per query:

```python
def adaptive_top_k(query: str, min_k: int = 3, max_k: int = 20) -> int:
    """Estimate the optimal number of documents to retrieve."""
    query_length = len(query.split())
    if query_length < 5:
        return min_k  # short query, fewer results needed
    if query_length > 30:
        return max_k  # long query may need more results
    # Scale linearly between min and max
    return min_k + (query_length - 5) * (max_k - min_k) // 25
```

### Validation for top_k Changes

- Before reducing top_k, measure recall@k at the current and proposed values.
- Accept a reduction only if recall@k drops less than a threshold (e.g., 0.02).
- Monitor downstream generation quality after deployment.

## Deduplication

Avoid processing the same content multiple times.

### Deduplication Opportunities

| Opportunity | Mechanism | Saving |
|---|---|---|
| Identical user queries | Response cache | High |
| Similar retrieved chunks | Chunk deduplication at retrieval time | Medium |
| Repeated document processing | Document hash cache in ingestion | High |
| Repeated embedding computation | Embedding cache | High |
| Repeated classification calls | Classifier output cache | Medium |

### Chunk Deduplication

```python
CHUNK_HASHES: set[str] = set()

def deduplicate_chunks(chunks: list[Chunk]) -> list[Chunk]:
    seen = set()
    unique = []
    for chunk in chunks:
        chunk_hash = hashlib.sha256(chunk.text.encode()).hexdigest()
        if chunk_hash not in seen and chunk_hash not in CHUNK_HASHES:
            seen.add(chunk_hash)
            unique.append(chunk)
    CHUNK_HASHES.update(seen)
    return unique
```

## Batching

Combine multiple independent requests into a single API call to reduce per-request overhead and improve throughput.

### When to Batch

| Scenario | Batching Benefit | Risk |
|---|---|---|
| Multiple embedding requests | High — reduces API calls significantly | None — embeddings are independent |
| Multiple classification requests | Medium — shared context reduces overhead | Low — results are independent |
| Multiple generation requests | Low-medium — depends on model batching support | Medium — one bad input may affect others |
| Ingestion pipeline | High — large throughput | Low — independent documents |

### Batching Implementation

```python
class EmbeddingBatcher:
    def __init__(self, batch_size: int = 32, max_wait: float = 0.5):
        self.batch_size = batch_size
        self.max_wait = max_wait
        self.queue: list[tuple[str, asyncio.Future]] = []
        self._lock = asyncio.Lock()

    async def embed(self, text: str) -> list[float]:
        future = asyncio.get_event_loop().create_future()
        async with self._lock:
            self.queue.append((text, future))
            if len(self.queue) >= self.batch_size:
                asyncio.create_task(self._flush())
            else:
                asyncio.create_task(self._delayed_flush())
        return await future

    async def _flush(self):
        async with self._lock:
            batch = self.queue[:]
            self.queue.clear()
        texts = [item[0] for item in batch]
        futures = [item[1] for item in batch]
        try:
            embeddings = await embed_batch(texts)
            for future, embedding in zip(futures, embeddings):
                future.set_result(embedding)
        except Exception as exc:
            for future in futures:
                future.set_exception(exc)

    async def _delayed_flush(self):
        await asyncio.sleep(self.max_wait)
        if self.queue:
            await self._flush()
```

### Batching Constraints

- Set a maximum wait time to avoid excessive latency for the first request in a batch.
- Do not batch requests with different priority levels.
- Monitor batch size distribution — consistently small batches suggest batching is not effective.
- Ensure error isolation: one failed item in a batch should not fail the entire batch.

## Streaming Tradeoffs

Streaming responses improves perceived latency but can increase cost.

### Streaming Cost Analysis

| Factor | Streaming | Non-Streaming |
|---|---|---|
| Time-to-first-token (TTFT) | Lower | Higher |
| Total output tokens | Same | Same |
| API cost | Same (per-token pricing) | Same |
| Compute overhead | Slightly higher (per-chunk processing) | Lower |
| User experience | Better (progressive display) | Worse (full wait) |
| Validation feasibility | Harder (validate progressively or buffer) | Easier (validate after complete) |

### When to Stream

- **Stream when**: user-facing chat, real-time applications, long generation tasks.
- **Do not stream when**: background processing, batch jobs, structured output that requires full validation before use.

### Streaming Cost Optimization

- If streaming, buffer the full response in background for validation (no extra cost).
- Stream to the user but validate asynchronously — if validation fails, display a correction.
- For structured output with streaming, validate incrementally if the format allows (e.g., per-field for JSON).

## Retry Cost Control

Retries multiply cost by the number of attempts. Control retry costs aggressively.

### Retry Guidelines

- Set a maximum retry count per request (e.g., 2 total attempts including the first).
- Do not retry on validation errors (the model is unlikely to produce valid output on retry without feedback).
- Include the parsing error or failure reason in the retry prompt to give the model useful context.
- Use a different model tier for the retry (e.g., retry with a larger model if the small model failed).
- Log retry attempts and monitor the retry rate — a high retry rate indicates a systemic issue.

### Retry Cascade with Cost Awareness

```python
RETRY_CASCADE = [
    {"model": "fast-cheap", "cost": 0.001, "condition": lambda r: True},
    {"model": "balanced", "cost": 0.005, "condition": lambda r: validate_schema(r)},
    {"model": "best", "cost": 0.02, "condition": lambda r: True},
]

def generate_with_cost_control(prompt: str) -> tuple[str, float]:
    total_cost = 0.0
    last_error = ""
    for tier in RETRY_CASCADE:
        response = call_model(tier["model"], prompt + "\n\nPrevious error: " + last_error)
        total_cost += tier["cost"]
        if tier["condition"](response):
            return response, total_cost
        last_error = f"Output did not pass validation: {response[:200]}"
    raise RetryExceededError(f"All retries failed, total cost: {total_cost}")
```

## Evaluation Cost Control

Running evaluation on LLM outputs is itself an LLM call and has a cost.

### Cost-Effective Evaluation

| Strategy | Saving | Quality Risk |
|---|---|---|
| Sample evaluation (not full set) | High (proportional to sample rate) | Medium — may miss edge cases |
| Small model judge | High (3-10x cheaper) | Medium — less accurate |
| Automatic metrics instead of LLM judge | Very high | Low for structural metrics |
| Fewer evaluation dimensions | Medium | Low — focus on critical metrics |
| Evaluate only on changes | High | Low — skip stable pipelines |

### Evaluation Budget

```python
EVALUATION_BUDGET = {
    "daily_api_calls": 500,  # max LLM-as-judge calls per day
    "daily_human_hours": 2,  # max human evaluation hours per day
    "cost_per_evaluation": 0.02,  # target cost per evaluation run
}
```

### Prioritize Evaluation Spend

1. Safety metrics (highest priority)
2. Faithfulness / grounding
3. Task completion / correctness
4. Structural validity
5. Style / formatting (lowest priority)

Allocate evaluation budget proportionally.

## Logging Token Usage

Track token consumption to understand cost drivers and detect anomalies.

### What to Log

| Field | Example | Purpose |
|---|---|---|
| Request ID | `req_abc123` | Trace individual requests |
| User ID | `user_42` | Attribute cost to users |
| Model | `gpt-4o` | Track per-model cost |
| Input tokens | 1520 | Input cost driver |
| Output tokens | 340 | Output cost driver |
| Cached input tokens | 800 | Discount applied |
| Latency | 1200ms | Correlate cost and performance |
| Endpoint / feature | `/chat` | Attribute cost to features |
| Timestamp | 2026-07-08T12:00:00Z | Time-based analysis |

### Cost Calculation

```python
MODEL_PRICING = {
    "gpt-4o": {"input": 0.0000025, "output": 0.00001},     # per token
    "gpt-4o-mini": {"input": 0.00000015, "output": 0.0000006},
    "claude-3.5-sonnet": {"input": 0.000003, "output": 0.000015},
}

def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    pricing = MODEL_PRICING[model]
    return input_tokens * pricing["input"] + output_tokens * pricing["output"]
```

### Token Usage Dashboard

Monitor:
- Cost per feature per day
- Cost per user per day (top-N users)
- Cost per model per day
- Average tokens per request (input, output)
- Cache hit rate
- Retry rate
- Throttled / rejected requests

## Quota Limits

Enforce usage limits to prevent runaway costs from unexpected traffic, bugs, or abuse.

### Quota Dimensions

| Quota | Granularity | Enforcement |
|---|---|---|
| Requests per minute | Per user, per IP | Rate limiter |
| Tokens per hour | Per user, per tenant | Token bucket |
| Cost per day | Per user, per tenant | Budget tracker |
| Concurrent requests | Per user | Semaphore |
| Background job tokens | Per job | Pre-computed budget |

### Quota Enforcement

```python
class TokenQuota:
    def __init__(self, daily_limit: int):
        self.daily_limit = daily_limit
        self.used_today: dict[str, int] = {}

    def check_and_consume(self, user_id: str, tokens: int) -> bool:
        used = self.used_today.get(user_id, 0)
        if used + tokens > self.daily_limit:
            return False
        self.used_today[user_id] = used + tokens
        return True

    def remaining(self, user_id: str) -> int:
        return max(0, self.daily_limit - self.used_today.get(user_id, 0))
```

### Quota Response

When a quota is exceeded:
- Return a clear error message to the user or caller.
- Log the rejection with user ID and attempted usage.
- Allow the user to see their current usage and limit.
- Do not silently degrade quality — either serve at full quality or reject.
- Implement an escalation path for legitimate users who need higher limits.

## User-Level Limits

Apply per-user cost controls based on usage patterns, subscription tiers, or risk levels.

### Limit Strategies

| Strategy | Implementation | Best For |
|---|---|---|
| Token cap per day | Hard limit on daily token consumption | All users |
| Token cap per session | Limit per conversation session | Chat applications |
| Tier-based limits | Different limits per subscription tier | SaaS products |
| Graduated pricing | Higher usage costs more per token | Usage-based billing |
| Auto-downgrade | Reduce model quality after exceeding threshold | Free-tier users |

### User Tier Example

```python
USER_TIERS = {
    "free": {
        "model": "fast-cheap",
        "daily_token_limit": 50000,
        "max_output_tokens": 500,
        "caching_enabled": True,
    },
    "pro": {
        "model": "balanced",
        "daily_token_limit": 500000,
        "max_output_tokens": 2000,
        "caching_enabled": True,
    },
    "enterprise": {
        "model": "best",
        "daily_token_limit": 5000000,
        "max_output_tokens": 4000,
        "caching_enabled": True,
    },
}
```

## Background Job Limits

Background jobs (ingestion pipelines, nightly evaluations, batch processing) can consume significant cost if unbounded.

### Job Budgeting

- Set explicit token or cost budgets per job before execution.
- Monitor job cost in real time and terminate jobs that exceed budget.
- Estimate job cost before starting (e.g., documents * estimated tokens per document).
- Schedule expensive jobs during low-traffic periods.
- Implement incremental processing with checkpointing to avoid redoing work on failure.

### Background Job Budget

```python
class JobBudget:
    def __init__(self, max_tokens: int, max_cost: float):
        self.max_tokens = max_tokens
        self.max_cost = max_cost
        self.total_tokens = 0
        self.total_cost = 0.0

    def consume(self, model: str, tokens: int) -> bool:
        cost = calculate_cost(model, tokens, 0)
        if self.total_tokens + tokens > self.max_tokens:
            return False
        if self.total_cost + cost > self.max_cost:
            return False
        self.total_tokens += tokens
        self.total_cost += cost
        return True
```

## Cost Regression Tests

Prevent cost regressions from being deployed unnoticed.

### Cost Test Cases

| Test | What It Checks | Failure Threshold |
|---|---|---|
| Average tokens per request | Cost per typical request | +10% from baseline |
| p99 tokens per request | Worst-case cost per request | +20% from baseline |
| Cost per golden set run | Full evaluation cost | +15% from baseline |
| Cache hit rate | Caching effectiveness | -5% from baseline |
| Retry rate | Retry cost | +2% from baseline |

### Cost Regression CI Gate

```yaml
# ci-cost-gate.yml
cost_gate:
  enabled: true
  metrics:
    - name: avg_input_tokens
      baseline: 1200
      max_regression: 0.10
    - name: avg_output_tokens
      baseline: 400
      max_regression: 0.10
    - name: cache_hit_rate
      baseline: 0.60
      max_degradation: 0.05
    - name: retry_rate
      baseline: 0.03
      max_increase: 0.02
  evaluation:
    run_on: golden_set_v2
    comparison: against_baseline
  rollback:
    automatic: true
    trigger: any_metric_exceeds_threshold
```

### Cost Baseline Management

- Record cost baselines for the current production configuration.
- Run cost regression tests on every PR that changes prompts, models, or retrieval parameters.
- Update baselines when intentional cost changes are deployed.
- Alert when cost metrics drift without a corresponding code change.

## Quality versus Cost Tradeoff

Document and communicate every decision that trades quality for cost.

### Tradeoff Documentation Template

```text
Optimization: [Name of the optimization]
Expected saving: [Estimated cost reduction]
Quality impact: [What quality metric is affected and by how much]
Acceptance criteria: [Minimum acceptable quality level]
Validation method: [How quality impact will be measured]
Rollback plan: [How to revert if quality drops below threshold]
Owner: [Person responsible for monitoring]
Review date: [When to re-evaluate this decision]
```

### Decision Matrix

| Scenario | Optimize? | Reasoning |
|---|---|---|
| Quality is above threshold, cost is high | Yes | Room to optimize without crossing threshold |
| Quality is near threshold, cost is high | Cautiously | Measure carefully, optimize only where quality risk is low |
| Quality is below threshold, cost is high | No | Fix quality first, then optimize |
| Quality is above threshold, cost is low | No | Not worth the effort |
| Quality is at threshold, cost is at budget | No | Both are at acceptable levels |

## When Not to Optimize

Cost optimization is not always the right priority.

### Do Not Optimize When

- **Quality is below the minimum threshold.** Fix quality first. Reducing cost at the expense of quality makes the product worse.
- **Cost is already within budget.** Optimization has its own cost (engineering time, complexity, maintenance). Spend effort where it matters.
- **The system is in active development.** Patterns may change. Optimize after the design stabilizes.
- **The optimization increases complexity significantly.** A 10% cost saving that doubles maintenance burden is rarely worth it.
- **The optimization reduces observability.** If caching, batching, or routing makes the system harder to debug, the operational cost may exceed the savings.
- **The optimization introduces coupling.** Routing logic that is tightly coupled to specific model versions will break when models change.
- **User experience would degrade measurably.** If caching serves stale data or routing produces inconsistent quality, users will notice.

### Optimization Budget

Treat optimization work like any other feature: allocate a budget, define success criteria, and measure the outcome. Do not optimize indefinitely.

## Required Review Output

When reviewing AI application cost, produce this summary:

```text
System overview:
[Name, purpose, and cost profile of the reviewed system.]

Current cost baseline:
[Average cost per request, per user per day, per month.
Breakdown by model, feature, and user tier.]

Token usage:
[Average input/output tokens per request, p50/p95/p99.
Cache hit rate. Retry rate. Throttling rate.]

Top cost drivers:
[Most expensive features, user tiers, and models.]

Optimizations in place:
[List of active optimizations with their estimated savings,
quality impact, validation method, and rollback strategy.]

Identified opportunities:
[Prioritized list of potential optimizations with expected
saving, quality risk, and implementation effort.]

Quality metrics:
[Current quality scores alongside cost metrics.
Any quality degradation from past optimizations.]

Cost regression tests:
[Test coverage, baseline values, CI gate status.]

Recommendations:
[Prioritized list of optimizations to implement or avoid.]
```

## Completion Criteria

AI cost optimization work is complete only when:

- current cost is measured and baselined per feature, user, and model
- the most expensive paths are identified and prioritized for optimization
- each optimization documents expected saving, quality risk, validation method, and rollback strategy
- prompt compression is validated against a test set before deployment
- model routing is implemented with clear criteria and quality validation per route
- caching is implemented for repeated queries, embeddings, and retrieval results
- retrieval top_k is set based on measured recall, not arbitrarily
- deduplication is applied to chunks, queries, and embeddings
- batching is implemented for embedding and classification calls where beneficial
- streaming decisions are documented with rationale
- retry costs are controlled with maximum limits and cascade logic
- evaluation costs are measured and optimized
- token usage is logged per request with user, model, and feature attribution
- quota limits exist per user and per tenant with enforcement
- background jobs have explicit token or cost budgets
- cost regression tests exist with baselines and CI gates
- quality metrics are monitored alongside cost metrics
- each tradeoff decision is documented with acceptance criteria
- optimizations that would degrade quality below threshold are explicitly rejected
