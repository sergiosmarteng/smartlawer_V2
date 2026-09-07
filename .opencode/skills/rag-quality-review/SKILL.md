---
name: rag-quality-review
description: Review and improve retrieval-augmented generation systems for chunking, retrieval quality, grounding, citation reliability, evaluation, latency and safety.
license: MIT
compatibility: opencode
metadata:
  category: ai-engineering
  stack: rag
  version: "1.0.0"
orchestration:
  lead_for:
    - rag-pipeline
  support_for: []
  conflicts_with:
    - ai-evaluation
---

# RAG Quality Review

Use this skill when reviewing, designing, debugging, or evaluating a retrieval-augmented generation (RAG) system.

The objective is to assess and improve every component of a RAG pipeline — ingestion, chunking, retrieval, generation, evaluation, security, and performance — so the system produces grounded, accurate, and safe responses.

## When to Use This Skill

Load this skill when the task involves any of the following:

- reviewing a RAG pipeline architecture
- debugging poor answer quality or hallucination in a RAG system
- designing a new RAG ingestion and retrieval pipeline
- evaluating chunking strategy, embedding choice, or search method
- implementing hybrid search or reranking
- setting up retrieval evaluation with metrics
- building golden test datasets for RAG quality
- deploying a RAG system to production
- auditing a RAG system for security and data leakage

Do not load this skill for:
- general LLM application security (use llm-app-security skill)
- structured output reliability (use structured-output-reliability skill)
- general database or search system design without LLM generation

## RAG Architecture Checklist

Assess every component of the RAG pipeline:

- [ ] Is the overall architecture documented with each component's responsibility?
- [ ] Is the ingestion pipeline separate from the query pipeline?
- [ ] Are documents preprocessed before chunking (cleaning, normalization, language detection)?
- [ ] Is the retrieval strategy appropriate for the data type (semantic, keyword, hybrid)?
- [ ] Are there multiple retrieval strategies available and evaluated, not just one hardcoded?
- [ ] Is there a reranking or fusion step between retrieval and generation?
- [ ] Is the context window of the generation model known and enforced?
- [ ] Are retrieved chunks pruned to fit within the model's context window?
- [ ] Is there a fallback when no relevant documents are retrieved?
- [ ] Is there an abstention mechanism when the model cannot answer from retrieved content?
- [ ] Are citations or source references included in the output?
- [ ] Is the system instrumented for monitoring retrieval quality, latency, and cost?
- [ ] Are there versioned pipelines so changes can be rolled back?
- [ ] Are there integration tests that exercise the full pipeline end to end?

### Architecture Anti-Patterns

| Anti-Pattern | Problem | Fix |
|---|---|---|
| Single-strategy retrieval | Misses relevant results that require different search methods | Implement hybrid search (semantic + keyword) |
| No pruning of retrieved chunks | Context window overflow, truncated generation | Prune to fit model context window; prioritize relevance |
| Retrieval as a black box | Cannot debug why bad documents are retrieved | Log query, top-k results, scores, and source metadata |
| Generation without citations | Users cannot verify model claims | Require source citations with every generation |
| No abstention fallback | Model hallucinates when no relevant context exists | Add a "no answer" response path |
| Increasing top_k to fix recall | Degrades precision, increases latency and context cost | Improve chunking, embedding, or reranking instead of raising top_k |

## Data Ingestion Checklist

### Document Processing

- [ ] Are documents cleaned before chunking (remove headers, footers, boilerplate, navigation elements)?
- [ ] Is the document format handled correctly (PDF, HTML, Markdown, plain text, DOCX)?
- [ ] Are images, tables, and figures handled (extracted, described, or skipped)?
- [ ] Is OCR applied to scanned documents when needed?
- [ ] Is the source URL or document identifier preserved for citation?
- [ ] Is the ingestion timestamp recorded for freshness tracking?
- [ ] Are duplicate documents detected and deduplicated?
- [ ] Are document-level permissions or access controls preserved?
- [ ] Is sensitive data detected and filtered during ingestion (PII, secrets, credentials)?

### Chunking Strategy

