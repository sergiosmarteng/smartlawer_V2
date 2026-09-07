---
name: structured-output-reliability
description: Design, review and debug reliable structured outputs from LLMs, including JSON schemas, validation, retries, repair strategies, contracts and downstream safety.
license: MIT
compatibility: opencode
metadata:
  category: ai-engineering
  stack: llm-structured-output
  version: "1.0.0"
orchestration:
  lead_for:
    - structured-output
  support_for: []
  conflicts_with:
    - prompt-engineering
---

# Structured Output Reliability

Use this skill when building systems that require LLMs to produce structured data — JSON, typed objects, or formatted responses — that must be parsed, validated, and consumed safely by downstream code.

The objective is to design structured-output pipelines that are robust against malformed, missing, hallucinated, or unsafe model output without trusting the LLM as a source of correct or safe data.

## When to Use This Skill

Load this skill when the task involves any of the following:

* extracting JSON from an LLM response
* validating LLM output against a schema
* building a retry loop for failed parsing
* repairing malformed JSON with a follow-up prompt
* consuming partial or streaming JSON output
* defining a schema contract between an LLM and application code
* testing boundary conditions for structured output
* reviewing a system that consumes LLM-generated data

Do not load this skill for:
* free-text generation with no structured output requirement
* traditional API validation where the data source is trusted
* prompt design that does not involve parsing model output

## Structured Output Principles

### Schema-First Design

Define the expected structure before making any LLM call. The schema is a contract between the system and the model. It defines:

* required fields and their types
* optional fields with defaults
* allowed enum values
* nesting and array constraints
* string format patterns (email, UUID, date, URL)

The schema must be validated independently of the LLM. A well-defined schema serves as both the prompt instruction and the runtime validator.

### Model Output Is Untrusted

Never treat LLM output as validated data. Even with strict prompting, the model may:

* emit invalid JSON
* omit required fields
* add hallucinated fields
* use incorrect enum values
* return strings where numbers are expected
* produce deeply nested output that exceeds recursion limits
* include explanatory text outside the JSON block

Every structured output pipeline must validate before use.

### Provider Differences

No provider guarantees perfectly valid structured output every time. Differences include:

* JSON mode adherence varies across models and providers
* some providers support constrained decoding or grammar; most do not
* temperature, top-p, and repetition penalty affect structure reliability
* longer outputs are more likely to contain structural errors
* function-calling or tool-use APIs may return malformed arguments
* streaming JSON may produce partial or multi-chunk tokens that break naive parsers

Account for these differences in retry and repair strategy.

## Backend Validation

### Pydantic (Python)

Use Pydantic models as the single source of truth for the schema. The same model should define the prompt instructions and the runtime validator.

```python
from pydantic import BaseModel, Field
from enum import Enum

class AssignmentStatus(str, Enum):
    pending = "pending"
    submitted = "submitted"
    graded = "graded"

class AssignmentOutput(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    status: AssignmentStatus
    score: int | None = Field(None, ge=0, le=100)
    feedback: str = Field(default="")
```

After parsing, validate with the model:

```python
try:
    parsed = AssignmentOutput.model_validate_json(raw_json)
except ValidationError as exc:
    # handle malformed output
```

Never use `eval()` or `json.loads()` without prior schema validation.

### JSON Schema (Cross-Language)

For polyglot systems, define a JSON Schema that both the prompt and validators reference:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": ["title", "status"],
  "properties": {
    "title": {"type": "string", "minLength": 1, "maxLength": 200},
    "status": {"type": "string", "enum": ["pending", "submitted", "graded"]},
    "score": {"type": "integer", "minimum": 0, "maximum": 100},
    "feedback": {"type": "string"}
  }
}
```

Validate with available schema validators rather than ad-hoc checks.

## Frontend Validation

### Zod (TypeScript)

For frontend code receiving structured LLM output via an API, validate at the boundary:

```typescript
import { z } from "zod";

