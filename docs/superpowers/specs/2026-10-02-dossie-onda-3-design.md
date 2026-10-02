# SmartLawer — Dossiê Jurídico, Onda 3

**Status:** especificação de produto para revisão e planejamento pelo DeepCode

**Data:** 2 de outubro de 2026

**Módulos:** Penal/processo penal; Ambiental; Eleitoral; Constitucional; Propriedade intelectual; Proteção de dados.

## 1. Resultado e dependências

A Onda 3 amplia o [Dossiê Universal](2026-09-27-dossie-juridico-universal-design.md) para áreas com procedimentos, calendários e dados particularmente sensíveis. O contrato técnico é o schema 3.0 e o envelope `module_results` descrito na [Onda 1](2026-10-02-dossie-onda-1-design.md). A Onda 0 deve estar operacional; cada módulo desta onda pode ser liberado separadamente após avaliação própria.

O dossiê deve apresentar narrativa, fatos controvertidos, elementos favoráveis e adversos, fontes originais, prova existente versus alegada, regras verificadas na data correta, lacunas e próximos passos. Nenhum módulo decide culpa, autenticidade, constitucionalidade, infração ambiental, violação de dados ou resultado eleitoral automaticamente.

## 2. Controles comuns desta onda

- Registrar jurisdição, órgão, procedimento, fase, data do fato, data de ciência/publicação e data jurídica de referência.
- Versão de norma, resolução, regulamento, decisão e calendário acompanha cada análise. A norma atual não substitui automaticamente a vigente no passado.
- Evidência digital preserva arquivo original, hash, origem declarada, metadados disponíveis e eventuais lacunas de cadeia de custódia; a integridade não é presumida só pelo hash criado no upload.
- Fotografias, vídeos, imagens de satélite, prints e mapas são contextualizados com página/região e limites da interpretação; comparação visual não equivale a perícia.
- Dados de crianças, saúde, investigação e dados pessoais sensíveis recebem mascaramento, controle de acesso e registro de abertura/exportação.
- Prazo processual ou eleitoral só recebe data final quando a regra do procedimento, calendário, marco e eventos de suspensão/alteração estiverem verificados.
- Precedente tem tribunal, identificação, data, status, trecho e teste de pertinência; decisão isolada não é descrita como orientação vinculante.
- Saída sem base suficiente fica `partial` ou `blocked`, com diligência concreta.

## 3. Penal e processo penal (`criminal@1.0.0`)

### Matriz de questões

| Tema | Dados e confrontos | Saída útil |
|---|---|---|
| Imputação | fato narrado, conduta atribuída, tipo indicado, sujeito, tempo e lugar | mapa de imputações por pessoa, sem atribuir culpa |
| Procedimento | notícia, investigação, denúncia/queixa, recebimento, instrução, decisão, recurso | fase e atos com fontes |
| Materialidade/autoria | laudos, objetos, depoimentos, reconhecimentos, registros digitais | matriz de suporte e contradição |
| Licitude da prova | obtenção, autorização, cadeia de custódia, integridade, impugnação | questões para revisão humana |
| Medidas cautelares | fundamento invocado, decisão, revisão, condições e datas | alerta de urgência e documentos faltantes |
| Tipicidade e defesa | elementos do tipo, dolo/culpa quando cabível, excludentes alegadas | teses bilaterais condicionadas |
| Tempo e pena | marcos, regime legal temporal, decisões, execução | cálculo apenas com dados jurídicos validados |

