# SmartLawer — Dossiê Jurídico, Onda 1

**Status:** especificação de produto para revisão e planejamento pelo DeepCode

**Data:** 2 de outubro de 2026

**Módulos:** Cível/processo civil; Família/sucessões; Trabalhista; Consumidor; Previdenciário.

## 1. Resultado e dependências

Esta onda especializa o [Dossiê Universal](2026-09-27-dossie-juridico-universal-design.md) após a Onda 0. O artefato publicado continua no schema 3.0, com os mesmos IDs, estados por seção, fontes, imagens, revisão, versões e isolamento de acesso. Um módulo acrescenta objetos e verificações ao núcleo; ele não substitui fatos, pedidos ou fontes já extraídos. O [plano da Onda 0](../plans/2026-10-02-dossie-juridico-universal-onda-0.md) é pré-requisito técnico.

Resultado esperado: em cada uma das cinco áreas, o advogado recebe uma matriz de questões próprias do tema, prova necessária, contrapontos, cálculo reproduzível quando aplicável e próximas diligências. Uma questão inaplicável fica marcada `not_applicable` com motivo. Quando faltam documentos ou parâmetros legais, o módulo registra `partial` ou `blocked` e uma ação concreta.

## 2. Contrato de módulo

Cada módulo desta onda declara `module_id`, `version`, `supported_areas`, `document_types`, `required_sections`, `issue_checklists`, `calculation_rules`, `research_sources` e `evaluation_cases`. A ativação é multirrótulo. `civil_procedure` pode complementar `family`, `consumer`, `labor` ou `social_security` conforme o procedimento, sem duplicar eventos e pedidos.

Cada resultado especializado usa este envelope, armazenado em `module_results[module_id]` no artefato 3.0; se o campo ainda não existir, adicioná-lo como extensão opcional formal do schema, mantendo compatibilidade de leitura:

```json
{
  "module_id": "family",
  "module_version": "1.0.0",
  "status": "complete",
  "reason": "Matriz aplicável examinada",
  "issue_assessments": [{
    "issue_key": "child_support.need_capacity",
    "status": "partial",
    "conclusion": "Necessidade alegada; capacidade ainda não documentada",
    "factual_refs": ["fact-1"],
    "supporting_source_refs": ["source-1"],
    "adverse_source_refs": [],
    "missing_inputs": ["comprovante de renda atual"],
    "related_claim_ids": ["claim-1"],
    "action_ids": ["action-1"]
  }],
  "calculation_ids": [],
  "limitations": []
}
```

`issue_key` é estável e versionado. A alteração de uma regra gera nova versão do módulo; uma reanálise cria novo run. `source_refs` apontam às fontes do artefato, inclusive páginas e regiões de imagem. Dados jurídicos pesquisados têm fonte externa e data de consulta; fatos do caso mantêm fonte documental.

## 3. Regras comuns de análise

- Para cada questão aplicável, mostrar premissas, norma válida na data pertinente, fatos favoráveis, fatos adversos, prova necessária e conclusão condicionada.
- Separar direito material, rito, fase, competência e pedido. O procedimento não é inferido somente pelo assunto.
- Registrar localidade, tribunal, datas dos fatos, data da peça e data de referência; divergências permanecem explícitas.
- Norma, precedente, convenção coletiva e ato infralegal são verificados em fonte oficial, com histórico temporal quando necessário.
- Prazo ou prescrição só recebe data final quando marco inicial, regime aplicável e evento interruptivo/suspensivo estiverem sustentados; caso contrário, gerar pergunta e diligência.
- Cálculo exige fórmula cadastrada, parâmetros, origem de índices, período, moeda e arredondamento. A IA não fornece número final livre.
- Imagem é prova visual contextualizada; fotografia, print ou anotação da parte não prova, por si só, autoria, data, autenticidade ou causalidade.
- A classificação errada de área pode ser corrigida pelo advogado e dispara nova análise versionada.

## 4. Cível e processo civil (`civil_procedure@1.0.0`)

### Questões obrigatórias

| Tema | Dados e checagens | Saída útil |
|---|---|---|
| Relação material | obrigação, título, inadimplemento, dano, nexo, excludentes, partes | mapa de premissas por pedido |
| Rito e competência | foro, valor, natureza da causa, cláusula de eleição, juizado, fase | hipótese de competência condicionada |
| Peças e atos | inicial, contestação, réplica, decisão, recurso, cumprimento | eventos, pedidos e ônus por fase |
| Tutela provisória | urgência/evidência, perigo, reversibilidade, contracautela | matriz de requisitos e provas faltantes |
| Prova | distribuição do ônus, perícia, documentos, testemunhas, autenticidade | matriz fato versus prova |
| Tempo | prescrição, decadência, intimação, preclusão, coisa julgada | cronologia processual verificável |
| Remédios | obrigação de fazer/não fazer, cobrança, indenização, rescisão, execução | consequências e relações entre pedidos |

### Fontes e cálculo

