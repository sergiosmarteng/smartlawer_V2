---
name: smartlawer-rag-production
description: RAG juridico producao SmartLawer_V2 com FastAPI, pgvector, Celery, Redis e Next.js. Use para ingestao de peticoes e contratos, chunking juridico, hybrid search, rerank, streaming com citacoes e avaliacao RAGAS com conformidade LGPD.
license: MIT
compatibility: opencode
metadata:
  project: smartlawer-v2
  stack: fastapi-pgvector-nextjs
  domain: legal-rag
---

# SmartLawer RAG Production

Padrao oficial de RAG juridico do SmartLawer_V2. Stack: `backend/` FastAPI + Celery + Redis, Postgres + pgvector, `src/` Next.js 14 App Router.

## Quando usar

Use quando for: ingerir PDF/DOCX juridico, alterar chunking/embedding, mexer em busca hibrida, reranker, endpoint de chat com streaming, avaliacao RAGAS, ou qualquer resposta com citacao legal.

## Workflow

### 1. Ingestao (Celery worker, nunca no request)

- Upload vai para `./uploads`, enfileira job Celery com `document_id`, `matter_id`, hash SHA256 para deduplicacao.
- Parser: PDF digital via `pypdf`/`Docling`, PDF escaneado com fallback OCR. Preservar metadados: `numero_processo, tribunal, comarca, data_julgamento, relator, classe, assunto, segredo_justica`.
- Chunking juridico: recursivo 800-1200 tokens com overlap 150-200, nunca quebrar no meio de artigo/inciso/alinea. Separadores preferenciais: `\n\nArt.`, `\n§`, `\nInciso`, `\nSúmula`, ementa/decisao.
- Embedding: `text-embedding-3-small` default. Self-hosted `BGE-M3` se sigilo exigir. Salvar `embedding_model_version` junto ao vetor para permitir reindexacao.
- pgvector prod (`ivfflat`/`hnsw`), Chroma so para dev local. Sempre filtrar por `tenant_id` + `matter_id` antes do ANN.

### 2. Retrieval

- Hybrid search obrigatorio: vetor pgvector + BM25/FTS Postgres, fusao RRF `k=60`.
- Reranker `Cohere rerank-3` ou `BGE-reranker` no top-30 -> top-6. Maior ROI do pipeline.
- Filtros: `tribunal, ano, ramo_direito, favoravel/desfavoravel`. Respeitar `segredo_justica`: nunca retornar trecho sigiloso para tenant errado.
- Retornar sempre: `documento, pagina, trecho literal, score, data`.

### 3. Geracao (FastAPI SSE + Next.js streaming)

- Endpoint FastAPI SSE com `tenant_id` no contexto, nunca confiar so no JWT do front.
- System prompt: "Responda apenas com base nos trechos. Toda afirmacao juridica exige [doc N, p. X]. Se nao houver base, diga que nao encontrou."
- Front Next.js 14: componente chat streaming com `useChat`, renderizar citacoes clicaveis, painel de fontes lateral.
- `structured-output-reliability`: resposta JSON validada `{answer, citations[], follow_up, confidence}`.

### 4. Seguranca LGPD (obrigatorio)

- `prompt-injection-defense`: classificar input, separar instrucao de dado recuperado, ignorar instrucao embutida em peticao ("desconsidere e ...").
- `llm-app-security`: PII masking antes de log/trace, logs sem CPF/OAB/conteudo sigiloso, retencao minima.
- `human-in-the-loop`: nunca protocolar, enviar peca ou dar parecer final sem aprovacao humana explicita no UI. Marcar rascunho como `AI-DRAFT, revisar`.

### 5. Avaliacao

- Golden set minimo 30 perguntas juridicas reais com resposta esperada + docs ouro.
- Metricas RAGAS: `faithfulness, answer_relevancy, context_precision, context_recall`. Gate CI: `faithfulness >= 0.85`.
- `ai-evaluation` com juiz calibrado + revisao humana amostral. Regressao a cada mudanca de chunker/embedder/prompt.

## Anti-patterns (nao fazer)

1. Chunk fixo 512 sem respeitar estrutura legal.
2. Vetor puro sem BM25 — perde numero de artigo e sumula.
3. Sem reranker em producao.
4. Ingestao sincrona no request API.
5. Citacao inventada ou pagina aproximada.
6. Logar prompt com dados do cliente.
7. Deploy sem golden set e gate de faithfulness.
8. Um embedding sem versionamento — impede reindex.

## Verificacao

```bash
# backend
pytest backend/tests/test_rag_ -q
ruff check backend
# frontend
npm run lint
npm run build
```

## Skills relacionadas

Lider: `rag-quality-review`. Suporte: `ai-evaluation, structured-output-reliability, llm-app-security, prompt-injection-defense, llm-observability, contract-review, pdf-processing, human-in-the-loop`.