- [ ] Is the chunking strategy documented with rationale?
- [ ] Are multiple chunk sizes evaluated, not just one chosen arbitrarily?
- [ ] Is the chunk size appropriate for the embedding model's token limit?
- [ ] Do chunks overlap to avoid splitting semantic units across boundaries?
- [ ] Is the overlap size appropriate (typically 10-20% of chunk size)?
- [ ] Is chunking aware of document structure (paragraphs, sections, headings, lists)?
- [ ] Are code blocks, tables, and lists kept intact within chunks when possible?
- [ ] Is there a fallback strategy for documents that are shorter than the chunk size?
- [ ] Are chunks too small to carry standalone meaning?
- [ ] Are chunks too large to retrieve precisely (low precision at high chunk size)?

### Chunking Approaches

| Approach | Best For | Considerations |
|---|---|---|
| Fixed-size with overlap | Uniform documents, simplicity | May split semantic units |
| Recursive character splitting | General purpose, works across formats | May produce uneven chunks |
| Semantic chunking (paragraph/section) | Well-structured documents (wikis, manuals) | Requires structure detection |
| Sentence-based splitting | Dense factual content | May produce very small chunks |
| Token-aware splitting | When exact token limits matter | Requires tokenizer matching the retrieval model |
| Document-then-chunk (parent-child) | When both summary and detail are needed | Two-level retrieval; more complex |

### Metadata

- [ ] Does every chunk carry sufficient metadata for downstream use?
- [ ] Required metadata: document ID, source URL or path, chunk index, document title
- [ ] Recommended metadata: ingestion timestamp, document type, author, section heading, page number
- [ ] Is metadata stored alongside the embedding for filtering?
- [ ] Are metadata fields indexed for fast filtering (date range, source type, tenant)?
- [ ] Is sensitive metadata excluded from what the generation model sees?
- [ ] Are metadata fields validated during ingestion?

### Embedding

- [ ] Is the embedding model documented with version and provider?
- [ ] Is the embedding dimension appropriate for the vector store index?
- [ ] Are embeddings updated when the model changes (re-embedding strategy)?
- [ ] Is the embedding compared against alternatives on the actual data?
- [ ] Are there multiple embedding strategies for different document types if needed?
- [ ] Is embedding cost and latency measured?
- [ ] Are embeddings cached to avoid recomputation during reindexing?

## Retrieval Checklist

### Search Methods

- [ ] Is the search method appropriate for the data type?

  | Data Type | Recommended Search |
  |---|---|
  | Conversational or semantic queries | Dense embedding (semantic search) |
  | Exact keyword or ID lookup | BM25 or traditional keyword search |
  | Factual, named-entity-heavy queries | Hybrid (semantic + BM25) |
  | Code, identifiers, technical terms | BM25 or sparse embedding |
  | Multi-lingual content | Multilingual embedding model |

- [ ] Is the retrieval method evaluated against the actual query distribution, not synthetic queries alone?
- [ ] Are retrieval parameters (top_k, similarity threshold) tuned on a validation set?
- [ ] Is there a fallback chain (semantic -> keyword -> None) when the primary method fails?
- [ ] Are query embeddings cached for repeated or similar queries?

### BM25

- [ ] Are BM25 parameters (k1, b) tuned on the document collection, not left at defaults?
  - k1 controls term saturation (default 1.2, tune between 0.5 and 2.0)
  - b controls length normalization (default 0.75, tune between 0.3 and 1.0)
- [ ] Is BM25 used as a standalone retriever or as part of hybrid fusion?
- [ ] Are stop words handled (removed or kept)?
- [ ] Is stemming or lemmatization applied?
- [ ] Is the BM25 index rebuilt when documents are added or removed?

### Hybrid Search

- [ ] Is hybrid search implemented as a combination of dense and sparse retrieval?
- [ ] Is the fusion strategy documented and measured?

  | Fusion Method | Behavior | When to Use |
  |---|---|---|
  | Reciprocal Rank Fusion (RRF) | Combines ranks from multiple result sets | Simple, robust, no score calibration needed |
  | Score normalization + weighted sum | Combines normalized similarity scores | When score distributions are comparable |
  | Round-robin interleaving | Alternates results from each method | When diversity is more important than rank quality |

