# Plano operacional — Piloto Real 50 execuções

**Data de criação:** 2026-10-02
**Status:** pronto para execução após (a) validação humana da release 0.2.0 no navegador e (b) smoke formal pós-deploy na VPS.
**Referência:** `smartlawer_V2/docs/implementation/release-0.2.0-vps.md`, `_dossie_indice-2026-09-27.md`, `2026-09-26-release-020-piloto.md`.

## 1. Objetivo

Medir, com advogado externo, **qualidade jurídica percebida** da análise 0.2.0 sobre casos reais, em **50 execuções** controladas, antes de:

- anunciar "análise completa" na landing;
- habilitar para qualquer usuário;
- partir para Onda 1 do Dossiê Universal V2.

**O que NÃO é este piloto:**

- Não é benchmark sintético (esse já rodou em T14 — `29c68e5 feat(eval): corpus sintetico e gate real`).
- Não é teste de carga.
- Não é validação de UX isolada.

## 2. Pré-condições (gate para iniciar)

- [ ] Validação humana no navegador OK (botão "Abrir dossiê V2" + copy PT-BR do upload com spinner).
- [ ] Smoke formal pós-deploy OK (ver `docs/operacao/smoke-pos-deploy-2026-10-02.md`).
- [ ] PAT rotacionado (ver `docs/runbooks/rotacao-pat-2026-10-02.md`) — **bloqueador de segurança**.
- [ ] Chave de IA na VPS ativa (Gemini ou OpenAI conforme `.env`).
- [ ] 2 advogados recrutados com carta de aceite assinada (LGPD: finalidade declarada).
- [ ] Holdout de 5 casos separados e lacrados antes do início.

## 3. Desenho amostral

| Grupo | N | Critério |
|---|---|---|
| **Train visível** (rubrica) | 20 docs | advogado-revisor **vê** o resultado do dossiê e preenche a rubrica |
| **Holdout** | 5 docs | advogado-revisor vê **só** o dossiê **sem o léxico** do `tmp/analysis-spec/`; usado para calibrar se a rubrica privada (LP) bate com o que o dossiê “diz” sem ajuda |
| **Validação cega** | 25 docs | advogado-revisor NÃO vê o dossiê V2 — só o caso (PDF original) — e produz a sua própria análise (esqueleto em texto); depois comparamos |

**Por que holdout vs blind:** queremos separar duas perguntas:

1. *“O dossiê V2 ajuda o advogado a ser mais rápido?”* → grupo **Validação cega** (mede utilidade real).
2. *“O que o advogado acha do dossiê quando o vê?”* → grupo **Train visível** (mede satisfação subjetiva).
3. *“A qualidade percebida é a mesma sem o léxico de apoio?”* → grupo **Holdout** (mede consistência da rubrica).

## 4. Critérios de inclusão dos documentos

Cada doc de piloto deve:

- Ser petição inicial real (não petição de teste). 10 docs são da pilha real do escritório; os outros 40 são públicos / autorizados por cliente.
- Cobrir áreas distintas:
  - 20 cível
  - 15 trabalhista
  - 10 consumidor
  - 5 previdenciário
- Variar em nº de páginas (≤10, 11–30, 31–60, >60).
- 5 deles devem ser **digitalizados** (escaneados) para exercitar OCR Docling.
- 5 devem ter **imagens relevantes** (fotografias de documentos, contratos) para exercitar extração de figuras.

## 5. Procedimento por execução

Para cada doc de piloto:

```text
1. Operador (smartlawer admin) faz upload via /upload.
   - Tempo de upload + extração anotado.
   - Se falhar (PROVIDER_UNAVAILABLE etc.): classificar falha, anotar, NÃO considerar "ruim" do dossiê.

2. Se execução OK: advogado-revisor abre /analysis/v2/<document_id> e:
   - Preenche rubrica (anexa §7).
   - Tempo até achar primeira informação útil (cronômetro).
   - Tempo até conclusão da análise (cronômetro).
   - Erros / bloqueios encontrados: anotar em campo aberto.

3. Comparação com a verdade (no fim, depois das 50):
   - Advogado B (2º advogado, cego ao dossiê) produz análise "ground truth" simplificada em texto.
   - Diff semântico manual entre dossiê V2 e ground truth.
```

## 6. Controle de custo

