---
name: prompt-engineering
description: Design, test, and optimize prompts for LLMs, including system prompts, few-shot, chain-of-thought, template management, technique selection, and prompt versioning.
license: MIT
compatibility: opencode
metadata:
  category: ai-engineering
  stack: prompt-engineering
  version: "1.0.0"
orchestration:
  lead_for:
    - prompt-engineering
  support_for:
    - structured-output
  conflicts_with:
    - structured-output-reliability
---

# Prompt Engineering

Use this skill when designing, testing, or optimizing prompts for LLM applications — including system prompt design, few-shot examples, chain-of-thought reasoning, prompt templates, technique selection, and prompt versioning.

The objective is to craft prompts that produce consistent, correct, and well-structured LLM output while minimizing token waste, latency, and iteration cost.

This skill covers prompt design and optimization. It does not cover prompt injection defense — use `prompt-injection-defense` for security. It does not cover structured output parsing or validation — use `structured-output-reliability` for that.

## When to Use This Skill

Load this skill when the task involves any of the following:

- writing or refining a system prompt for an LLM application
- selecting a prompting technique (few-shot, CoT, role, persona, structured output)
- designing few-shot examples for consistent output
- managing prompt templates across environments (dev, staging, production)
- testing and comparing prompt variants
- optimizing prompts for token efficiency, latency, or quality
- versioning prompts and tracking changes
- debugging poor LLM output caused by prompt quality (not security or infrastructure)
- designing prompts for multi-step or agentic workflows

Do not load this skill for:

- prompt injection defense or security hardening (use prompt-injection-defense skill)
- structured output parsing and validation (use structured-output-reliability skill)
- general LLM application security (use llm-app-security skill)
- model serving or infrastructure (use model-serving-production skill)
- offline evaluation methodology or test sets (use ai-evaluation skill)

## Prompt Anatomy

### Core Components

Every prompt consists of some or all of these components, ordered by decreasing priority:

| Component | Purpose | Example |
|-----------|---------|---------|
| **System instruction** | Defines the model's role, constraints, and behavior | "You are a senior code reviewer." |
| **Context** | Background information the model needs | "The codebase uses FastAPI and SQLAlchemy." |
| **Task description** | What the model should do | "Review the following pull request for bugs." |
| **Output format** | How the response should be structured | "Return a JSON object with fields: severity, file, recommendation." |
| **Constraints** | Boundaries on the response | "Do not suggest adding new dependencies." |
| **Few-shot examples** | Input-output pairs demonstrating desired behavior | "Input: ... Output: ..." |
| **User input** | The specific request or data to process | "```python\nprint('hello')\n```" |

### Context Window Budget

Plan token allocation within the model's context window:

```text
Total context window:             8,000  (for gpt-4o-mini)
├── System prompt:               ~1,000  (role, constraints, format)
├── Few-shot examples:           ~1,500  (2-3 examples)
├── Retrieved context (RAG):     ~3,000  (relevant documents)
├── Conversation history:        ~1,500  (recent turns)
├── User input:                    ~500  (current request)
├── Buffer for response:         ~1,000  (generated output)
└── Remaining headroom:          ~1,500  (safety margin)
```

Leave 10-20% headroom. Prompts that fill the entire context window degrade output quality and increase latency.

## Technique Selection

### Prompting Techniques Comparison

| Technique | Best For | Token Cost | When to Use |
|-----------|----------|------------|-------------|
| **Zero-shot** | Simple, well-defined tasks | Low | The model already knows what to do |
| **Few-shot** | Format control, style mimicry | Medium | Model produces inconsistent output without examples |
| **Chain-of-thought (CoT)** | Reasoning, math, multi-step logic | Medium | Task requires step-by-step reasoning |
| **Role prompting** | Tone, perspective, domain expertise | Low | Output needs a specific voice or authority level |
| **Persona prompting** | Consistent character or viewpoint | Low | Brand voice, customer-facing chat, creative writing |
| **Structured output** | JSON, typed data, tool calls | Low | Machine-consumable output required |
| **Step-back prompting** | Abstract reasoning before specific answer | Medium | Task requires understanding the principles before the specifics |
| **Tree-of-thought** | Complex exploration with branching | High | Open-ended problems, creative brainstorming |
| **Self-consistency** | High-stakes reasoning tasks | High* | Need confidence estimate; multiple CoT runs sampled |
| **Generated knowledge** | Factual accuracy, domain tasks | Medium | Model lacks domain context; generate knowledge first |

