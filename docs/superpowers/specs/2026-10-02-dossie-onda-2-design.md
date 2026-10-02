# SmartLawer — Dossiê Jurídico, Onda 2

**Status:** especificação de produto para revisão e planejamento pelo DeepCode

**Data:** 2 de outubro de 2026

**Módulos:** Empresarial/societário; Contratos; Tributário; Administrativo; Imobiliário.

## 1. Resultado e dependências

A Onda 2 acrescenta análise especializada de negócios, patrimônio e atuação estatal ao [Dossiê Universal](2026-09-27-dossie-juridico-universal-design.md). Depende do contrato e da publicação segura da Onda 0. Pode ser implementada depois da Onda 1 sem depender funcionalmente de cada módulo dela; quando duas áreas coexistirem, os módulos compartilham entidades, fatos, pedidos e fontes por IDs estáveis.

O advogado deve conseguir comparar instrumentos, obrigações, períodos e versões; identificar partes e responsáveis; quantificar somente o que tem parâmetros; localizar cada fato e regra; enxergar obrigações e riscos de ambos os polos. O sistema não emitirá opinião conclusiva baseada apenas no título de um documento.

## 2. Contrato e regras transversais

Usar `module_results[module_id]` do schema 3.0 descrito na [Onda 1](2026-10-02-dossie-onda-1-design.md), com `issue_assessments`, fontes, limitações e ações. Ativar módulos por questão: um contrato societário pode acionar `contracts` e `corporate`; um imóvel comprado em recuperação judicial pode acionar também `real_estate`. O módulo primário não absorve o outro.

As especializações devem preservar:

- versões de contrato, estatuto, edital, matrícula e auto, com hash e datas de vigência;
- pessoa/empresa, CNPJ/CPF mascarado, grupo econômico alegado e papéis distintos;
- competência do ente federativo, órgão, município/estado, regime, exercício e data do fato;
- separação entre valor declarado, valor cobrado, valor pago, valor calculado e valor controvertido;
- calendário dos atos e prazos com origem do marco temporal;
- pesquisa em fonte oficial com texto e vigência pertinentes, incluindo normas locais quando aplicáveis;
- cálculo com fórmula, período, índice, moeda, base de incidência e versão; regra ausente gera `blocked`;
- documentos e imagens de matrícula, planta, assinatura, nota fiscal e comprovante com página original.

Um vínculo jurídico não é afirmado só porque dois nomes aparecem no mesmo documento. Cláusula sem assinatura ou versão não é tratada automaticamente como aceita. Inscrição registral e publicidade não são presumidas pelo nome do arquivo.

## 3. Empresarial e societário (`corporate@1.0.0`)

### Matriz de questões

| Tema | Dados a extrair e confrontar | Produto no dossiê |
|---|---|---|
| Estrutura | sociedades, sócios, administradores, participação, controladas, filiais | grafo versionado de entidades e poderes |
| Atos | contrato/estatuto, atas, alterações, registro, deliberações, procurações | cronologia de decisões e validade a confirmar |
| Governança | quórum, convocação, conflito de interesse, deveres, representação | checklist com suporte e lacunas |
| Capital e quotas | subscrição, integralização, cessão, avaliação, preferência | quadro de participação e divergências |
| Obrigações | garantias, dívida, distribuição, prestação de contas, responsabilidade | matriz obrigação versus parte |
| Crise | inadimplência, renegociação, recuperação, falência, credores | alertas condicionados por procedimento |
| Prova | livros, atas assinadas, demonstrativos, registros, e-mails | o que foi examinado versus apenas citado |

### Fontes e cálculos