- [ ] Are fusion weights tuned on a validation set?
- [ ] Does hybrid search return better results than either method alone (verified with metrics)?
- [ ] Is hybrid search latency acceptable for the use case?

### Reranking

- [ ] Is a reranking step applied after initial retrieval?
- [ ] Is the reranker a cross-encoder model (more accurate but slower)?
- [ ] Is the reranker compared against no-reranker on retrieval metrics before deployment?
- [ ] Is reranking applied to a reasonable candidate set (top 20-100) rather than the full corpus?
- [ ] Is reranking latency and cost measured?
- [ ] Is there a cache for reranker results on common queries?
- [ ] Are reranking scores used for pruning (remove low-scoring results after reranking)?
- [ ] Is the reranker model versioned and monitored for drift?

### Vector Store (PGVector)

- [ ] Is the vector store choice appropriate for the scale and requirements?

  | Feature | PGVector | Dedicated Vector DB |
  |---|---|---|
  | Transactional consistency | Full ACID | Varies |
  | Metadata filtering | Native PostgreSQL | Varies |
  | Index type | IVFFlat, HNSW | HNSW, IVF, others |
  | Scalability | Up to millions of vectors | Billions |
  | Operational overhead | Part of existing PostgreSQL | Separate service |

- [ ] Is the index type appropriate for the data size and query latency requirements?
  - IVFFlat: faster build, slower queries, approximate
  - HNSW: slower build, faster queries, higher memory, approximate
- [ ] Is the index rebuilt when new data changes the distribution significantly?
- [ ] Are the index parameters tuned (lists for IVFFlat, ef_search/ef_construction for HNSW)?
- [ ] Is the vector dimension compatible with the index type?
- [ ] Are PostgreSQL connection pool settings appropriate for expected query volume?
- [ ] Are vector queries included in PostgreSQL query monitoring and EXPLAIN plans?

### Tenant Isolation

- [ ] Does every retrieval query include a tenant or user ID filter derived from authentication context?
- [ ] Is the tenant filter applied at query time, not during ingestion?
- [ ] Are cross-tenant queries structurally impossible (not just discouraged by prompt)?
- [ ] Are shared documents (cross-tenant) explicitly designated with access control metadata?
- [ ] Are vector indexes tenant-aware (partitioned by tenant when data volume per tenant is large)?
- [ ] Are tenant isolation mechanisms tested with adversarial queries?

```python
# Tenant isolation: filter applied at query time from auth context
def retrieve(user: User, query: str, top_k: int) -> list[Document]:
    results = vector_store.similarity_search(
        query,
        k=top_k,
        filter={"tenant_id": user.tenant_id},
    )
    return results
```

### Freshness

- [ ] Is there a documented policy for document freshness (how old can a document be)?
- [ ] Are documents timestamped with ingestion time and source update time?
- [ ] Is there a mechanism to update or re-ingest documents when source content changes?
- [ ] Is stale document detection implemented (compare last update time with freshness policy)?
- [ ] Are deleted or revoked documents removed from the index?
- [ ] Is the freshness policy enforced in retrieval (filter by max age, prefer newer documents)?
- [ ] Is incremental ingestion supported, or is full reindexing required for every update?
- [ ] Are there integration tests verifying that updated content is reflected in retrieval results?

## Generation Checklist

### Prompt Construction

- [ ] Is the retrieval context explicitly delimited and separated from instructions?
- [ ] Does the prompt instruct the model to answer only from the provided context?
- [ ] Does the prompt include an abstention instruction ("If the answer is not in the context, say you do not know")?
- [ ] Is the prompt tested with edge cases (empty context, irrelevant context, conflicting context)?
- [ ] Is the system prompt versioned and change-logged?
- [ ] Are prompt changes evaluated against the evaluation dataset before deployment?

```text
You are a helpful assistant. Answer the user's question using ONLY the
context provided below. If the answer is not in the context, say
"I cannot answer this question based on the available information."

--- BEGIN CONTEXT ---
{retrieved_context}
--- END CONTEXT ---

--- QUESTION ---
{user_query}
```

