# Worker Report — A6 PII masking + prompt-injection defense (2026-09-08)

## Scope

GitHub issue #18: mascarar PII em logs/traces, classificar input, separar
instrucao de dado recuperado. DoD: teste red-team basico passando.

## Changes

- `backend/app/core/security_rag.py` (new): `mask_pii`/`contains_pii`
  (CPF, CNPJ, e-mail, telefone BR, OAB, processo CNJ; nunca levanta,
  trunca em 500 chars), `is_injection_attempt` (PT+EN: ignore/desconsidere,
  revele system prompt, jailbreak/DAN, override/bypass, exfiltre; safe-harbor
  para perguntas juridicas legitimas), `BLOCK_MESSAGE` deterministica.
- `backend/app/core/rag_answer.py`: SYSTEM_PROMPT ganha secao de seguranca
  (trechos = DADOS nao confiaveis, nunca revelar prompt, minimizar PII);
  `build_grounded_prompt` delimita `=== TRECHOS RECUPERADOS (DADOS ...) ===`
  + instrucao de ignorar ordens embutidas; `answer_query` classifica antes
  de retrieval/LLM e retorna bloqueio sem citar nada (ai_draft +
  requires_human_review mantidos).
- `backend/app/api/routes/chat.py`: `POST /chat/stream` bloqueia injection
  sem chamar retrieval/LLM; `logger.exception` nao mais interpola excecao
  (evita vazar PII/conteudo em logs); bloqueio logado com query mascarada.
- `backend/tests/test_security_rag.py` (new, 7 tests): redacao de PII,
  never-raise/truncamento, 7 ataques PT/EN bloqueados, 4 benignas + vazios
  liberados, isolamento de dados no prompt, bloqueio sem chamar LLM,
  bloqueio no endpoint stream.

## Validation

- `pytest backend/tests/test_security_rag.py -q`: **7 passed**.
- `pytest backend/tests/ -q`: **64 passed** (57 antes + 7 novos).
- `python backend/evals/run_gate.py`: `GATE PASSED` (sem regressao).

## Notes for next worker (Onda B)

- Mascaramento cobre logs/traces e queries logadas; excerpts de citacao
  ainda retornam texto literal do chunk (necessario p/ fundamentacao) —
  B2/C4 podem avaliar redacao de PII nos excerpts se a LGPD exigir.
- Classificador e regex leve e deterministico; upgrade p/ LLM-judge pode
  substituir o interior de `is_injection_attempt` sem mudar o contrato.
- Live pgvector/FTS/Cohere/LLM continuam pendentes de Docker + chaves (B1).
