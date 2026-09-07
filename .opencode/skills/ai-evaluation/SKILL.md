---
name: ai-evaluation
description: Design and review evaluation workflows for LLM, RAG and AI systems, including test sets, metrics, judge prompts, reliability, bias, regression testing and failure analysis.
license: MIT
compatibility: opencode
metadata:
  category: ai-engineering
  stack: ai-evaluation
  version: "1.0.0"
orchestration:
  lead_for:
    - ai-evaluation
  support_for: []
  conflicts_with:
    - llm-observability
    - rag-quality-review
---

# AI Evaluation

Use this skill when designing, reviewing, or improving evaluation workflows for LLM outputs, RAG pipelines, structured-output systems, or any AI-powered feature.

The objective is to build evaluation pipelines that produce trustworthy signals about system quality — not to inflate scores, chase benchmarks, or treat LLM judgments as ground truth.

## When to Use This Skill

Load this skill when the task involves any of the following:

- building a test set for evaluating LLM output quality
- designing a human or automated evaluation workflow
- selecting metrics for a specific AI task
- implementing LLM-as-judge evaluation
- creating regression tests for AI system changes
- monitoring output quality drift in production
- evaluating RAG retrieval and generation quality
- reviewing an existing evaluation pipeline for rigour
- comparing two models, prompts, or system versions statistically

Do not load this skill for:
- general software testing and debugging (use testing-and-debugging skill)
- security-specific AI evaluation (use llm-app-security or prompt-injection-defense skills)
- traditional non-AI benchmark design

## Evaluation Goals

Define the evaluation goal before selecting metrics or building datasets. The goal determines what to measure and how to interpret results.

### Common Evaluation Goals

| Goal | Question | Key Metrics |
|---|---|---|
| Correctness | Does the output contain the right answer? | Exact match, F1, accuracy |
| Faithfulness | Is the output grounded in the provided context? | Faithfulness score, citation precision |
| Helpfulness | Does the output address the user's need? | Answer relevance, task completion rate |
| Safety | Does the output violate policies or contain harmful content? | Safety violation rate, refusal correctness |
| Reliability | Does the system produce consistent output? | Inter-rater reliability, output variance |
| Latency | How fast does the system respond? | p50/p95/p99 latency |
| Cost | What does each request cost? | Cost per request, cost per task |

### Evaluation Types

- **Point evaluation**: measure a single output in isolation
- **Pairwise comparison**: compare outputs from two systems on the same input
- **Ranked evaluation**: rank multiple outputs by quality
- **Pass/fail evaluation**: check specific criteria (safety, format)
- **Continuous scoring**: assign a score on a scale (1-5, 0-1)

### Pre-Evaluation Questions

- What decision will the evaluation inform (ship, revert, tune)?
- What is the minimum quality threshold for production?
- What is the acceptable false positive rate for safety metrics?
- How much evaluation noise is acceptable before the signal is useless?
- How will the evaluation set be maintained as the system evolves?

## Dataset Construction

### Principles

- Test sets must reflect the production distribution, not an idealized version of it.
- Include realistic inputs, not only well-formed ones.
- Document how each example was created and labeled.
- Split data into training, validation, and test sets when tuning any parameter.
- Never tune on the test set.
- Version test sets and track changes over time.

### Sourcing Test Examples

| Source | Strength | Weakness |
|---|---|---|
| Production logs | Reflects real user behavior | May contain PII; needs sanitization |
| Manual authoring | High quality, targeted | Expensive, may miss edge cases |
| Synthetic generation | Covers edge cases cheaply | May not reflect real distribution |
| Public benchmarks | Comparable across systems | May not match your domain |
| User feedback | Captures real failures | Sparse, biased toward extreme experiences |

### Balancing the Dataset

- Balance by difficulty (easy, medium, hard)
- Balance by expected output type (short answer, structured, free text)
- Include examples where the system is expected to succeed and fail
- Include examples where abstention is correct
- Include examples with ambiguous or incomplete context

### Sample Size

- Minimum 100 examples per evaluation dimension for meaningful metrics
- 500-1000 examples per dimension for reliable comparison between systems
- More examples needed when:
  - the metric has high variance
  - the expected effect size is small
  - subpopulations need separate analysis

## Golden Test Sets

A golden test set is a labeled set of input-output pairs that serves as the ground truth for evaluation.

### Requirements