\* Self-consistency runs N parallel CoT chains and votes on the answer. Cost scales linearly with N.

### Decision Flow

```
Is the model likely to know what to do without examples?
├── Yes → Zero-shot
|   ├── Does output format matter? → Add format instruction
|   └── No format needed → Done
└── No → Few-shot
    ├── Does the task require reasoning?
    |   ├── Yes → Chain-of-thought
    |   |   ├── Is correctness critical? → Self-consistency
    |   |   └── Correctness less critical → Simple CoT
    |   └── No → Standard few-shot
    ├── Does tone or voice matter?
    |   ├── Yes → Role or persona prompting
    |   └── No → Standard instruction
    └── Does output need to be machine-readable?
        └── Yes → Structured output format
```

### Technique Limitations

| Technique | Common Failure Mode | Mitigation |
|-----------|-------------------|------------|
| Zero-shot | Inconsistent output across calls | Add minimal format constraints |
| Few-shot | Model copies example patterns too rigidly | Vary examples; add variation instructions |
| Chain-of-thought | Model can reason correctly to wrong answer | Add verification step: "Double-check your reasoning" |
| Role prompting | Model over-commits to role | Balance role with task constraints |
| Structured output | Model adds commentary outside the structure | Explicitly forbid extra text |

## System Prompt Design

### Principles

1. **Be specific, not verbose.** More words do not mean better instructions. Every sentence should add precision.
2. **State what to do, not what not to do.** "Output only the JSON object" works better than "Do not output anything except the JSON object."
3. **Put the most important instruction first.** Models pay more attention to early content.
4. **Use consistent terminology.** Do not use "task", "job", and "assignment" interchangeably in the same prompt.
5. **Test with the weakest model.** If it works on the cheapest/fastest model, it will work better on expensive ones.

### System Prompt Template

```text
You are a [role]. You specialize in [domain].

## Your Task
[clear, specific description of what the model should do]

## Constraints
- [constraint 1]
- [constraint 2]
- [constraint 3]

## Output Format
[exact format specification]

## Examples
[2-3 few-shot examples if needed]

## Context
[background information the model needs]
```

### System Prompt Anti-Patterns

| Anti-Pattern | Problem | Fix |
|---|---|---|
| "You are an AI assistant" | Generic, no guidance | Be specific: "You are a customer support agent for Acme Corp." |
| Multiple conflicting instructions | Model cannot satisfy both | Prioritize: "Safety is more important than completeness." |
| Overly long constraints list | Model ignores or forgets | Group related constraints; limit to 5-7 |
| Vague quality instructions | Not testable | "Responses must cite line numbers" vs. "Be thorough" |
| Instructions buried in middle | Model skips or deprioritizes | Put critical instructions at the start |

## Few-Shot Example Design

### Example Quality Criteria

Every few-shot example must be:

1. **Correct** — the expected output is accurate
2. **Consistent** — follows the same format as all other examples
3. **Representative** — reflects the distribution of real inputs
4. **Distinct** — covers different patterns, not minor variations of the same case
5. **Balanced** — edge cases and common cases both represented

### Example Selection

| Example Type | Purpose | Count |
|-------------|---------|-------|
| Standard case | Shows normal expected behavior | 1-2 |
| Edge case | Shows handling of unusual input | 1 |
| Negative example | Shows what not to do (optional) | 0-1 |

### Few-Shot Template

```text
Input: [example input 1]
Output: [example output 1]

Input: [example input 2]
Output: [example output 2]

Input: {user_input}
Output:
```

Leave the final "Output:" line incomplete so the model continues from there.

### Common Few-Shot Mistakes

- **Too many examples** — context window fills; quality degrades after 5-10 examples
- **Examples too similar** — model memorizes the pattern instead of learning the rule
- **Wrong ordering** — model pays more attention to early and late examples (primacy/recency effects)
- **Examples with errors** — model reproduces the errors in its output
- **Examples that contradict the system prompt** — model follows examples over instructions

## Chain-of-Thought Prompting

### Simple CoT

Append "Let's think step by step" or equivalent to the prompt:

```text
Question: {question}
Let's think step by step, then provide the final answer.
```

### Structured CoT

Provide a reasoning template:

```text
Question: {question}

Reasoning:
1. First, identify what the question is asking.
2. Break down the problem into components.
3. Work through each component.
4. Combine the results.

Final answer:
```