### Context Window Management

- [ ] Is the generation model's context window known and documented?
- [ ] Are retrieved chunks pruned to fit within the context window (with margin for system prompt and response)?
- [ ] Is there a strategy for selecting which chunks to include when the total exceeds the window?
- [ ] Are chunks prioritized by relevance score when pruning?
- [ ] Is the context window utilization measured (tokens used vs. available)?
- [ ] Are very long documents or chunks truncated to fit?
- [ ] Is there a warning or alert when context utilization exceeds a threshold?

### Citation Grounding

- [ ] Are source references attached to each generated statement?
- [ ] Are citations verifiable (document ID, chunk index, source URL)?
- [ ] Is the citation format consistent and documented?

  | Citation Style | Format | Best For |
  |---|---|---|
  | Inline bracket | `The sky is blue [1].` | Simple, compact |
  | Footnote | `The sky is blue^[Source: document.pdf]` | Detailed references |
  | Document list | Separate citation section with URLs | User-facing applications |
  | Chunk-level | `[doc_id=doc-123, chunk=5]` | Debugging and evaluation |

- [ ] Is citation accuracy measured (what percentage of claims are correctly attributed)?
- [ ] Are there tests for hallucinated citations (model claims a source that does not exist)?
- [ ] Is there a mechanism to verify that a citation's source document actually contains the claimed information?
- [ ] Are citations preserved through response post-processing?

### Hallucination Reduction

- [ ] Is the model explicitly instructed to ground answers only in the retrieved context?
- [ ] Are there post-generation checks for hallucination (secondary model or rule-based)?
- [ ] Is factual consistency measured against the retrieved context (not the entire corpus)?
- [ ] Are there domain-specific constraints that reduce hallucination risk (enum values, allowed formats)?
- [ ] Is the abstention mechanism tested and effective?

Important: Retrieval does not eliminate hallucination. A model can still:
- ignore retrieved context and rely on parametric knowledge
- misinterpret retrieved context
- combine unrelated chunks into a false statement
- fabricate citations that look plausible
- produce confident-sounding but incorrect answers from ambiguous context

Post-generation validation is required, not optional.

### Answer Abstention

- [ ] Does the system have a defined abstention mechanism?
- [ ] Is the abstention threshold tuned (confidence score, relevance score)?
- [ ] Are there different abstention behaviors for different query types?
- [ ] Is abstention logged for quality monitoring?
- [ ] Are false positive abstentions (model refuses to answer when the context has the answer) measured?
- [ ] Are false negative abstentions (model answers when the context does not support it) measured?
- [ ] Is the abstention rate tracked over time?

### Sensitive Data Filtering

- [ ] Are retrieved documents filtered to remove sensitive content before reaching the generation model?
- [ ] Is PII detection applied to retrieved context?
- [ ] Are credentials, API keys, or secrets stripped from context?
- [ ] Is there a blocklist or deny-list for document sources or content types?
- [ ] Are retrieval results filtered by document-level access permissions?
- [ ] Is the generation model prevented from echoing sensitive data verbatim?
- [ ] Are output filters applied to prevent sensitive data from appearing in responses?

## Evaluation Checklist

### Retrieval Metrics

- [ ] Is retrieval quality measured before generation quality?
- [ ] Are standard retrieval metrics computed:

  | Metric | What It Measures | Target |
  |---|---|---|
  | Recall@k | Fraction of relevant documents in top-k results | Maximize |
  | Mean Reciprocal Rank (MRR) | Rank position of first relevant result | Maximize |
  | Precision@k | Fraction of top-k results that are relevant | Balance with recall |
  | Normalized Discounted Cumulative Gain (nDCG) | Rank quality accounting for graded relevance | Maximize |
  | Mean Average Precision (MAP) | Average precision across recall levels | Good for binary relevance |

- [ ] Are metrics computed at multiple values of k (1, 3, 5, 10, 20)?
- [ ] Are metrics disaggregated by query type (semantic, keyword, multi-hop)?
- [ ] Are confidence intervals reported for retrieval metrics?
- [ ] Is retrieval evaluation automated and run on every pipeline change?

### Generation Metrics