- Every example has a verified correct answer or rubric.
- Answers are reviewed by at least one person other than the author.
- Edge cases are explicitly labeled (tricky, requires reasoning, ambiguous).
- The test set is versioned and immutable once published.
- Changes to the test set require a review and version bump.

### Maintenance

- Add new examples when new failure patterns are discovered.
- Remove or update examples when the task definition changes.
- Review the test set periodically for quality drift.
- Track the age of each example — stale examples lose relevance.

```python
class GoldenTestSet:
    version: str
    examples: list[GoldenExample]
    created_at: datetime
    updated_at: datetime
    coverage_notes: str

class GoldenExample:
    input: str | dict
    expected_output: str | dict | None  # None when abstention is expected
    rubric: str | None  # criteria for scoring
    difficulty: Literal["easy", "medium", "hard"]
    tags: list[str]  # "safety", "reasoning", "multi-hop", "structured"
```

## Edge Cases

Edge cases are inputs that differ from the typical distribution. They reveal brittle behavior not apparent on standard examples.

### Edge Case Categories

| Category | Example |
|---|---|
| Empty input | "", null, whitespace-only |
| Very short input | "yes", "no", "?" |
| Very long input | 10x the expected input length |
| Ambiguous input | "It depends" without context |
| Contradictory context | Two documents that say opposite things |
| Irrelevant context | Retrieved documents unrelated to the query |
| Multi-lingual input | Input in a language the system was not tested on |
| Special characters | Unicode, escape sequences, control characters |
| Adversarial input | Prompt injection, role-play, encoding tricks |
| Out-of-scope request | "Write a poem" when the system only answers factual questions |
| Missing fields | Required fields absent in structured input |
| Numerical edge cases | Zero, negative numbers, very large numbers, NaN |

### Edge Case Coverage

- Document which edge cases the test set covers.
- Add edge cases to the golden set explicitly — do not assume they are covered by standard examples.
- Test edge cases separately from standard examples to measure degradation.
- Track edge case performance over time — it may degrade without affecting standard metrics.

## Regression Tests

Regression tests capture specific failures that occurred in production or evaluation and verify they do not recur.

### What to Regress

- Every confirmed bug or failure in production
- Every safety violation
- Every hallucination or factual error
- Every citation error
- Every incorrect abstention (false positive or false negative)
- Every format violation

### Test Format

```python
class RegressionTest:
    input: str | dict  # the exact input that caused the failure
    expected_behavior: str  # description of what should happen
    pass_condition: Callable[[Output], bool]  # how to check success
    source: str  # where this failure was discovered
    created_at: datetime
```

### Running Regression Tests

- Run regression tests on every system change.
- Fail the CI pipeline if any regression test does not pass.
- When a regression test is intentionally invalidated (system behavior changed), document the reason.

## Human Evaluation

Human evaluation is the most reliable signal but is expensive and slow. Use it for calibration and validation of automated metrics, not for every change.

### When to Use Human Evaluation

- Calibrating an LLM-as-judge pipeline
- Validating a new metric before automation
- Evaluating subjective dimensions (tone, helpfulness, creativity)
- Auditing safety-critical outputs
- Building the initial golden test set

### Rating Scales

| Scale Type | Example | Best For |
|---|---|---|
| Binary | Correct / Incorrect | Factual accuracy |
| Likert | 1-5 scale | Quality, helpfulness |
| Rubric-based | Score per criterion (0-2) | Multi-dimensional evaluation |
| Pairwise | A is better / B is better / Tie | Model comparison |
| Ranked | Rank outputs 1-N | Sorting by quality |

### Rater Selection

- Raters should match the target user demographic when possible.
- Provide clear instructions and examples before rating.
- Calibrate raters on a shared set before independent work.
- Raters must understand the domain and task.
- Rotate raters to avoid fatigue and bias.

## LLM-as-Judge

Using an LLM to evaluate outputs is scalable but has significant limitations. Treat LLM judge scores as approximate signals, not ground truth.

### Limitations

- **Position bias**: the judge prefers the first or last option in pairwise comparisons.
- **Verbosity bias**: the judge prefers longer, more detailed outputs regardless of correctness.
- **Self-enhancement bias**: the judge prefers outputs that match its own style.
- **Rubric overfitting**: the judge scores highly on rubric criteria while missing the actual quality.
- **Injection susceptibility**: an adversarial output can manipulate the judge's score.
- **Inconsistency**: the same input can receive different scores across calls.
- **Calibration drift**: judge behavior changes with model updates.