### CoT with Verification

```text
Question: {question}

Step 1: Restate the question in your own words.
Step 2: Break down the information given.
Step 3: Work through the reasoning.
Step 4: State your conclusion.
Step 5: Verify your conclusion against the question. Does it fully answer what was asked?
Step 6: Provide the final answer.
```

### When CoT Hurts

- Tasks where the model is already highly accurate without reasoning
- Tasks where reasoning steps are obvious and add no value
- Very simple factual lookups (a date, a name, a definition)
- Tasks where step-by-step reasoning leads to overthinking

## Prompt Templates

### Template Management

Store prompts as versioned files, not string literals in code:

```python
from string import Template
import yaml

class PromptManager:
    def __init__(self, prompts_dir: str = "prompts"):
        self.prompts: dict[str, str] = {}
        self._load_prompts(prompts_dir)

    def _load_prompts(self, directory: str):
        for path in Path(directory).glob("*.prompt"):
            self.prompts[path.stem] = path.read_text()

    def render(self, name: str, **kwargs) -> str:
        template = self.prompts.get(name)
        if not template:
            raise ValueError(f"Unknown prompt: {name}")
        return Template(template).safe_substitute(**kwargs)
```

### Template Variables

```text
# review-code.prompt
You are a senior {{ language }} developer reviewing code.

## Code to Review
```{{ language }}
{{ code }}
```

## Review Focus
- {{ focus_areas }}

## Instructions
{{ instructions }}
```

### Prompt File Organization

```text
prompts/
├── production/           # Tested, approved prompts
│   ├── chat-system.prompt
│   ├── summarization.prompt
│   └── code-review.prompt
├── staging/              # Pending approval
│   └── chat-system-v2.prompt
├── experiments/          # Active iterations
│   ├── chat-system-v3a.prompt
│   └── chat-system-v3b.prompt
└── archived/             # Previous versions
    └── chat-system-v1.prompt
```

### Variable Injection Safety

When injecting user data into prompt templates, escape or sanitize to prevent unintended behavior:

```python
def safe_substitute(template: str, variables: dict) -> str:
    """Replace variables while escaping unsafe content."""
    for key, value in variables.items():
        if isinstance(value, str):
            # Wrap user-provided values in delimiters
            template = template.replace(
                f"{{{{ {key} }}}}",
                f"---BEGIN {key.upper()}---\n{value}\n---END {key.upper()}---"
            )
    return template
```

Note: See `prompt-injection-defense` skill for comprehensive security measures.

## Prompt Testing

### Testing Methodology

Test prompts systematically before deployment:

1. **Unit test** — does the prompt produce the expected output structure for known inputs?
2. **Edge case test** — does it handle empty input, very long input, unusual input?
3. **Regression test** — does a change break previously working behavior?
4. **A/B comparison** — which of two prompt variants performs better?
5. **Model comparison** — does the prompt work across different models?

### Prompt Test Runner

```python
class PromptTestRunner:
    def __init__(self, model: str = "gpt-4o-mini"):
        self.model = model
        self.results: list[PromptTestResult] = []

    def run_test(self, prompt: str, test_case: PromptTestCase) -> PromptTestResult:
        response = llm_client.completions.create(
            model=self.model,
            prompt=prompt.format(input=test_case.input),
            temperature=0,
        )
        passed = test_case.validator(response.text, test_case.expected)
        return PromptTestResult(
            test_name=test_case.name,
            passed=passed,
            input=test_case.input,
            output=response.text,
            expected=test_case.expected,
            latency_ms=response.usage.total_time,
        )

    def run_suite(self, prompt: str, suite: list[PromptTestCase]) -> TestSummary:
        for case in suite:
            self.results.append(self.run_test(prompt, case))
        passed = sum(1 for r in self.results if r.passed)
        return TestSummary(
            total=len(self.results),
            passed=passed,
            failed=len(self.results) - passed,
            pass_rate=passed / len(self.results),
        )
```

### Test Case Categories

| Category | Examples |
|----------|----------|
| Happy path | Typical input the prompt was designed for |
| Edge input | Empty string, very long text, special characters |
| Format variants | Markdown, JSON, code blocks, multiple languages |
| Ambiguity | Input that could be interpreted multiple ways |
| Off-topic | Input unrelated to the prompt's purpose |
| Boundary | Input at or near context window limits |

