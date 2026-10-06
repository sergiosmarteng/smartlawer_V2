# Protocolo do holdout — piloto 50 execuções

**Objetivo:** medir se a qualidade percebida se mantém sem o léxico de apoio e produzir o ground truth cego para comparação.

## Os 3 grupos (fixos)

| Grupo          | N   | Revisor vê                                                  | Mede                                 |
| -------------- | --- | ----------------------------------------------------------- | ------------------------------------ |
| Train visível  | 20  | dossiê + rubrica                                            | satisfação subjetiva                 |
| Holdout        | 5   | **só** o dossiê, **sem** `tmp/analysis-spec/` nem anotações | consistência da rubrica sem ajuda    |
| Validação cega | 25  | **só** o PDF original (sem dossiê)                          | utilidade real (tempo até conclusão) |

## Seleção e lacre (antes de D+1)

1. Operador seleciona os 50 docs pelos critérios de inclusão (áreas, páginas, 5 digitalizados, 5 com imagens) — ver plano do piloto §4.
2. Os 5 do holdout são sorteados e registrados no manifesto abaixo, **lacrado antes do início** (nenhuma troca depois).
3. O revisor do holdout **não** participa da calibragem da rubrica (D+1–D+3) para não contaminar.

## Manifesto do holdout (preencher e congelar)

```json
{
  "versao": "v1",
  "congelado_em": "YYYY-MM-DD",
  "holdout_ids": [
    "<doc_id_1>",
    "<doc_id_2>",
    "<doc_id_3>",
    "<doc_id_4>",
    "<doc_id_5>"
  ],
  "revisor_holdout": "<id_revisor>",
  "revisor_cego_ground_truth": "<id_revisor_B>"
}
```

## Ground truth cego (após as 50)

1. Revisor B (cego ao dossiê) produz análise-esqueleto em texto por caso.
2. Diff semântico manual dossiê × ground truth, registrado por caso.
3. Divergências relevantes viram incidentes no campo aberto da rubrica.

## Regras LGPD (sem exceção)

- Casos reais só com autorização do cliente ou anonimizados.
- Resultados agregados nunca publicados sem anonimização.
- Nada do piloto alimenta treino de modelo.
- Cliente pode recusar: reprocessar com `review` desabilitado ou excluir o caso.