- [ ] Is generation quality measured:

  | Metric | What It Measures | How to Measure |
  |---|---|---|
  | Faithfulness | Whether generated claims are supported by context | Human eval or LLM-as-judge |
  | Answer relevance | Whether the answer addresses the query | Human eval or LLM-as-judge |
  | Citation accuracy | Whether citations match the supporting document | Verified against source text |
  | Abstention correctness | Whether the model correctly abstains when unsupported | Measured against labeled abstention cases |
  | Answer completeness | Whether all parts of the query are answered | Human eval or rubric-based |

- [ ] Are generation metrics computed separately from retrieval metrics?
- [ ] Are there human-annotated evaluation sets for faithfulness and relevance?
- [ ] Is LLM-as-judge calibrated against human judgments?

### Golden Q/A Sets and Regression Datasets

- [ ] Is there a golden set of query-answer pairs with known ground truth?
- [ ] Does the golden set include:

  - simple factual queries
  - multi-hop queries requiring multiple documents
  - edge cases (ambiguous queries, no relevant document)
  - adversarial queries (injection attempts, out-of-scope requests)
  - queries at different difficulty levels

- [ ] Is the golden set versioned and audited for quality?
- [ ] Are additions to the golden set reviewed by more than one person?
- [ ] Are there regression tests that check specific known failure cases?

- [ ] Is there a regression dataset that captures:

  - queries that previously produced bad answers
  - queries with known hallucination issues
  - queries where citations were incorrect
  - queries where abstention failed

- [ ] Are regression tests automated and run in CI on pipeline changes?

### Evaluation Automation

- [ ] Are retrieval evaluations automated in CI?
- [ ] Are generation evaluations automated (with LLM-as-judge or rubric-based methods)?
- [ ] Are evaluation results tracked over time (dashboard or reports)?
- [ ] Are changes to chunking, embedding, or retrieval compared against a baseline?
- [ ] Is there a mechanism to backfill evaluation results when golden sets change?

### Measurement Before Optimization

Do not change chunk size, top_k, embedding model, or retrieval strategy without measurement.

```python
# Always measure before and after a change
def evaluate_change(pipeline_before, pipeline_after, eval_set):
    before_metrics = evaluate(pipeline_before, eval_set)
    after_metrics = evaluate(pipeline_after, eval_set)

    for metric in ["recall@5", "mrr", "faithfulness", "answer_relevance"]:
        delta = after_metrics[metric] - before_metrics[metric]
        print(f"{metric}: {before_metrics[metric]:.3f} -> {after_metrics[metric]:.3f} ({delta:+.3f})")

    # Reject changes that degrade any metric past a threshold
    return after_metrics["faithfulness"] >= before_metrics["faithfulness"] - 0.02
```

## Security Checklist

- [ ] Is retrieval access controlled by tenant or user permissions?
- [ ] Is the tenant filter derived from authentication context, not from user input?
- [ ] Are documents with different sensitivity levels stored in separate indexes or partitions?
- [ ] Is the ingestion pipeline protected from untrusted document sources?
- [ ] Are uploaded documents scanned for malware before ingestion?
- [ ] Is sensitive data filtered before documents reach the generation model?
- [ ] Is the generation model prevented from outputting sensitive data from retrieved context?
- [ ] Are API keys for embedding and generation services stored securely (not in code, not in logs)?
- [ ] Are there rate limits on query endpoints?
- [ ] Are there rate limits on ingestion endpoints?
- [ ] Are vector store queries monitored for suspicious patterns (extraction attacks, probing)?
- [ ] Is there an audit log for queries that return sensitive content?
- [ ] Are system prompts and retrieval configuration not exposed to end users?
- [ ] Is output sanitized before rendering in web interfaces?
- [ ] Are there protections against prompt injection via retrieved documents?
- [ ] Is the RAG pipeline tested for indirect prompt injection (documents containing injection payloads)?
- [ ] Is there a process for revoking access to documents that were already ingested?

## Performance Checklist

### Latency