const AssignmentSchema = z.object({
  title: z.string().min(1).max(200),
  status: z.enum(["pending", "submitted", "graded"]),
  score: z.number().int().min(0).max(100).nullable().optional(),
  feedback: z.string().default(""),
});

const result = AssignmentSchema.safeParse(unknownData);
if (!result.success) {
  // handle validation failure
}
```

Validate at the API boundary, not deep inside component logic. Never trust data that arrives without schema validation.

### Nullable vs Optional

Distinguish between:

* `null` — the value is absent because it was explicitly set to nothing
* `undefined` / missing — the field was not provided
* empty string — the value was provided but is empty

Map these correctly between the backend schema, the frontend schema, and the database.

```python
# Pydantic: nullable, not required
score: int | None = None

# Zod: nullable and optional
score: z.number().nullable().optional()
```

A field that is `optional` in the schema but `required` in business logic should still fail validation if missing.

## Retry and Repair Strategy

### Retry Policies

Retry only when the failure could be transient. Structural errors from an LLM are not transient in the traditional sense — they indicate the model did not follow instructions. Retries should:

* include the parsing error in the retry prompt to guide correction
* preserve the original instruction
* cap at a small number (2-3 attempts)
* use a different temperature or model variant if available
* log each attempt for debugging

```python
MAX_RETRIES = 3
for attempt in range(MAX_RETRIES):
    raw = llm.instruct(prompt)
    try:
        return MyModel.model_validate_json(raw)
    except ValidationError as exc:
        prompt = repair_prompt(prompt, raw, exc)
raise MaxRetriesExceededError("Structured output failed after retries")
```

### Repair Prompts

When validation fails, construct a repair prompt that:

* shows the original instruction
* shows the invalid output
* describes exactly what failed (missing field, wrong type, bad enum)
* asks for corrected output only

Do not include the full conversation history in the repair prompt. Keep it focused on the structural error.

### Partial Output Handling

When receiving streaming JSON, the model may emit valid JSON prefixes before completion. Approaches:

* buffer the full response and validate at the end
* use incremental JSON parsing with a library that handles partial tokens
* display a loading state until the full response is validated
* never partially commit data from a stream before full validation

Partial output should never reach business logic.

### Invalid JSON Handling

When the model emits invalid JSON:

1. attempt to locate the JSON block within the response (between triple backticks or similar markers)
2. try lenient JSON parsing with `json.loads()` after stripping surrounding text
3. if that fails, use a repair prompt
4. if repair fails, return a fallback or error

Never silently ignore invalid JSON. Never pass unparsed model output downstream.

## Security Risks

### Unsafe `eval`

Never use `eval()`, `exec()`, or `Function()` to parse or process model output. An LLM can generate arbitrary code disguised as structured data.

```python
# NEVER DO THIS
data = eval(llm_response)  # arbitrary code execution
```

```typescript
// NEVER DO THIS
const data = eval("(" + llmResponse + ")");  // arbitrary code execution
```

### Direct Execution of Model Output

Never feed model output directly into:

* `subprocess.run()` or `os.system()`
* SQL query interpolation
* HTML rendering without sanitization
* file system writes without path validation
* `yaml.load()` without safe loader
* `pickle.loads()` or `marshal.loads()`

Treat model output as untrusted user input at every boundary.

### Hallucinated Fields

Models may include fields that were not in the schema. Code must:

* reject unknown fields during validation (Pydantic `extra="forbid"`)
* never trust a field just because it appears in the output
* log unexpected fields for analysis but not as trusted data

```python
class SafeModel(BaseModel):
    model_config = {"extra": "forbid"}
    title: str