Never treat LLM judge output as ground truth without checks.

### Mitigations

- Randomize the order of outputs in pairwise comparisons.
- Evaluate multiple times per example and average scores.
- Calibrate the judge against human judgments on a held-out set.
- Use structured output (scored rubric) instead of free-text judgment.
- Include control examples with known correct scores.
- Monitor judge agreement with human raters over time.
- Version the judge model and prompt.

### Judge Prompt Design

```text
You are evaluating an AI assistant's response. Score the response
on the following criteria. For each criterion, assign 0 (fail) or
1 (pass). Output only a JSON object with the scores.

Criteria:
- correctness: The response contains the correct factual answer.
- completeness: The response addresses all parts of the query.
- safety: The response does not contain harmful or policy-violating content.
- citation: The response cites sources correctly (N/A if no citation needed).

Input:
{input}

Response to evaluate:
{response}

Output format:
{"correctness": 0 or 1, "completeness": 0 or 1, "safety": 0 or 1, "citation": 0 or 1}
```

### Calibration

- Compare LLM judge scores to human scores on a calibration set.
- Compute agreement metrics (Cohen's kappa, accuracy, F1).
- Set a minimum agreement threshold (e.g., Cohen's kappa >= 0.6) before trusting the judge.
- If agreement is below threshold, revise the rubric or switch to human evaluation.
- Recalibrate when the judge model or prompt changes.

```python
def calibrate_judge(
    judge: Judge,
    calibration_set: list[ExampleWithHumanScore],
    threshold_kappa: float = 0.6,
) -> bool:
    human_scores = [ex.human_score for ex in calibration_set]
    judge_scores = [judge.evaluate(ex.input, ex.response) for ex in calibration_set]
    kappa = cohens_kappa(human_scores, judge_scores)
    return kappa >= threshold_kappa
```

## Rubric Design

A rubric defines the criteria and scoring rules for evaluation. A well-designed rubric reduces rater disagreement and makes scores interpretable.

### Rubric Components

- **Criteria**: what dimensions are evaluated (correctness, clarity, safety).
- **Scales**: how each criterion is scored (pass/fail, 1-5, 0-2).
- **Anchors**: what each score means with concrete examples.
- **Instructions**: how to apply the rubric, including edge cases.

### Rubric Quality Checklist

- [ ] Each criterion is independent (no overlap).
- [ ] Each criterion is observable (raters can point to evidence in the output).
- [ ] Score levels have clear, distinct definitions.
- [ ] Score definitions include examples of each level.
- [ ] The rubric covers edge cases (tie, N/A, ambiguous).
- [ ] The rubric is tested on a sample before full deployment.
- [ ] Raters agree on rubric interpretation (measured by calibration).

### Example Rubric

```text
Criterion: Faithfulness

Score 0: The response contains claims not supported by the provided context.
  - Example: Context says "Temperature was 30°C."
    Response says "Temperature was 35°C."

Score 1: The response only contains claims supported by the provided context,
but may omit relevant information.
  - Example: Context says "The sky is blue and clouds are white."
    Response says "The sky is blue."

Score 2: The response only contains claims supported by the context and
includes all relevant information from the context.
```

## Inter-Rater Reliability

Inter-rater reliability (IRR) measures how consistently different raters score the same outputs. Low IRR means the rubric or task definition is unclear.

### When to Measure IRR

- Before deploying a new evaluation rubric.
- When onboarding new raters.
- Periodically during ongoing evaluation to detect rater drift.
- Whenever the evaluation task changes.

### IRR Metrics

| Metric | When to Use | Interpretation |
|---|---|---|
| Cohen's kappa | Two raters, categorical scores | >= 0.6 substantial agreement |
| Fleiss' kappa | Three+ raters, categorical scores | >= 0.6 substantial agreement |
| Spearman correlation | Two raters, ranked scores | >= 0.7 strong correlation |
| ICC (Intraclass correlation) | Two+ raters, continuous scores | >= 0.75 good reliability |
| Percentage agreement | Any number of raters | Simple but does not account for chance |

### Addressing Low IRR

- Review rubric definitions with raters — ambiguous criteria cause disagreement.
- Add more concrete examples to score anchors.
- Reduce the number of score levels (e.g., 5-point to 3-point).
- Split a vague criterion into more specific sub-criteria.
- Retrain raters on problematic examples.
- Remove raters who consistently disagree with the consensus.

## Automatic Metrics

Automatic metrics are fast, cheap, and reproducible. They are best for catching clear failures, not for measuring subjective quality.

### Lexical Metrics

| Metric | What It Measures | Limitations |
|---|---|---|
| Exact match | Whether output exactly matches expected | Punctuation-sensitive, no partial credit |
| F1 / ROUGE-L | N-gram overlap with reference | Misses semantic equivalence |
| BLEU | N-gram precision (translation-focused) | Poor for free-form generation |
| METEOR | Unigram matching with synonym support | Better than BLEU for short text |
| TER | Edit distance to reference | Translation-focused |

### Task-Specific Automatic Metrics

| Metric | What It Measures |
|---|---|
| JSON validity | Whether output is parseable JSON |
| Schema validity | Whether output matches a Pydantic/Zod schema |
| Enum accuracy | Whether output uses correct enum values |
| Format compliance | Whether output follows required format (Markdown, XML) |
| Length compliance | Whether output is within allowed length |
| Language match | Whether output is in the expected language |

### Semantic Metrics

| Metric | What It Measures | Implementation |
|---|---|---|
| BERTScore | Semantic similarity using BERT embeddings | Correlates with human judgment |
| BLEURT | Learned evaluation metric | Requires fine-tuned model |
| COMET | Translation quality | Specific to translation |
| Sentence embedding cosine | Cosine similarity of embeddings | Simple, fast, coarse |

## Task-Specific Metrics

Different tasks require different metrics. Select metrics based on the task, not convention.

| Task | Primary Metrics | Secondary Metrics |
|---|---|---|
| Question answering | Exact match, F1 | Faithfulness, abstention correctness |
| Summarization | ROUGE-L, faithfulness | Conciseness, coverage |
| Translation | BLEU, COMET | Language accuracy, fluency |
| Code generation | Functional correctness, syntax validity | Style match, documentation |
| Classification | Accuracy, F1 per class | Calibration, confidence |
| Structured extraction | JSON validity, schema validity, field accuracy | Enum accuracy, null handling |
| Chat / dialogue | Answer relevance, safety, task completion | Fluency, tone |
| Instruction following | Rubric score per instruction dimension | Completeness |

### Defining Task-Specific Metrics

When standard metrics do not fit the task, define custom metrics:

```python
from pydantic import BaseModel

class CitationAccuracy(BaseModel):
    total_citations: int
    correct_citations: int
    incorrect_citations: int
    hallucinated_citations: int  # citations to non-existent sources

    @property
    def precision(self) -> float:
        if self.total_citations == 0:
            return 1.0
        return self.correct_citations / self.total_citations
```

## RAG Evaluation

RAG evaluation requires separate metrics for retrieval and generation. A good retrieval can still produce bad generation, and vice versa.

### Retrieval Metrics

| Metric | What It Measures |
|---|---|
| Recall@k | Fraction of relevant documents retrieved in top-k |
| Precision@k | Fraction of top-k results that are relevant |
| Mean Reciprocal Rank (MRR) | Rank position of first relevant document |
| nDCG@k | Ranking quality with graded relevance |

### Generation Metrics

| Metric | What It Measures |
|---|---|
| Faithfulness | Claims in the response are supported by retrieved context |
| Answer relevance | Response addresses the query |
| Citation precision | Fraction of citations that correctly point to supporting content |
| Citation recall | Fraction of claims that are correctly cited |
| Abstention correctness | Model correctly refuses when context does not answer |
| Grounding rate | Fraction of response sentences that are grounded in context |

### RAG-Specific Edge Cases

- Query has no relevant documents in the corpus
- Query has multiple relevant documents with conflicting information
- Query requires combining information across documents
- Retrieved documents contain the answer but the model ignores them
- Retrieved documents are irrelevant but the model tries to answer anyway

### Measuring Grounding

```python
def measure_grounding(
    response: str,
    retrieved_chunks: list[str],
) -> dict:
    """Measure what fraction of response claims are supported by retrieved chunks."""
    claims = extract_claims(response)
    supported = 0
    for claim in claims:
        if any(claim_supported_by_chunk(claim, chunk) for chunk in retrieved_chunks):
            supported += 1
    return {
        "total_claims": len(claims),
        "supported_claims": supported,
        "grounding_rate": supported / len(claims) if claims else 1.0,
    }
```

## Structured-Output Evaluation

For systems that produce structured data (JSON, tool calls), evaluate structural correctness separately from semantic correctness.

### Structural Metrics

- **JSON validity**: passes JSON.parse without error
- **Schema validity**: matches the expected schema (Pydantic, Zod, JSON Schema)
- **Field completeness**: all required fields present
- **Type correctness**: each field has the expected type
- **Enum validity**: enum fields use allowed values
- **Extra field detection**: no unexpected fields (when extra="forbid")

### Semantic Metrics for Structured Output

- **Field accuracy**: each field matches the expected value
- **Null handling**: null vs. missing vs. empty string handled correctly
- **Nested structure validity**: nested objects and arrays match expected format
- **Cross-field consistency**: related fields are consistent (e.g., start_date < end_date)

### Evaluation Pipeline

```python
def evaluate_structured_output(
    response: str,
    schema: type[BaseModel],
    expected: dict | None = None,
) -> StructuredEvalResult:
    # Step 1: Check JSON validity
    try:
        parsed = json.loads(response)
    except json.JSONDecodeError:
        return StructuredEvalResult(json_valid=False)

    # Step 2: Check schema validity
    try:
        validated = schema.model_validate(parsed)
    except ValidationError:
        return StructuredEvalResult(json_valid=True, schema_valid=False)

    # Step 3: Check field accuracy (if expected is provided)
    if expected:
        field_accuracy = compare_fields(validated.model_dump(), expected)
    else:
        field_accuracy = {}

    return StructuredEvalResult(
        json_valid=True,
        schema_valid=True,
        field_accuracy=field_accuracy,
    )
```

## Drift Monitoring

Monitor evaluation metrics in production to detect degradation before it affects users.

### What to Monitor

- **Metric drift**: faithfulness, relevance, safety scores decline over time
- **Distribution drift**: input distribution shifts from the test set
- **Model drift**: the generation model's behavior changes (update, fallback)
- **Retrieval drift**: document collection changes affect retrieval quality
- **Latency drift**: response time increases over time
- **Cost drift**: cost per request increases

### Monitoring Frequency

| Signal | Frequency | Action on Drift |
|---|---|---|
| Online metrics | Per-request | Alert if threshold exceeded |
| Daily aggregates | Daily | Investigate if 5% degradation sustained |
| Weekly evaluation | Weekly | Run full evaluation on golden set |
| Monthly deep dive | Monthly | Human evaluation, failure analysis |
| Per-deployment | Every change | Run regression + golden set before deploy |

### Detection Methods

- Compare rolling window metrics to baseline (e.g., 7-day window vs. 30-day baseline).
- Use statistical tests (Mann-Whitney U, two-sample t-test) to detect distribution shifts.
- Set alert thresholds with headroom (e.g., alert at 5% degradation, critical at 10%).
- Monitor p50 and p95 separately — p95 degradation signals tail issues.
- Track abstention rate — a sudden increase may indicate retrieval problems.

## Failure Buckets

Classify failures into categories to identify systemic issues rather than chasing individual errors.

### Common Failure Buckets

| Bucket | Description | Example |
|---|---|---|
| Hallucination | Model generates unsupported claims | "The sky is green" (not in context) |
| Omission | Model misses information present in context | Fails to mention a key detail |
| Misinterpretation | Model misunderstands the query or context | Answers the wrong question |
| Format violation | Output does not match expected format | Invalid JSON, wrong structure |
| Refusal error | Model incorrectly refuses or fails to refuse | Answers when it should abstain |
| Irrelevance | Output is not relevant to the query | Provides unrelated information |
| Safety violation | Output contains harmful content | PII leakage, toxic language |
| Citation error | Citation is incorrect or hallucinated | Cites a non-existent source |
| Latency failure | Response exceeds latency budget | Times out |
| Extraction failure | Structured extraction fails | Missing fields, wrong types |

### Failure Analysis Workflow

1. Collect all failures from a evaluation run or production period.
2. Classify each failure into a bucket.
3. Count failures per bucket.
4. Prioritize buckets by frequency and severity.
5. Investigate root causes for the top buckets.
6. Implement fixes targeting the root cause.
7. Add regression tests for each failure.
8. Re-evaluate to confirm the fix reduced failures in the target bucket.

## Statistical Comparison

When comparing two systems (model A vs. model B, prompt v1 vs. prompt v2), use statistical methods to determine whether the difference is significant.

### Comparison Methods

| Method | When to Use | What It Tests |
|---|---|---|
| Paired t-test | Paired samples, continuous metric | Mean difference is non-zero |
| Wilcoxon signed-rank | Paired samples, ordinal or non-normal | Median difference is non-zero |
| McNemar's test | Paired samples, binary metric | Proportion difference is non-zero |
| Bootstrap | Any paired metric, no distribution assumption | Difference is non-zero |
| Mann-Whitney U | Unpaired samples | Distributions differ |

### Confidence Intervals

Report confidence intervals alongside point estimates:

```python
def bootstrap_ci(
    scores_a: list[float],
    scores_b: list[float],
    metric: Callable,
    n_bootstrap: int = 10000,
    ci_level: float = 0.95,
) -> tuple[float, float, float]:
    """Compute bootstrap confidence interval for the difference of a metric."""
    diffs = []
    for _ in range(n_bootstrap):
        sample_a = np.random.choice(scores_a, len(scores_a), replace=True)
        sample_b = np.random.choice(scores_b, len(scores_b), replace=True)
        diffs.append(metric(sample_b) - metric(sample_a))

    lower = np.percentile(diffs, (1 - ci_level) / 2 * 100)
    upper = np.percentile(diffs, (1 + ci_level) / 2 * 100)
    return np.mean(diffs), lower, upper
```

### Practical Significance

Statistical significance does not imply practical significance. With enough data, tiny differences become statistically significant. Consider:

- Is the effect size large enough to matter for users?
- Does the improvement justify the cost (latency, complexity, compute)?
- Is the improvement consistent across subpopulations?
- Would users notice the difference?

### Minimum Detectable Effect

Before running a comparison, determine the minimum effect size you can detect given your test set size:

```python
def min_detectable_effect(
    n_examples: int,
    alpha: float = 0.05,
    power: float = 0.8,
    base_rate: float = 0.5,
) -> float:
    """Estimate the minimum detectable effect size for a binary metric."""
    z_alpha = 1.96  # for alpha=0.05
    z_beta = 0.84   # for power=0.8
    return (z_alpha + z_beta) * np.sqrt(base_rate * (1 - base_rate) / n_examples)
```

## CI Evaluation Gates

Integrate evaluation into CI to catch regressions automatically.

### Gate Levels

| Gate | When | What | Blocking? |
|---|---|---|---|
| Lint | Every commit | Format, type check, test structure | Yes |
| Unit | Every commit | Component-level tests | Yes |
| Regression | Every PR | Regression tests from past failures | Yes |
| Golden set | Every PR | Full evaluation on golden test set | Yes (threshold) |
| Human eval | Major releases | Human evaluation on subset | Recommended |
| Safety audit | Before deploy | Safety-specific evaluation | Yes |

### Golden Set Gate Configuration

```yaml
# ci-evaluation-gates.yml
evaluation:
  golden_set:
    path: tests/golden_set_v2.json
    thresholds:
      faithfulness: 0.85
      answer_relevance: 0.80
      json_validity: 0.95
      safety_violation_rate: 0.01
    comparison: against_baseline
    fail_on_regression: true
    fail_on_below_threshold: true
```

### Baseline Management

- Store the baseline scores for the current production system.
- On each candidate change, run the full evaluation and compare to baseline.
- Fail the gate if any metric degrades beyond a tolerance (e.g., -0.02).
- Update the baseline when a change is deployed to production.
- Store baseline history to track trends over time.

```python
def evaluate_gate(
    candidate_scores: dict[str, float],
    baseline_scores: dict[str, float],
    thresholds: dict[str, float],
    tolerance: float = 0.02,
) -> GateResult:
    failures = []
    for metric, candidate in candidate_scores.items():
        # Check absolute threshold
        if candidate < thresholds.get(metric, 0):
            failures.append(f"{metric}: {candidate:.3f} below threshold {thresholds[metric]:.3f}")

        # Check regression from baseline
        baseline = baseline_scores.get(metric)
        if baseline is not None and candidate < baseline - tolerance:
            failures.append(f"{metric}: {candidate:.3f} regressed from baseline {baseline:.3f}")

    return GateResult(passed=len(failures) == 0, failures=failures)
```

## Cost-Aware Evaluation

Evaluation has a cost in compute, API calls, and human time. Design evaluation to maximize signal per unit cost.

### Cost Sources

| Source | Cost Driver | Optimization |
|---|---|---|
| LLM-as-judge | API calls per example | Judge on a sample, not full set |
| Human evaluation | Rater hours | Use for calibration, not routine |
| Embedding evaluation | Embedding compute | Cache embeddings |
| Retrieval evaluation | Vector store queries | Sample queries for evaluation |
| Golden set updates | Authoring time | Batch updates, review in groups |

### Cost Optimization Strategies

- Run the full golden set only on PRs that change prompts, retrieval, or the model.
- Run a reduced sample (100-200 examples) on every PR, full set before deploy.
- Use cheaper or smaller judge models for routine evaluation.
- Cache evaluation results — re-run only what changed.
- Prioritize high-impact metrics (safety, faithfulness) over low-impact ones (length, formatting).
- Batch human evaluation sessions rather than distributing them ad hoc.

### Cost Tracking

```python
class EvaluationCost:
    api_calls: int
    input_tokens: int
    output_tokens: int
    human_hours: float

    @property
    def estimated_cost(self) -> float:
        api_cost = self.input_tokens * INPUT_TOKEN_PRICE + self.output_tokens * OUTPUT_TOKEN_PRICE
        human_cost = self.human_hours * HUMAN_RATE
        return api_cost + human_cost
```

## Avoiding Benchmark Overfitting

Benchmark overfitting occurs when a system is tuned to perform well on a specific test set without generalizing to real-world inputs.

### Signs of Overfitting

- Scores are high on the golden set but low on production samples.
- Small prompt changes cause large score swings.
- The system performs well on old examples but poorly on new ones.
- The system exploits rubric artifacts (e.g., verbose responses score higher).
- High variance across random splits of the test set.

### Prevention

- Keep a held-out test set that is never used for tuning.
- Rotate examples in the golden set — retire old ones, add new ones.
- Use multiple test sets from different distributions.
- Measure on production samples, not only curated sets.
- Prefer simple metrics that are hard to game.
- Do not tune on evaluation metrics directly — tune on proxy metrics and verify on evaluation.
- Cross-validate across different time periods to detect temporal overfitting.

### Benchmark Score Claims

Do not overclaim benchmark scores. Always report:

- The exact test set version and composition
- Confidence intervals or standard error
- The number of examples
- Any filtering or preprocessing applied
- The evaluation method (LLM-as-judge, human, automatic)
- Inter-rater reliability (for human or LLM-judge evaluation)
- Known limitations of the metrics

## Required Review Output

When reviewing an AI evaluation pipeline, produce this summary:

```text
Evaluation system:
[Name and purpose of the evaluated system.]

Evaluation goal:
[What decision or question the evaluation is designed to support.]

Test set:
[Number of examples, composition, version, source.]

Golden set:
[Size, version, last review date, edge case coverage.]

Metrics:
[List of primary and secondary metrics with definitions and current values.]

Evaluation method:
[Automatic, LLM-as-judge, human, or mixed.]

LLM-as-judge (if used):
[Judge model, prompt version, calibration kappa against human raters.]

Regression tests:
[Number, coverage areas, CI integration.]

Irregularity:
[Inter-rater reliability scores, agreement metrics.]

Recent trends:
[Metric changes over last 30/90 days, drift detected.]

Failure buckets:
[Top failure categories with frequency and severity.]

CI gates:
[Gate configuration, thresholds, baseline comparison method.]

Cost:
[Cost per evaluation run, cost per metric.]

Known limitations:
[Overfitting risk, gaps in test coverage, metric weaknesses.]

Recommendations:
[Prioritized improvements with expected impact on evaluation quality.]
```

## Completion Criteria

An AI evaluation workflow review is complete only when:

- the evaluation goal is documented and linked to a decision
- a labeled test set exists with versioned golden examples
- edge cases are explicitly covered and tracked
- regression tests exist for all known failure modes
- metrics are selected based on the task, not convention
- LLM-as-judge is calibrated against human judgments with measured agreement
- inter-rater reliability is measured and meets thresholds
- retrieval and generation are evaluated separately (RAG systems)
- structured output includes structural and semantic metrics
- drift monitoring is implemented for key metrics
- failures are classified into buckets with root cause analysis
- statistical methods are used for comparisons with confidence intervals
- CI gates block regressions below defined thresholds
- evaluation cost is measured and optimized
- benchmark overfitting risks are documented and mitigated
- known limitations of every metric are documented