Fontes iniciais: [Código Penal](https://planalto.gov.br/ccivil_03/decreto-lei/del2848compilado.htm), [Código de Processo Penal](https://www.planalto.gov.br/ccivil_03/decreto-lei/del3689compilado.htm), Constituição e lei especial pertinente. Distinguir fato da imputação, denúncia recebida, acusação provada e sentença. Não criar score de culpa ou risco de condenação. Prazo, prescrição, dosimetria e pena exigem conferência profissional obrigatória; sem conjunto completo, mostrar apenas parâmetros e lacunas.

Gate: nunca afirmar autoria por reconhecimento fotográfico ou print isolado; nunca transcrever dados sigilosos em logs ou resumos públicos; inconsistência na cadeia de custódia gera questão, não nulidade automática.

## 4. Ambiental (`environmental@1.0.0`)

### Matriz de questões

| Tema | Dados e confrontos | Saída útil |
|---|---|---|
| Local e atividade | imóvel, coordenadas, bioma, atividade, licença, período | mapa documental com precisão e fonte |
| Impacto | evento, área, substância, medição, laudo, dano alegado | matriz de evidência e incerteza |
| Licenciamento | requerimento, condicionantes, validade, fiscalização, renovação | linha temporal de obrigações |
| Responsabilidades | pessoa física/jurídica, conduta, nexo, esfera civil/administrativa/penal | questões separadas por esfera |
| Remediação | plano, custo, execução, monitoramento, resultados | ações e prova de cumprimento |
| Sanção | auto, defesa, decisão, recurso, multa, embargo | estado processual verificado |

Fontes iniciais: [Política Nacional do Meio Ambiente](https://www.planalto.gov.br/ccivil_03/leis/l6938compilada.htm), [Lei 9.605/1998](https://planalto.gov.br/ccivil_03/leis/l9605.htm), normas oficiais do ente licenciador e da atividade. Mapas, imagens de satélite e fotografias preservam data, resolução e origem declaradas; o sistema não identifica desmatamento, área ou causalidade como conclusão pericial. Cálculo de multa e custo de reparação exige auto, metodologia, unidade, período e norma aplicável.

Gate: não confundir licença vencida com inexistente sem verificar renovação e regime; não somar sanções de esferas distintas como uma dívida única; não afirmar autoria do dano apenas por titularidade do imóvel.

## 5. Eleitoral (`electoral@1.0.0`)

### Matriz de questões

| Tema | Dados e confrontos | Saída útil |
|---|---|---|
| Pleito | ano, cargo, circunscrição, turno, fase | calendário e regras específicas |
| Sujeitos | partido, federação, candidatura, eleitor, órgão | papéis e legitimidade condicionada |
| Propaganda | peça, canal, data, impulsionamento, autoria alegada | matriz de conteúdo, veiculação e fonte |
| Registro | requisitos, documentos, decisões, impugnações | pendências por fase |
| Contas | receita, despesa, fonte, comprovantes, prestação | conciliação sem valor inferido |
| Ilícitos | fato imputado, elemento exigido, prova, contraponto | avaliação bilateral e cautelosa |
| Prazos | publicação/intimação, calendário, resolução e rito | prazo calculável somente se todos os marcos existirem |

Fontes iniciais: [Lei 9.504/1997](https://www.planalto.gov.br/ccivil_03/leis/l9504compilado.htm), Código Eleitoral e resoluções oficiais do TSE correspondentes ao pleito. O [portal de normas de 2026 do TSE](https://www.tse.jus.br/eleicoes/eleicoes-2026-content/normas-e-documentacoes/normas-e-documentacoes-eleicoes-2026) e a [Resolução 23.760/2026](https://www.tse.jus.br/legislacao/compilada/res/2026/resolucao-no-23-760-de-2-de-marco-de-2026) demonstram que calendário e regras precisam ser selecionados pelo ano do pleito. O módulo não transporta o calendário de 2026 para outro ano.

Gate: sem pleito, fase e ato de ciência confirmados, prazo fica `blocked`; print de rede social não prova sozinho autoria, alcance ou patrocínio; não misturar regras de eleições municipais e gerais.

## 6. Constitucional (`constitutional@1.0.0`)

### Matriz de questões

| Tema | Dados e confrontos | Saída útil |
|---|---|---|
| Norma/ato | texto impugnado, ente, hierarquia, vigência, efeitos | objeto preciso da controvérsia |
| Parâmetro | dispositivo constitucional, princípio, direito, competência | parâmetro com redação temporal |
| Via | controle difuso/concentrado, legitimidade, competência, subsidiariedade | hipóteses processuais condicionadas |
| Precedentes | tese, ratio, alcance, modulação, status | pertinência e limites |
| Impacto | pessoas, efeitos administrativos/financeiros, transição | cenários sem projeção inventada |

Fonte inicial: texto constitucional atualizado em portal legislativo oficial, com histórico de emendas, e precedentes oficiais de STF/STJ conforme competência. O módulo separa argumento constitucional da conclusão sobre validade da norma. Não afirma inconstitucionalidade porque uma petição a alegou, nem trata precedente revogado/superado como vigente. Efeitos e modulação só são descritos quando constarem da decisão verificada.

## 7. Propriedade intelectual (`intellectual_property@1.0.0`)

### Matriz de questões

| Tema | Dados e confrontos | Saída útil |
|---|---|---|
| Objeto | obra, marca, patente, desenho, segredo, software, domínio | classificação e limites |
| Titularidade | criação, cessão, licença, vínculo, registro, território | cadeia documental de direitos |
| Vigência | depósito, concessão, renovação, prazo, extensão territorial | estado condicionado a fonte oficial |
| Uso | reprodução, distribuição, sinal distintivo, licença, exceção alegada | comparação de atos e permissões |
| Conflito | anterioridade, semelhança alegada, confundibilidade, contrafação | questões para perícia/revisão |
| Valores | royalties, remuneração, perdas alegadas, contratos | cenários com base contratual comprovada |

Fontes iniciais: [Lei 9.279/1996](https://www.planalto.gov.br/ccivil_03/leis/l9279.htm), [Lei 9.610/1998](https://planalto.gov.br/ccivil_03/leis/l9610.htm), bases oficiais de registro quando a consulta estiver autorizada. Imagens de marcas ou obras podem ser comparadas visualmente como indícios, nunca como conclusão automática de cópia, confundibilidade ou titularidade. Segredo empresarial exige controles de acesso mais restritos e não deve ser enviado a pesquisa externa.

Gate: distinguir direito autoral de registro industrial; não afirmar validade atual de título sem consulta oficial; não concluir infração só por semelhança visual.

## 8. Proteção de dados (`data_protection@1.0.0`)

### Matriz de questões

| Tema | Dados e confrontos | Saída útil |
|---|---|---|
| Agentes | controlador, operador, encarregado, terceiro, titular | papéis alegados e documentados |
| Tratamento | categoria de dado, finalidade, operação, fluxo, compartilhamento | mapa de tratamento e fontes |
| Base e direitos | base legal invocada, informação, pedido de titular, resposta | lacunas e controvérsias |
| Segurança | incidente alegado, vetor, evidência, contenção, impacto | cronologia com incertezas |
| Transferência | destino, instrumento, salvaguardas, data | avaliação temporal e regulatória |
| Governança | contratos, políticas, RIPD, registros, medidas | evidência examinada versus declarada |

Fontes iniciais: [LGPD](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709compilado.htm) e [regulamentações oficiais da ANPD](https://www.gov.br/anpd/pt-br/acesso-a-informacao/institucional/atos-normativos/regulamentacoes_anpd). O catálogo regulatório deve ser sincronizado e versionado; a lista da ANPD inclui atos posteriores à LGPD, de modo que a análise deve aplicar a regra vigente no evento. O módulo separa incidente relatado, incidente confirmado e dano demonstrado. Não conclui obrigação de notificação ou sanção sem critérios e datas verificados.

Gate: consultas externas recebem dados minimizados; dado sensível não aparece em telemetria; exportação respeita mascaramento e autorização do caso; um print de aviso não prova que todos os titulares foram notificados.

## 9. Pesquisa e cálculos especializados

Cada módulo especifica fonte oficial, jurisdição e data de aplicação. Para fontes variáveis por pleito, órgão ou ente, o pipeline persiste a versão recuperada e sua URL. Falha de acesso não é substituída por memória do modelo. O motor de cálculos só executa fórmulas cadastradas e revisadas: pena, prescrição, multa, dano, royalty, prazo eleitoral ou valor regulatório não são calculados genericamente. O relatório mostra entradas faltantes e responsável pela validação.

## 10. Corpus e avaliação jurídica

Cada módulo terá ao menos seis fixtures sintéticas/anonimizadas: caso completo, caso adverso, falta de prova, norma temporalmente alterada, imagem/print ambíguo e caso multiarea. Acrescentar:

- penal: investigação versus sentença e prova digital com cadeia incompleta;
- ambiental: licença antiga, satélite sem metadados e sanções em esferas diferentes;
- eleitoral: dois pleitos distintos e intimação sem data;
- constitucional: precedente com modulação e precedente não vinculante;
- propriedade intelectual: título vencido e obras visualmente semelhantes com cadeia de titularidade ausente;
- proteção de dados: incidente alegado sem confirmação e transferência internacional sob atos de datas distintas.

Dois revisores da área avaliam cobertura, precisão, pertinência da norma, cautela com incerteza, proteção de dados e utilidade. Divergência vira item de calibração do corpus, não aprovação automática.

## 11. Critérios de aceite

1. Cada questão aplicável tem fonte e conclusão condicionada ou estado justificado com ação.
2. Calendário, jurisdição, órgão, rito e vigência correspondem ao caso; dados ausentes bloqueiam prazo ou conclusão dependente.
3. Artefato separa imputação, alegação, prova, decisão e conclusão do sistema.
4. Evidência visual/digital preserva origem, hash disponível, metadados, página/região e limites de autenticidade.
5. Dados sensíveis são mascarados no resumo e protegidos no acesso, exportação e logs.
6. Cálculo somente usa regra versionada e parâmetros documentados.
7. Multiarea preserva objetos comuns sem duplicação e resultado especializado por módulo.
8. Artefato anterior conserva versões das fontes e módulos; reanálise gera novo run.
9. Queda de fonte externa gera análise documental parcial e pendência, sem autoridade inventada.
10. Advogados revisores aprovam corpus e casos adversariais antes da liberação do módulo.

## 12. Entrega ao DeepCode

Criar planos individuais para `criminal`, `environmental`, `electoral`, `constitutional`, `intellectual_property` e `data_protection`. Cada pacote em `backend/app/modules/<module_id>/` conterá contrato, checklist, ativação, fontes autorizadas, regras temporais, corpus, gate e componentes de apresentação sobre as abas universais. Feature flag e rollout são individuais. O módulo penal exige revisão de segurança e jurídica antes de uso externo; eleitoral exige revisão do calendário por pleito; proteção de dados exige revisão de privacidade e minimização. A Onda 0 permanece como fallback útil enquanto um módulo especializado estiver indisponível.

## 13. Referências oficiais verificadas

- [Código Penal — Planalto](https://planalto.gov.br/ccivil_03/decreto-lei/del2848compilado.htm)
- [Código de Processo Penal — Planalto](https://www.planalto.gov.br/ccivil_03/decreto-lei/del3689compilado.htm)
- [Política Nacional do Meio Ambiente — Planalto](https://www.planalto.gov.br/ccivil_03/leis/l6938compilada.htm)
- [Lei de Crimes Ambientais — Planalto](https://planalto.gov.br/ccivil_03/leis/l9605.htm)
- [Lei das Eleições — Planalto](https://www.planalto.gov.br/ccivil_03/leis/l9504compilado.htm)
- [Normas do pleito 2026 — TSE](https://www.tse.jus.br/eleicoes/eleicoes-2026-content/normas-e-documentacoes/normas-e-documentacoes-eleicoes-2026)
- [Lei de Propriedade Industrial — Planalto](https://www.planalto.gov.br/ccivil_03/leis/l9279.htm)
- [Lei de Direitos Autorais — Planalto](https://planalto.gov.br/ccivil_03/leis/l9610.htm)
- [LGPD — Planalto](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709compilado.htm)
- [Regulamentações — ANPD](https://www.gov.br/anpd/pt-br/acesso-a-informacao/institucional/atos-normativos/regulamentacoes_anpd)

As referências são ponto de partida do catálogo oficial; cada execução verifica texto, vigência, alcance e alterações pertinentes à data do caso.