Fontes iniciais: [Código Civil](https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm), [Lei das S.A.](https://www.planalto.gov.br/ccivil_03/leis/l6404consol.htm), [Lei de Recuperação e Falência](https://www.planalto.gov.br/ccivil_03/_ato2004-2006/2005/lei/l11101compilado.htm), atos oficiais de registro e normas específicas do tipo societário. Cálculos permitidos: participação baseada em quotas/ações documentadas, saldo de obrigações e cenários de rateio parametrizados; avaliação econômica de empresa exige método e dados fornecidos, não valor inventado.

Gates: não atribuir responsabilidade pessoal de administrador/sócio, controle ou fraude somente por posição societária; não concluir quórum sem composição e regra vigente; distinguir pedido de recuperação, deferimento e concessão.

## 4. Contratos (`contracts@1.0.0`)

### Matriz de questões

| Tema | Dados a extrair e confrontar | Produto no dossiê |
|---|---|---|
| Formação | proposta, aceite, assinatura, representação, anexos, condições | estado de formação com incertezas |
| Versões | minuta, aditivo, renovação, rescisão, vigência | diff de cláusulas e datas |
| Prestação | obrigação, condição, prazo, SLA, entrega, aceite | matriz parte versus obrigação |
| Financeiro | preço, reajuste, retenção, multa, juros, garantia | cronograma e valores rastreáveis |
| Descumprimento | evento alegado, notificação, cura, prova de entrega/pagamento | controvérsias e defesas |
| Risco | ambiguidade, lacuna, dependência, cláusula de foro/arbitragem | riscos e providências específicas |

O módulo usa [Código Civil](https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm) e legislação especial da espécie contratual, quando confirmada. Reajustes e multas só são calculados com cláusula vigente, base, índice, termo e período. O comparador deve preservar texto original da cláusula e posição no documento. Não concluir validade ou abusividade em abstrato sem relação material, legislação e fatos.

## 5. Tributário (`tax@1.0.0`)

### Matriz de questões

| Tema | Dados a extrair e confrontar | Produto no dossiê |
|---|---|---|
| Competência | ente, tributo, período, contribuinte, responsável | jurisdição e regime explícitos |
| Fato gerador | operação, data, local, classificação, base | premissas documentais e controvérsias |
| Lançamento | auto, declaração, notificação, ciência, impugnação | linha administrativa/processual |
| Crédito | principal, multa, juros, correção, pagamentos, compensações | quadro por competência e origem |
| Benefício/regime | opção, enquadramento, isenção, imunidade, alíquota | condições verificadas e pendências |
| Tempo | decadência, prescrição, suspensão, interrupção | análise condicionada aos marcos sustentados |
| Reforma | regimes de transição, tributos, períodos de produção de efeitos | regra temporal versionada |

Fonte federal inicial: [CTN](https://planalto.gov.br/ccivil_03/leis/l5172compilado.htm) e normas federais oficiais específicas. Quando o tributo depender de estado ou município, o catálogo deve localizar fonte normativa oficial do ente e recusar conclusão de alíquota/regime se ela não estiver disponível. A reforma tributária exige tabela de vigência e produção de efeitos por tributo e período; texto consolidado atual não substitui a regra aplicável ao fato pretérito.

Cálculos são por competência com base, alíquota, deduções, pagamentos, atualização e arredondamento auditáveis. Gate: nunca inferir crédito tributário definitivo de um auto isolado; não calcular prescrição ou decadência com marco e causa suspensiva desconhecidos; não usar alíquota de outro município/estado.

## 6. Administrativo (`administrative@1.0.0`)

### Matriz de questões

| Tema | Dados a extrair e confrontar | Produto no dossiê |
|---|---|---|
| Ente e agente | esfera, órgão, autoridade, delegação, interessado | mapa de competência |
| Ato | motivação, forma, objeto, publicação, ciência | controle de requisitos com fontes |
| Processo | requerimento, defesa, instrução, decisão, recurso | cronologia e pendências |
| Licitação | edital, critérios, propostas, habilitação, julgamento, recurso | comparação com regra do certame |
| Contrato público | matriz de riscos, execução, medição, aditivo, sanção | obrigações e eventos financeiros |
| Responsabilização | imputação, elemento subjetivo quando exigido, prova, defesa | questões bilaterais condicionadas |

Fontes iniciais: [Lei 14.133/2021](https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2021/lei/l14133.htm), normas do ente/órgão e edital/contrato do caso. O módulo registra qual regime legal rege o procedimento; não presume aplicação uniforme da lei federal a qualquer caso pretérito ou ente. Cálculos de reajuste, reequilíbrio e multa exigem cláusula, fato, período e índice verificáveis.

Gate: não tratar notícia, denúncia ou relatório preliminar como sanção final; não afirmar nulidade sem checar consequência e estágio; diferenciar decisão administrativa de decisão judicial.

## 7. Imobiliário (`real_estate@1.0.0`)

### Matriz de questões

| Tema | Dados a extrair e confrontar | Produto no dossiê |
|---|---|---|
| Imóvel | matrícula, endereço, área, descrição, unidade, cadastro | identidade e divergências do bem |
| Direito | propriedade, posse, promessa, usufruto, garantia, locação | linha de títulos e ocupação |
| Registro | atos, averbações, prenotações, ônus, certidões | estado registral com data da certidão |
| Negócio | preço, parcelas, entrega, escritura, financiamento | obrigações e pagamentos |
| Conflito | limites, benfeitorias, atraso, vício, inadimplemento, despejo | fatos, prova e alternativas |
| Urbanismo | uso, zoneamento, aprovação, regularização, condomínio | fonte municipal/registral e pendências |

Fontes iniciais: [Código Civil](https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm), [Lei de Registros Públicos](https://www.planalto.gov.br/ccivil_03/leis/l6015consolidado.htm) e normas especiais conforme o instrumento. Plantas, mapas e fotografias exibem recorte e página original, sem substituir perícia de área ou autenticidade. Cálculos de parcelas, mora ou rateio dependem de contrato, pagamentos e índices; área divergente não deve ser "corrigida" automaticamente pela imagem.

Gates: não inferir titularidade atual de matrícula antiga; diferenciar posse, domínio e direito obrigacional; não afirmar regularidade urbanística sem consulta ao ente competente.

## 8. Pesquisa e fonte normativa

Os cinco módulos terão catálogo de fontes autorizado por jurisdição e data. Cada regra aplicada registra `instrument_id`, `provision_id`, `jurisdiction`, `effective_from`, `effective_to`, `retrieved_at`, URL oficial, hash/versão quando disponível e trecho de suporte. O serviço bloqueia uso de fonte não recuperada, ambígua ou posterior ao fato como fundamento histórico confirmado. Precedentes requerem tribunal, processo/tema, data, status e pertinência ao caso.

Fonte local ausente gera limitação e pergunta ao advogado, não aplicação de regra federal aproximada. O usuário pode anexar norma ou decisão local, que continua como documento do caso até verificação da autenticidade e vigência.

## 9. Corpus, revisão e critérios de aceite

Cada módulo deve ter fixtures sintéticas/anonimizadas de caso completo, adverso, incompleto, multiarea, norma antiga e documento com tabela/imagem. Dois advogados da especialidade avaliam precisão factual, cobertura, correção temporal, pertinência de norma e utilidade da ação. Um caso de regressão deve combinar `contracts` + `tax` e outro `corporate` + `real_estate` para provar que o reconciliador não duplica fatos, partes, pedidos ou valores.

Critérios de aceite:

1. Cada questão aplicável possui conclusão condicionada ou estado justificado, com fontes e dados faltantes.
2. Versões de instrumento e alterações são comparáveis sem perder redação original.
3. Competência do ente, jurisdição e data são explícitas antes de aplicar regra.
4. Cálculos são reproduzíveis e separados dos valores alegados/documentados.
5. Documento visual relevante abre em imagem e página original; ausência ou falha de extração são distintas.
6. Caso multiarea mantém um único objeto por fato/pedido reconciliado e resultados específicos por módulo.
7. Falha de pesquisa oficial reduz o estado a `partial` ou `blocked`, preservando análise documental útil.
8. Cada artefato conserva versões de módulo e catálogo normativo; reanálise cria novo run.

## 10. Entrega ao DeepCode

Criar planos por módulo ou pares coesos: `contracts` + `corporate`, `tax`, `administrative` e `real_estate`. Cada pacote em `backend/app/modules/<module_id>/` contém schema adicional, checklist, regra de ativação, cálculos cadastrados, fontes autorizadas, corpus e gate próprio. A interface usa abas universais e mostra cartões especializados onde pertinentes. Habilitar por feature flag individual, com shadow runs e aprovação de advogados antes da liberação. Não alterar schema 3.0 silenciosamente; extensão incompatível exige nova versão formal.

## 11. Referências oficiais verificadas

- [Código Civil — Planalto](https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm)
- [Lei das S.A. — Planalto](https://www.planalto.gov.br/ccivil_03/leis/l6404consol.htm)
- [Lei 11.101/2005 — Planalto](https://www.planalto.gov.br/ccivil_03/_ato2004-2006/2005/lei/l11101compilado.htm)
- [CTN — Planalto](https://planalto.gov.br/ccivil_03/leis/l5172compilado.htm)
- [Lei 14.133/2021 — Planalto](https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2021/lei/l14133.htm)
- [Lei de Registros Públicos — Planalto](https://www.planalto.gov.br/ccivil_03/leis/l6015consolidado.htm)

O catálogo de produção deve consultar a redação vigente e a aplicável na data dos fatos, inclusive normas locais e regras de transição.