### Evaluating Prompt Quality

| Metric | What It Measures | How to Measure |
|--------|-----------------|----------------|
| Output consistency | Same input produces similar outputs | Run N times with temperature=0; measure variance |
| Format compliance | Output matches expected structure | Parse and validate (see structured-output-reliability) |
| Task accuracy | Output is correct for the task | Compare against golden answers |
| Token efficiency | Output is not unnecessarily verbose | Track output token count vs. expected |
| Latency | Time to first token and total time | Measure at model API level |
| Refusal rate | Model refuses to perform the task | Track "I cannot" / "I'm unable" patterns |

## Prompt Versioning

### Versioning Strategy

Every prompt change should be tracked like a code change:

1. **Semantic versioning** — major for structural changes, minor for refinements, patch for fixes
2. **Changelog** — document what changed and why
3. **A/B test results** — data supporting the new version
4. **Rollback plan** — how to revert if the new version regresses

### Prompt Version Metadata

Store metadata alongside the prompt file:

```yaml
# chat-system-v2.prompt.meta.yaml
version: "2.0.0"
created: 2026-07-09
author: "developer@example.com"
model: "gpt-4o-mini"
temperature: 0.3
changes:
  - "Added explicit output format instructions"
  - "Reduced system prompt from 1200 to 800 tokens"
  - "Replaced generic examples with domain-specific ones"
test_results:
  pass_rate: 0.94
  test_count: 50
  previous_pass_rate: 0.87
supersedes: "chat-system-v1.prompt"
```

### What to Version

- Full prompt text (not just diff — context matters)
- Model and parameters used during testing
- Test results (pass rate, test count)
- Known limitations or edge cases
- Dependencies (retrieval sources, tool definitions)

## Prompt Optimization

### Reducing Token Count

| Technique | Savings | Trade-off |
|-----------|---------|-----------|
| Remove redundant instructions | Medium | None |
| Shorten examples | Medium | May reduce output quality |
| Use abbreviations or codes | Low | May confuse the model |
| Move shared context to system prompt | High | Depends on architecture |
| Reduce few-shot examples | High | Quality may drop below minimum |
| Use shorter variable names | Low | Readability impact |

### Optimizing for Latency

- Shorter prompts = faster response (especially for input-bound models)
- Fewer output tokens = faster response
- Lower max_tokens = faster response
- Higher temperature may halt earlier (less "thinking")
- Streaming helps perceived latency but not total processing time

### Optimizing for Cost

```python
def choose_cheapest_model(task_difficulty: str) -> str:
    """Route simple tasks to cheaper models."""
    if task_difficulty == "simple":
        return "gpt-4o-mini"   # $0.15/$0.60 per 1M tokens
    elif task_difficulty == "medium":
        return "gpt-4o-mini"   # Still capable for most tasks
    else:
        return "gpt-4o"        # $2.50/$10.00 per 1M tokens
```

Note: See `ai-cost-optimization` skill for comprehensive cost strategy.

## Prompting for Multi-Step Workflows

### Step Separation

In multi-step pipelines, each step should have its own prompt rather than one combined prompt:

```
Prompt A: Extract key entities from the user's question
       ↓ extracted entities
Prompt B: Search the knowledge base for relevant documents
       ↓ search results
Prompt C: Generate answer using search results
       ↓ answer
Prompt D: Format answer according to output schema
```

### Context Passing Between Steps

Pass only the necessary information between steps, not the full output:

```python
def multi_step_pipeline(user_input: str) -> dict:
    step_a = llm.chat(
        prompt=EXTRACT_ENTITIES,
        user_input=user_input,
    )
    # Pass only the structured entities, not the raw response
    entities = parse_entities(step_a)

    step_b = search_knowledge_base(entities)
    # Pass only the relevant search results
    context = summarize_search_results(step_b)

    step_c = llm.chat(
        prompt=GENERATE_ANSWER,
        context=context,
        user_input=user_input,
    )
    return format_output(step_c)
```

### State Management

For agentic workflows, maintain a separate state object that grows across steps rather than appending to the prompt:

```python
class AgentState:
    def __init__(self):
        self.history: list[dict] = []
        self.current_step: str = ""
        self.intermediate_results: dict = {}

    def add_step(self, step_name: str, result: dict):
        self.history.append({"step": step_name, "result": result})
        self.intermediate_results[step_name] = result
        self.current_step = step_name

    def build_prompt_context(self, max_turns: int = 5) -> str:
        recent = self.history[-max_turns:]
        return "\n".join(
            f"Step {s['step']}: {json.dumps(s['result'])}"
            for s in recent
        )
```