| Item | Cálculo |
|---|---|
| Custo médio por execução | somar tokens cobrados Gemini/OpenAI por run; dividir por 50 |
| Custo total estimado | 50 × (custo médio doc com extração Docling + análise) — definir cap por run no `.env` (`MAX_RUN_TOKENS`, `MAX_RUN_USD`) |
| Budget stop | parar piloto se consumo total > USD 100 (decisão do operador) |
| Concorrência | manter `worker_concurrency=2` (decisão atual da release 0.2.0) — Docling ~3min na 1ª conversão |
| Telemetria | capturar `run_id`, `started_at`, `finished_at`, `tokens_in/out`, `cost_usd` por execução — já instrumentado em `d7e1502 feat(ops): limites, telemetria e exclusao rastreavel (V2 T13)` |

## 7. Rubrica de avaliação (anexa)

```yaml
# Preenchida por advogado-revisor para cada doc do train visível + holdout.
id: <doc_id>
run_id: <uuid>
data: <YYYY-MM-DD>
advogado: <id_revisor>

secoes:
  visao_geral:
    utilidade: 1-5                    # 1=inútil, 5=substitui leitura do PDF
    precisao_factual: 1-5
    cobertura: 1-5
    limitacoes_explicitas: bool       # se TRUE, há declaração honesta de lacuna
  pedidos:
    completude: 1-5                   # % dos pedidos representados
    fontes_resolvidas: 1-5              # quão fácil abrir a fonte
    valores_extraidos: 1-5
  provas:
    identificacao: 1-5
    matriz_pedido_x_prova: 1-5        # 1=ausente, 5=matriz completa
  direito:
    pertinencia: 1-5
    verificacao: 1-5
  calculos:
    corretude: 1-5
    reproducao: 1-5                   # rodar de novo = mesmo número
  estrategia_acoes:
    utilidade: 1-5
    cobertura_risco: 1-5
  revisao:
    facilidade_correcao: 1-5
    historico_versoes: 1-5

estado_honesto:
  progresso_coerente: true|false       # progresso da UI corresponde ao real?
  falha_anunciada: true|false         # se falhou, disse ao usuário?

custos:
  tempo_primeira_info_util_min: <float>
  tempo_conclusao_min: <float>

observacoes: <texto livre>
incidentes:
  - <descrição>     # lista; cada incidente com severidade (low/med/high)
```

Métricas agregadas após as 50:

- Média e desvio padrão por eixo.
- % de docs com `limitacoes_explicitas = true` (esperado: ≥80% — princípio de honestidade).
- % de docs com falha do provedor (esperado: ≤5%, dependendo do tráfego).
- % de docs com `progresso_coerente = true` (esperado: ≥95%).
- Custo mediano por execução (sinalizado se > cap).

## 8. Critérios de Go / não-go para ampliar do dossiê

**Go (liberar Onda 0 + habilitar para mais advogados):**

- Média geral de utilidade ≥ 3.5/5.
- ≤10% dos docs com `limitacoes_explicitas = false` E ocorrência de afirmação sem fonte.
- ≤5% dos docs com erro grave de cálculo (AC-08).
- Custo mediano por execução dentro do budget.
- Nenhum incidente de privacidade / LGPD.

**Não-go (bloquear, voltar para engenharia):**

- Média geral de utilidade < 2.5/5.
- >10% dos docs com afirmação material sem fonte.
- >1% dos docs com teses inventadas (FALLBACK_THESES reincidente).
- Custo explode (>2× do cap).
- Vazamento de dado entre usuários/organizações.

## 9. Cronograma sugerido

| Dia | Atividade |
|---|---|
| D-0 | Gate de pré-condições OK; baseline do piloto cadastrado. |
| D+1 a D+3 | Recrutar 2 advogados; carta LGPD; calibrar rubrica com 3 docs-piloto. |
| D+4 a D+13 | Executar 50 docs (~5/dia) com revisão ao fim de cada dia. |
| D+14 a D+17 | Análise agregada (advogado + operador); go/no-go. |
| D+18 | Decisão Go/no-go documentada em `docs/operacao/resultado-piloto-<data>.md`. |

## 10. Riscos e mitigações

| Risco | Mitigação |
|---|---|
| Advogado não terminar a tempo | Acordo prévio de prazo; pagamento por entrega |
| Custo estourar budget | `MAX_RUN_TOKENS` no `.env`; parar e investigar |
| Resultado não compará (muita variabilidade) | Holdout + revisão cega reduzem ruído |
| Cliente recusar (LGPD) | Carta de aceite + opção de reprocessamento com `review` desabilitado |
| Tempo de Docling dominar a percepção | Medir separado; UI mostra estágios reais (AC-11) |
| Cálculo determinístico divergir | Testar com dataset de valores conhecidos; fixar `Calculation` versionado |

## 11. Não-objetivos

- Não usar o piloto para treinar modelo.
- Não publicar resultados agregados sem anonimizar (LGPD).
- Não estender escopo da rubrica sem debater antes — rubrica é fixa no D+14.