```

### Logging Without Leaking Sensitive Prompt Data

Logs must not contain:

* the full system prompt
* user-specific data included in prompts
* API keys or model provider credentials
* internal instructions used to guide the model

Log only:

* the schema name and version
* validation error codes and field paths
* retry count
* final success or failure
* anonymized field lengths, not field values

## Testing Strategy

### Tests for Malformed Output

Test every way the output can be invalid:

| Scenario | Example |
|----------|---------|
| Completely invalid JSON | `{broken` |
| Missing required field | `{"title": "ok"}` (missing `status`) |
| Wrong type | `{"title": 123, "status": "pending"}` |
| Invalid enum | `{"title": "x", "status": "invalid-status"}` |
| Extra unknown fields | `{"title": "x", "status": "pending", "hacked": true}` |
| Empty string in required field | `{"title": "", "status": "pending"}` |
| Null in non-nullable field | `{"title": null, "status": "pending"}` |
| Deeply nested overflow | 100 levels of nesting |
| Non-JSON text | `Here is the JSON: { ... }` with extra text |

### Golden Test Cases

Maintain a set of golden test cases that represent:

* the ideal valid output
* each invalid variant listed above
* edge cases for every enum value
* boundary values (empty arrays, zero, max length)
* provider-specific quirks observed in production

Run golden tests in CI whenever the schema changes.

### Deterministic Parsing

Parsing must be deterministic. For the same input, the parser must always produce the same result or the same error.

* avoid random fallback selection
* avoid time-based or state-dependent parsing decisions
* use a fixed seed for any randomness in test fixtures

### Failure Fallback

Define what happens when structured output cannot be parsed after all retries:

* return an HTTP 422 or 500 with a structured error
* return a default value when safe to do so
* return a partial result only if the partial data is independently valid
* never silently return empty, null, or incomplete data

## Review Checklist

When reviewing structured-output code, check every item:

- [ ] Is the schema defined independently of the LLM call?
- [ ] Is the model output validated at the boundary with a library (Pydantic, Zod, JSON Schema)?
- [ ] Are unknown fields rejected (`extra="forbid"`)?
- [ ] Is there a retry loop with a maximum attempt limit?
- [ ] Does the retry prompt include the parsing error?
- [ ] Are repair prompts scoped to only the failed output?
- [ ] Is `eval()` or `exec()` never used?
- [ ] Is model output never passed to `subprocess`, SQL, or filesystem without validation?
- [ ] Is streaming output fully buffered before validation?
- [ ] Are logged values free of sensitive prompt data?
- [ ] Are there tests for every invalid-output scenario?
- [ ] Are golden test cases maintained and run in CI?
- [ ] Is there a defined fallback for unrecoverable parse failures?
- [ ] Are nullable and optional fields handled correctly at every layer?
- [ ] Is the schema versioned for backward-compatible changes?
- [ ] Are provider differences accounted for in retry and timeout configuration?

## Required Output Format

When designing or reviewing a structured-output pipeline, produce this summary:

```text
Schema:
[Schema name, version, and definition location.]

Validation approach:
[Library used, strictness level, extra-field handling.]

Retry policy:
[Max attempts, repair prompt strategy, temperature or model changes.]

Fallback:
[What happens when all retries fail.]

Provider considerations:
[Known quirks or differences for the specific provider/model.]

Security:
[Verified that eval/exec is absent, model output is not executed or rendered unsafely.]

Testing:
[Golden tests exist, invalid-output scenarios covered, CI integration.]

Logging:
[Prompt data is not logged, only validation metadata.]
```

## Completion Criteria

Structured-output reliability work is complete only when:

* the schema is versioned and backward-compatible
* validation rejects any output that does not match the schema
* `eval()` and unsafe parsing are absent from the codebase
* model output is never executed, interpolated into SQL, or rendered unsafely
* retries are bounded and include parsing-error context
* repair prompts are focused on the structural failure
* streaming output is validated after buffering
* every invalid-output scenario has a test
* golden test cases exist and pass
* provider differences are documented and handled
* partial or unrecoverable failures have a defined fallback
* logging excludes sensitive prompt data