- [ ] Is latency measured end to end and per component?
- [ ] Are latency budgets defined for each pipeline stage?
- [ ] Is the retrieval latency acceptable for the use case?

  | Use Case | Acceptable Retrieval Latency |
  |---|---|
  | Real-time chat | < 500ms total |
  | Search-as-you-type | < 200ms |
  | Document analysis | < 5s |
  | Batch processing | Minutes to hours |

- [ ] Is embedding generation latency measured (model inference time)?
- [ ] Is the vector store query latency measured (index search time)?
- [ ] Is generation latency measured (TTFT, tokens per second)?
- [ ] Are latency outliers tracked and investigated (p95, p99)?

### Cost

- [ ] Is the cost per query measured and tracked?
- [ ] Are embedding costs measured (API cost or compute cost per document)?
- [ ] Are generation costs measured (per token, per query)?
- [ ] Is vector store compute cost measured (index build, query cost)?
- [ ] Is there a cost budget and alert when exceeded?
- [ ] Is the cost-quality tradeoff evaluated when making pipeline changes?

### Caching

- [ ] Are query embeddings cached for repeated queries?
- [ ] Are generation responses cached for identical queries?
- [ ] Is there a cache invalidation strategy when documents change?
- [ ] Is the cache hit rate measured?
- [ ] Is cache storage cost measured against compute savings?
- [ ] Are cache keys designed to avoid serving stale or incorrect results?
- [ ] Is there a warming strategy for expected queries?

### Caching Approaches

| Cache Type | What It Stores | TTL | Invalidation |
|---|---|---|---|
| Query embedding cache | Embedding vectors for frequent queries | Hours to days | On index change |
| Response cache | Generated answers for exact query matches | Minutes to hours | On document update |
| Chunk cache | Retrieved document chunks for identical queries | Session or minutes | On document update |
| Reranker cache | Reranking scores for (query, chunk) pairs | Hours | On model change |

### Monitoring

- [ ] Are retrieval metrics monitored in production (not just in evaluation)?
- [ ] Is there a dashboard for RAG pipeline health?

  Monitor:
  - queries per second
  - p50/p95/p99 latency per component
  - error rate per component
  - retrieval results per query (count, scores)
  - abstention rate
  - cache hit rate
  - cost per query
  - ingestion throughput

- [ ] Are alerts configured for latency, error rate, and abstention rate anomalies?
- [ ] Are logs structured and searchable per query ID?
- [ ] Is there a feedback loop for collecting production query quality signals?

## Required Review Output

When reviewing a RAG system, produce this summary:

```text
System overview:
[Name, purpose, and architecture summary of the RAG system.]

Pipeline components:
[Ingestion method, chunking strategy, embedding model, search method,
reranker, generation model.]

Chunking:
[Strategy, chunk size, overlap, rationale.]

Retrieval:
[Method(s), top_k, index type, fusion strategy, reranker.]

Metrics (retrieval):
[Recall@k, MRR, nDCG, precision@k with current values.]

Metrics (generation):
[Faithfulness, answer relevance, citation accuracy, abstention rate.]

Golden set:
[Number of Q/A pairs, version, last update.]

Security:
[Tenant isolation, sensitive data filtering, injection testing status.]

Performance:
[p50/p95/p99 latency, cost per query, cache hit rate.]

Issues found:
[List each finding with severity, location, impact, and recommended fix.]

Recommendations:
[Prioritized list of improvements with expected impact.]
```

## Completion Criteria

A RAG quality review is complete only when:

- all checklists in this document have been reviewed
- retrieval is evaluated with metrics (recall@k, MRR, nDCG) before generation quality
- generation is evaluated with faithfulness and answer relevance metrics
- golden Q/A and regression datasets exist and are versioned
- evaluation is automated and runs on pipeline changes
- metrics are measured before and after any change
- chunking strategy and parameters are documented with evaluation evidence
- search method (semantic, keyword, hybrid) is chosen based on data evaluation
- reranking effectiveness is measured, not assumed
- tenant isolation is enforced in every query
- sensitive data filtering is implemented
- latency and cost are measured with budgets defined
- caching is implemented where appropriate
- an abstention mechanism exists and is evaluated
- indirect prompt injection via retrieved documents is tested
- findings are documented with severity, location, impact, and recommendation