## Anti-Patterns

| Anti-Pattern | Problem | Fix |
|---|---|---|
| Prompt as code comment | Prompt changes require code deployment | Externalize prompts to versioned files |
| Single prompt for all tasks | One prompt cannot optimize for multiple tasks | Create task-specific prompts |
| No prompt testing | Cannot measure improvement or regression | Add systematic prompt test suite |
| Over-fitting to one model | Prompt breaks on model update or provider switch | Test across 2+ models; document differences |
| Ignoring output length | Model writes essays for yes/no questions | Set explicit max_tokens and format constraints |
| Putting user input first | Model ignores system instructions after seeing user content | Always place system instructions before user input |
| Repeating instructions | Context waste without quality gain | Say it once, clearly |
| No fallback behavior | Model failure leaves user with error or silence | Define fallback response for edge cases |
| Temperature too high for structured output | Format compliance decreases | Use temperature=0 for structured output tasks |

## Testing a Prompt Engineering System

### Unit Tests

```python
def test_prompt_renders_all_variables():
    manager = PromptManager(prompts_dir="tests/fixtures/prompts")
    rendered = manager.render("test_prompt", language="Python", code="x = 1")
    assert "{{ language }}" not in rendered
    assert "{{ code }}" not in rendered
    assert "Python" in rendered

def test_prompt_with_empty_variable_does_not_crash():
    manager = PromptManager(prompts_dir="tests/fixtures/prompts")
    rendered = manager.render("test_prompt", language="", code="")
    assert rendered is not None

def test_unknown_prompt_raises_error():
    manager = PromptManager(prompts_dir="tests/fixtures/prompts")
    with pytest.raises(ValueError, match="Unknown prompt"):
        manager.render("nonexistent")
```

### Integration Tests

```python
@pytest.mark.slow
def test_prompt_produces_valid_output():
    runner = PromptTestRunner()
    prompt = "Summarize the following in one sentence: {input}"
    result = runner.run_test(prompt, PromptTestCase(
        name="short_summary",
        input="The quick brown fox jumps over the lazy dog.",
        validator=lambda output, _: len(output.split()) <= 20,
        expected=None,
    ))
    assert result.passed

def test_prompt_test_suite_counts():
    runner = PromptTestRunner()
    suite = [
        PromptTestCase(name="case1", input="a", validator=lambda o, e: True, expected=None),
        PromptTestCase(name="case2", input="b", validator=lambda o, e: False, expected=None),
    ]
    summary = runner.run_suite("Process: {input}", suite)
    assert summary.total == 2
    assert summary.passed == 1
    assert summary.failed == 1
    assert summary.pass_rate == 0.5
```

### Regression Tests

- [ ] Every prompt change includes a test run against the previous golden outputs
- [ ] Prompt regression is detected before deployment
- [ ] Test suite covers all supported models (if multi-model)
- [ ] Output format changes are detected (token count, structure, refusal patterns)

## Completion Criteria

Prompt engineering work is complete only when:

- [ ] the prompting technique is selected based on task requirements, not preference
- [ ] the system prompt defines role, task, constraints, and output format explicitly
- [ ] few-shot examples (if used) are correct, consistent, and representative
- [ ] prompts are stored in versioned files, not code string literals
- [ ] a test suite exists with happy path, edge case, and regression tests
- [ ] prompt quality metrics (consistency, format compliance, accuracy) are measured
- [ ] the prompt has been tested with at least one cheap/fast model
- [ ] context window budget is tracked and headroom is maintained
- [ ] user input is injected safely with delimiters
- [ ] a rollback plan exists for prompt regressions
- [ ] output length is constrained appropriately for the task
- [ ] temperature is set appropriately (0 for structured, higher for creative)

## Related Skills

- `prompt-injection-defense` — for hardening prompts against injection attacks
- `structured-output-reliability` — for parsing and validating structured LLM output
- `ai-evaluation` — for rigorous evaluation of LLM output quality
- `ai-cost-optimization` — for reducing token and model costs
- `rag-quality-review` — for RAG-specific prompt design with retrieval context
- `multi-agent-orchestration` — for prompt design in multi-agent workflows
