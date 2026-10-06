# Rubrica do piloto — v1 (CONGELADA)

**Status:** congelada em 2026-10-06. **Imutável até D+14.** Qualquer mudança exige nova versão (`v2`) e reavaliação dos casos já julgados — nunca edição retroativa.

**Fonte normativa:** `docs/operacao/piloto-50-execucoes-2026-10-02.md` §7–§8.
**Versão máquina-legível:** `backend/evals/rubric_pilot_v1.toml` (vale o TOML em caso de divergência — o teste `test_pilot_metrics.py::test_rubric_toml_matches_piloto_thresholds` trava os thresholds).

## Escala

Todas as notas de 1 (inútil) a 5 (excelente), exceto campos `bool` indicados.

## Dimensões

| Seção            | Campo                        | O que mede                           |
| ---------------- | ---------------------------- | ------------------------------------ |
| visao_geral      | utilidade                    | 1=inútil, 5=substitui leitura do PDF |
| visao_geral      | precisao_factual             | fatos corretos e conferíveis         |
| visao_geral      | cobertura                    | cobertura do caso                    |
| visao_geral      | limitacoes_explicitas (bool) | há declaração honesta de lacuna      |
| pedidos          | completude                   | % dos pedidos representados          |
| pedidos          | fontes_resolvidas            | quão fácil abrir a fonte             |
| pedidos          | valores_extraidos            | valores presentes e corretos         |
| provas           | identificacao                | provas identificadas                 |
| provas           | matriz_pedido_x_prova        | 1=ausente, 5=matriz completa         |
| direito          | pertinencia                  | normas pertinentes ao caso           |
| direito          | verificacao                  | vigência e verificação               |
| calculos         | corretude                    | números corretos                     |
| calculos         | reproducao                   | rodar de novo = mesmo número         |
| calculos         | erro_grave (bool)            | erro grave de cálculo (AC-08)        |
| estrategia_acoes | utilidade                    | plano acionável                      |
| estrategia_acoes | cobertura_risco              | riscos cobertos                      |
| revisao          | facilidade_correcao          | corrigir é simples                   |
| revisao          | historico_versoes            | versões preservadas                  |

## Estado honesto (por caso)

- `progresso_coerente` (bool): progresso da UI corresponde ao real?
- `falha_anunciada` (bool): se falhou, disse ao usuário?

## Custos (por caso)

- `tempo_primeira_info_util_min`, `tempo_conclusao_min` (cronômetro)
- `custo_usd` (telemetria da run)

## Incidentes (lista aberta, com severidade)

Cada item: descrição + `low`/`med`/`high`/`privacidade`. Incidente de privacidade ou sigilo **reprova o piloto sozinho**.

## Thresholds Go / Não-go (§8, travados no TOML)

**Go (todos):** utilidade média ≥ 3.5; afirmação sem fonte ≤ 10%; erro grave de cálculo ≤ 5%; custo mediano dentro do cap; zero incidentes de privacidade.
**Não-go (qualquer um):** utilidade ≤ 2.5; afirmação sem fonte ≥ 10%; tese inventada ≥ 1%; custo > 2× cap; vazamento de dados.