Fontes iniciais: [Código Civil](https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm), [Código de Processo Civil](https://planalto.gov.br/ccivil_03/_ato2015-2018/2015/lei/l13105compilada.htm) e [Lei dos Juizados Especiais](https://www.planalto.gov.br/ccivil_03/leis/l9099.htm). Precedentes devem vir do tribunal competente e ter inteiro teor ou trecho verificável. Cálculos candidatos: soma de parcelas documentadas, atualização parametrizada e comparação de cenários; juros, índice e termo inicial dependem de regra validada e decisão/documento do caso.

### Gates específicos

- Não concluir competência apenas pelo valor sem verificar natureza, partes e rito.
- Não calcular prazo com data de intimação desconhecida.
- Não tratar petição como prova do inadimplemento quando o documento contratual/pagamento não foi examinado.

## 5. Família e sucessões (`family@1.0.0`)

### Questões obrigatórias

| Tema | Dados e checagens | Saída útil |
|---|---|---|
| Pessoas e vínculos | parentesco, filiação, idade, representação, capacidade, dependência | grafo de pessoas com fontes |
| Guarda e convivência | situação atual, rotina, decisões, alegações de risco, provas | alternativas e pontos de apuração, sem diagnóstico |
| Alimentos | necessidade, possibilidade, proporcionalidade, renda, despesas, vigência | cenários condicionados e documentos faltantes |
| Divórcio e patrimônio | regime de bens, aquisição, titularidade, dívidas, avaliações | inventário de bens e controvérsias |
| Sucessões | óbito, herdeiros, testamento, bens, dívidas, doações, inventário | quadro de interessados e bens, sem partilha fictícia |
| Medidas urgentes | tutela, proteção de incapaz, provas e risco imediato | prioridade de revisão humana |

### Fontes, imagens e cálculo

Fontes iniciais: [Código Civil](https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm), [CPC](https://planalto.gov.br/ccivil_03/_ato2015-2018/2015/lei/l13105compilada.htm) e [ECA](https://planalto.gov.br/ccivil_03/leis/l8069compilado.htm). Certidões, decisões, comprovantes de renda, despesas e documentos patrimoniais são fontes do caso. Fotografias de criança e documentos de saúde ficam ocultos por padrão, com acesso auditado. Cálculo de alimentos é cenário explícito, nunca percentual presumido como regra universal; partilha exige regime, datas, bens, dívidas e premissas verificadas.

### Caso de regressão obrigatório

Usar fixture sintética de disputa de guarda e alimentos inspirada na forma do dossiê que originou o defeito: pedidos de guarda compartilhada, distribuição de encargos e alimentos. O resultado deve conter pessoas, eventos, alegações separadas de prova, comprovantes examinados versus mencionados, questões jurídicas, teses para ambos os polos, possíveis cenários financeiros e diligências. A contagem de páginas não pode ser `0/0` se há documento processado.

### Gates específicos

- Não afirmar capacidade econômica sem fonte.
- Não concluir risco à criança só por alegação ou imagem.
- Não expor dados de menores em resumo, log ou exportação sem controles do caso.

## 6. Trabalhista (`labor@1.0.0`)

### Questões obrigatórias

| Tema | Dados e checagens | Saída útil |
|---|---|---|
| Vínculo | contratação, subordinação, função real, jornada, remuneração, término | linha contratual e controvérsias |
| Verbas | salário, férias, 13º, FGTS, rescisão, adicionais, reflexos | pedidos por rubrica e período |
| Jornada | cartões, escalas, banco de horas, acordos, contracheques | divergências e memória de cálculo |
| Normas coletivas | categoria, base territorial, vigência, cláusula integral | aplicação temporal justificada |
| Acidente/doença | evento, CAT, treinamento, EPI/EPC, nexo, laudo, capacidade | matriz de prova e teses condicionadas |
| Processo | competência, prescrição, liquidação, ônus, perícia | pendências por fase |

### Reuso e fontes

Reaproveitar a matriz de acidente existente em `backend/app/modules/labor/checklist.py`, mas corrigir seu vocabulário: uma referência a uma alegação não torna o item `documented`; a evidência precisa ter tipo e suporte verificados. Fontes iniciais: [CLT](https://www.planalto.gov.br/ccivil_03/decreto-lei/del5452compilado.htm), [Lei 8.213/1991](https://www.planalto.gov.br/ccivil_03/leis/l8213compilado.htm), NRs do órgão oficial competente e instrumentos coletivos integrais com vigência. A NR e a CCT devem ser avaliadas na data do fato.

### Cálculos e gates

Fórmulas versionadas para rubricas trabalhistas somente após identificar remuneração, período, jornada, reflexos e exclusões; detectar sobreposição entre verbas. Nunca inferir incapacidade, culpa, nexo ou autenticidade de equipamento apenas por fotografia. Uma perícia alegada e não anexada fica `mentioned_not_located`.

## 7. Consumidor (`consumer@1.0.0`)

### Questões obrigatórias

| Tema | Dados e checagens | Saída útil |
|---|---|---|
| Relação de consumo | fornecedor, consumidor, produto/serviço, cadeia | papéis e escopo da relação |
| Oferta e contrato | publicidade, preço, condições, aceite, alterações | comparação entre oferta e execução |
| Vício/defeito | evento, natureza, dano, comunicação, tentativa de solução | cronologia e prova por hipótese |
| Cobrança | faturas, pagamentos, estornos, negativação | valores e duplicidades verificáveis |
| Atendimento | protocolos, respostas, datas e prazos | trilha de tentativa extrajudicial |
| Dados e plataforma | tratamento de dados, segurança, intermediários | ativação conjunta de LGPD quando pertinente |

Fontes iniciais: [CDC](https://planalto.gov.br/ccivil_03/leis/l8078compilado.htm), contrato e oferta efetivamente apresentados; normas setoriais oficiais somente se a atividade for identificada. Cálculos: diferenças de cobrança, valores pagos, estornos e cenários de restituição sob regra validada. Print de aplicativo ou conversa conserva metadados e contexto; não confirma sozinho titularidade da conta ou integridade da captura.

Gate: não aplicar automaticamente inversão do ônus, responsabilidade solidária, prazo decadencial ou restituição em dobro sem premissas e fonte jurídica verificadas.

## 8. Previdenciário (`social_security@1.0.0`)

### Questões obrigatórias

| Tema | Dados e checagens | Saída útil |
|---|---|---|
| Regime | RGPS, RPPS ou outro; órgão e benefício | regime identificado ou pergunta prioritária |
| Histórico | filiação, vínculos, contribuições, carência, qualidade | linha temporal com lacunas e divergências |
| Requerimento | DER, decisão, ciência, recurso, documentos | cronologia administrativa/judicial |
| Incapacidade | atestados, perícias, duração, atividade, DII alegada | matriz documental, sem diagnóstico próprio |
| Dependência | vínculo, idade, dependência, óbito | provas e requisitos por benefício |
| Valor | salários de contribuição, índices, períodos, teto | cenário reproduzível condicionado |

Fontes iniciais: [Lei 8.213/1991](https://www.planalto.gov.br/ccivil_03/leis/l8213compilado.htm), [Lei 8.212/1991](https://www.planalto.gov.br/ccivil_03/leis/l8212compilado.htm) e atos oficiais vigentes do INSS, conforme benefício e data. CNIS, cartas, processos administrativos, laudos e comprovantes devem ser examinados por revisão. Cálculos só são habilitados com regime, espécie, datas, salários e regras temporais suficientes. O módulo não presume benefício ou retroativos com base em poucos documentos.

## 9. Pesquisa, avaliação e aceite

Cada módulo terá corpus sintético/anonimizado com ao menos: um caso favorável, um adverso, um incompleto, um multiarea, um documento longo com pedido final, um documento com imagem e um caso de norma temporalmente alterada. Avaliação jurídica por dois revisores da área medirá cobertura de questões aplicáveis, precisão factual, pertinência de fontes, equilíbrio, utilidade e cálculo. Divergências dos revisores são registradas; nenhum percentual de êxito é inferido.

Critérios de aceite por módulo:

1. Todas as questões ativadas produzem avaliação fundamentada ou estado justificado.
2. Pedido e tese relevantes apontam para fatos, provas, normas e fontes correspondentes.
3. Fonte oficial, versão, vigência e data de consulta acompanham cada regra aplicada.
4. Falha de pesquisa mantém análise documental `partial` e pendência acionável.
5. Cálculo sem parâmetros fica bloqueado com lista das entradas faltantes.
6. Casos multiarea ativam módulos pertinentes sem duplicar pedidos, fatos ou imagens.
7. Usuário sem acesso ao caso não acessa resultados, fontes nem visuais especializados.
8. Artefatos anteriores preservam módulo e versão usados; reanálise cria novo artefato.

## 10. Entrega ao DeepCode

Criar planos de implementação separados para `civil_procedure` + `family` (Onda 1A) e para `labor` + `consumer` + `social_security` (Onda 1B), conforme o plano da Onda 0. Cada módulo terá pacote próprio em `backend/app/modules/<module_id>/`, testes unitários, corpus, gate jurídico, verificação de fontes, componentes de apresentação sobre as abas universais e feature flag individual. Fazer rollout de um módulo por vez; falha de um módulo não impede o dossiê universal.

## 11. Referências oficiais verificadas

- [Código Civil — Planalto](https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm)
- [CPC — Planalto](https://planalto.gov.br/ccivil_03/_ato2015-2018/2015/lei/l13105compilada.htm)
- [ECA — Planalto](https://planalto.gov.br/ccivil_03/leis/l8069compilado.htm)
- [CLT — Planalto](https://www.planalto.gov.br/ccivil_03/decreto-lei/del5452compilado.htm)
- [CDC — Planalto](https://planalto.gov.br/ccivil_03/leis/l8078compilado.htm)
- [Lei 8.213/1991 — Planalto](https://www.planalto.gov.br/ccivil_03/leis/l8213compilado.htm)

Estas páginas orientam o catálogo inicial de pesquisa; o implementador deve conferir redação e vigência pertinentes ao caso no momento da execução.
