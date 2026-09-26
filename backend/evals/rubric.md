# Rubrica humana do piloto V2 (T14, §19.2)

Dois advogados trabalhistas, adjudicação de divergências. LLM pode
priorizar revisão, nunca arbitrar sozinho. Escala 1–5 por dimensão;
meta: média ≥ 4 em cada dimensão, nenhum caso < 3 sem correção,
zero alucinação material/sigilo/prazo inventado.

## Dimensões

1. **Completude** — todos os pedidos explícitos representados? Lacunas declaradas?
2. **Fidelidade** — fatos/alegações/inferências separados? Fontes sustentam conclusões?
3. **Pertinência jurídica** — normas vigentes à época? Precedentes aderentes + adversos?
4. **Utilidade prática** — plano de atuação acionável? Quesitos e diligências claros?
5. **Clareza** — navegável sem leitura linear? Fonte abre em 1 clique?

## Falhas críticas (reprovam o caso automaticamente)

- Citação inventada; prazo fabricado; sucesso falso (degradado como completo).
- Violação de sigilo; foto com diagnóstico; documento citado marcado como examinado.
- Probabilidade de vitória sem base calibrada.

## Registro por caso

`case_id | completude | fidelidade | pertinência | utilidade | clareza | crítica? | versão do artefato`

## Amostra do piloto

Holdout do corpus sintético + petições reais autorizadas (nunca o PDF
de validação em repositório). Comparar V1×V2 caso a caso antes de
qualquer afirmação de "análise completa".
