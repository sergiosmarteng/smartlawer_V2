# SmartLawer — Especificação do Dossiê Jurídico Universal V2

**Versão:** 1.0

**Data:** 27 de setembro de 2026

**Status:** especificação aprovada para planejamento e implementação

**Público:** produto, engenharia, design, QA, segurança e advogados revisores

**Executor previsto:** DeepCode ou equipe de implementação equivalente

## 1. Objetivo

Implementar um Dossiê Jurídico Universal que transforme um ou mais documentos de um caso em uma análise estruturada, verificável, útil e navegável para advogados de qualquer área do Direito.

O dossiê deve responder, com fontes localizáveis:

- quem participa do caso e em qual papel;
- o que aconteceu e em que ordem;
- o que cada parte afirma, pede e contesta;
- quais provas existem, foram apenas mencionadas ou ainda precisam ser produzidas;
- quais normas, precedentes e cláusulas são relevantes;
- quais teses favorecem e desfavorecem cada polo;
- quais riscos, valores, prazos, lacunas e contradições existem;
- quais providências devem ser tomadas e em qual prioridade;
- quais conclusões dependem de validação humana.

A primeira entrega deve conter um núcleo universal aplicável a todas as áreas. Especializações serão adicionadas em ondas por meio de módulos versionados. A ausência de módulo especializado nunca poderá produzir uma tela vazia: o sistema deverá entregar a análise universal e declarar explicitamente os limites da especialização disponível.

## 2. Definição de sucesso

O recurso estará bem implementado quando um advogado conseguir:

1. compreender o caso pela visão executiva sem reler inicialmente todos os arquivos;
2. abrir a fonte de qualquer afirmação material na página e, quando possível, na região exata;
3. distinguir alegação, prova, inferência, fato admitido, fato controvertido e dado desconhecido;
4. conferir a cobertura dos documentos, páginas, pedidos e seções;
5. identificar lacunas, contradições, riscos e providências prioritárias;
6. revisar, corrigir, aprovar, comparar e exportar versões do dossiê;
7. utilizar imagens, tabelas e outros elementos visuais como evidências contextualizadas;
8. receber um estado honesto de falha ou parcialidade quando o sistema não puder produzir conteúdo confiável.

Não é sucesso produzir texto longo, repetir pedidos em abas diferentes ou preencher campos com conteúdo genérico. Profundidade significa cobertura verificável e utilidade para decisão, não volume artificial.

## 3. Diagnóstico da implementação atual

### 3.1 Sintoma reproduzido

No dossiê associado ao documento `22741f40-11e6-40ef-8f93-c0f8196e70bd`, a aba Pedidos apresenta seis itens e as demais abas ficam vazias. O cabeçalho informa `páginas: 0/0`, `estado completed` e `andamento: 100% (extraction)`. Os pedidos aparecem sem fontes, com `refs: a confirmar`.

### 3.2 Causa raiz confirmada no código

O problema não é apenas de renderização. O artefato V2 publicado já contém quase somente pedidos:

1. `backend/app/tasks/document_tasks.py` executa `LegalAnalyzer.analyze_petition()` usando o contrato legado.
2. O resultado legado é entregue a `coerce_legacy_analysis()`.
3. `backend/app/core/schemas_v2.py::coerce_legacy_analysis()` converte apenas `requests` em `claims`.
4. O mesmo método cria `ArtifactContent` com `facts`, `evidence`, `legal_references`, `theses`, `calculations`, `risks` e `sources` vazios.
5. A cobertura não recebe as páginas inventariadas e permanece `0/0`.
6. O frontend `src/pages/analysis/v2/[id].tsx` exibe fielmente esses arrays vazios.

Logo, a aba Pedidos funciona porque é a única seção populada pela ponte legada. As demais não possuem dados para exibir.

### 3.3 Defeitos correlatos

- A task denomina a execução como pipeline V2, mas publica uma coerção do resultado V1.
- O inventário de páginas é executado em modo `best-effort` e sua falha não impede a publicação.
- O processamento pode marcar o documento legado como concluído antes de publicar e validar o artefato V2.
- O run pode terminar com estágio de extração mesmo com progresso apresentado como 100%.
- O caminho normal não executa extração estruturada, reconciliação, análise temática, pesquisa, cálculo e composição.
- `coerce_legacy_analysis()` adiciona a limitação correta, mas o fluxo ainda permite ao usuário interpretar o resultado como dossiê final.
- Fontes não são criadas para os pedidos convertidos.
- A extração de figuras existente não é ligada semanticamente ao artefato, aos fatos ou às provas.
- Estados vazios do frontend não explicam de forma consistente se algo é inaplicável, ausente, bloqueado ou não processado.

### 3.4 Decisão obrigatória

`coerce_legacy_analysis()` permanecerá apenas para leitura/migração de análises antigas. É proibido utilizá-lo como produtor do novo Dossiê Universal.

## 4. Escopo

### 4.1 Incluído

- Casos com um ou vários documentos.
- PDFs digitais ou digitalizados, imagens e documentos convertíveis pelo pipeline já suportado.
- Núcleo universal para todas as áreas jurídicas.
- Classificação multirrótulo de áreas e subáreas.
- Extração integral por página, bloco, tabela e imagem.
- Dossiê com identificação, partes, cronologia, pedidos, fatos, controvérsias, provas, imagens, fundamentos, questões processuais, teses, riscos, cálculos, estratégia, ações, lacunas, fontes e revisão.
- Módulos jurídicos especializados versionados e ativados por classificação.
- Pesquisa jurídica com fontes autorizadas e verificáveis.
- Revisão humana, histórico, comparação e exportação.
- Observabilidade, segurança, autorização e proteção de dados.
- Migração e reprocessamento controlado de análises antigas.

### 4.2 Fora do escopo inicial

- Protocolar petições ou realizar atos processuais automaticamente.
- Prometer êxito, probabilidade de vitória ou substituir a decisão profissional.
- Diagnóstico médico, perícia, autenticação forense ou confirmação de autoria por imagem.
- Acesso a processos ou bases externas sem autorização e integração explícita.
- Treinamento de modelos com documentos de clientes sem consentimento específico.
- Implementação integral simultânea de todas as especializações jurídicas.
- Substituição automática do documento original por texto reconstruído.

## 5. Princípios jurídicos e epistêmicos

### 5.1 Alegação não é prova

Toda proposição deve registrar quem a afirmou, onde foi localizada, seu estado epistêmico e quais evidências a sustentam ou contradizem.

Estados mínimos:

- `alleged`: alegado por uma parte;
- `documented`: sustentado por documento examinado;
- `admitted`: admitido por parte identificada;
- `disputed`: controvertido;
- `inferred`: inferência explicitamente marcada;
- `unknown`: não determinado.

### 5.2 Ausência no conjunto não significa inexistência

O sistema dirá “não localizado nos documentos examinados”. Só afirmará inexistência quando houver fonte apta a sustentar essa conclusão.

### 5.3 Citação deve sustentar a proposição

Uma referência existente, porém irrelevante, não valida uma afirmação. O suporte terá estado `matched`, `partial`, `insufficient`, `contradictory` ou `unverified`.

### 5.4 Análise bilateral

Mesmo quando o polo for informado, o dossiê deverá apresentar elementos favoráveis e adversos. Não poderá operar como gerador automático de confirmação da estratégia escolhida.

### 5.5 Incerteza descritiva

Scores técnicos deverão identificar sua dimensão e fórmula. Confiança de extração não poderá ser convertida em probabilidade de vitória.

## 6. Experiência do usuário

### 6.1 Criação da análise

Antes do processamento, o usuário poderá informar ou confirmar:

- caso existente ou novo caso;
- documentos integrantes;
- polo representado: autor/requerente, réu/requerido, terceiro ou neutro;
- objetivo da análise;
- data jurídica de referência;
- áreas sugeridas;
- nível de urgência e idioma.

O sistema poderá sugerir valores, mas não ocultará a possibilidade de correção.

### 6.2 Cabeçalho do dossiê

O cabeçalho exibirá:

- nome ou identificação do caso;
- área principal e áreas relacionadas;
- tipo de procedimento e fase, quando conhecidos;
- polo e objetivo;
- versão do artefato e dos módulos;
- estado da execução e da revisão;
- cobertura de documentos, páginas e blocos;
- data da análise e data jurídica de referência;
- avisos críticos e ações principais;
- comandos de reanálise, comparação e exportação.

### 6.3 Abas obrigatórias

#### 6.3.1 Visão geral

- narrativa específica do caso;
- questão central;
- pedidos centrais;
- exposição econômica conhecida;
- fatos determinantes;
- provas mais relevantes;
- fundamentos principais;
- teses mais fortes e mais frágeis;
- riscos prioritários;
- ações recomendadas;
- cobertura, limitações e pendências.

#### 6.3.2 Partes

- pessoas, empresas, órgãos e terceiros;
- papéis materiais e processuais;
- representantes e advogados;
- relações entre entidades;
- identificadores mascarados quando necessário;
- divergências de nome, papel ou qualificação;
- fontes de cada informação.

#### 6.3.3 Cronologia

- eventos ordenados por data;
- distinção entre data do fato, emissão, protocolo, ciência, publicação e prazo;
- intervalo quando a data for aproximada;
- eventos conflitantes sem resolução silenciosa;
- filtros por parte, pedido, documento e categoria;
- fonte e estado epistêmico.

#### 6.3.4 Pedidos

Cada pedido ou subpedido terá:

- número original e identificador estável;
- requerente e destinatário;
- título e providência requerida;
- fundamento fático e jurídico;
- valor literal e normalizado;
- período e recorrência;
- relações `alternate`, `subsidiary`, `cumulative`, `overlaps` ou `procedural_accessory`;
- contestação, admissão ou ausência de manifestação;
- provas relacionadas;
- riscos, teses e cálculos relacionados;
- todas as ocorrências e fontes.

#### 6.3.5 Fatos e controvérsias

- proposição factual;
- autor da afirmação;
- estado epistêmico;
- fontes de suporte e oposição;
- relação com pedidos e teses;
- conflitos e dados faltantes;
- impacto jurídico provável, sem converter inferência em fato.

#### 6.3.6 Provas e imagens

- prova documental, testemunhal, pericial, digital, material ou pretendida;
- estado `examined`, `mentioned_not_located`, `proposed` ou `unavailable`;
- proposições sustentadas ou enfraquecidas;
- autenticidade ou integridade quando verificável;
- limitações e diligência recomendada;
- imagens relacionadas, com miniatura, ampliação e acesso à página original;
- matriz pedido/fato/tese versus prova.

#### 6.3.7 Direito

- normas, precedentes, súmulas, atos administrativos e cláusulas contratuais;
- separação entre material citado no processo e pesquisado pelo sistema;
- citação literal, normalização, vigência e data de consulta;
- tribunal, órgão, número, relator e data quando aplicáveis;
- trecho relevante e pertinência ao caso;
- status de verificação e fonte oficial.

#### 6.3.8 Questões processuais

- competência;
- legitimidade e interesse;
- requisitos da peça;
- prescrição, decadência, preclusão e prazos;
- distribuição do ônus probatório;
- tutelas, recursos, incidentes e pressupostos aplicáveis;
- fatos e datas necessários para concluir cada item;
- conclusão condicionada e fonte.

#### 6.3.9 Teses

Cada tese terá:

- polo;
- questão jurídica;
- conclusão condicionada;
- premissas factuais e jurídicas;
- provas favoráveis e adversas;
- contraponto provável;
- pré-requisitos;
- provas ou pesquisa adicionais;
- ação recomendada;
- limitações;
- fontes.

Teses genéricas não poderão ser injetadas para aparentar conteúdo.

#### 6.3.10 Cálculos

- valores extraídos;
- fórmula e versão;
- entradas, unidades e datas;
- índices, juros, correção e arredondamento;
- premissas e cenários;
- resultado reproduzível;
- divergências entre valores;
- parcelas não quantificadas e motivo.

#### 6.3.11 Estratégia, riscos e ações

- riscos jurídicos, probatórios, processuais, financeiros e operacionais;
- impacto e incerteza;
- mitigação;
- plano priorizado de providências;
- perguntas ao cliente;
- documentos e provas a obter;
- quesitos e perguntas para audiência;
- responsável, prazo sugerido e dependências;
- ligação com fatos, pedidos e fontes.

#### 6.3.12 Revisão

- status da revisão;
- pendências do verificador;
- correções e justificativas;
- autoria e data;
- comparação antes/depois;
- histórico de versões;
- aprovação ou rejeição por usuário autorizado.

### 6.4 Estado obrigatório de cada seção

Todas as seções terão:

```json
{
  "status": "complete | partial | blocked | not_applicable",
  "reason": "explicação obrigatória",
  "coverage": {
    "items_expected": null,
    "items_found": 0,
    "items_verified": 0
  },
  "pending_actions": []
}
```

Um array vazio sem metadados de estado será inválido.

## 7. Imagens como evidência de primeira classe

### 7.1 Tipos tratados

- fotografias;
- capturas de tela;
- plantas, croquis, mapas e diagramas;
- gráficos;
- tabelas renderizadas;
- comprovantes e recibos;
- assinaturas, rubricas, carimbos e selos;
- códigos, etiquetas e elementos gráficos;
- página completa quando o contexto espacial for necessário.

### 7.2 Objeto visual

```json
{
  "id": "visual-uuid",
  "document_id": "uuid",
  "revision_id": "uuid",
  "page_number": 5,
  "region": {"x": 0.10, "y": 0.20, "width": 0.60, "height": 0.40},
  "kind": "photo | screenshot | diagram | table | signature | stamp | page | other",
  "status": "examined | unresolved | irrelevant | extraction_failed",
  "storage_key": "opaque-key",
  "thumbnail_key": "opaque-key",
  "caption_original": null,
  "description": "descrição cautelosa",
  "relevance": "por que pode importar ao caso",
  "sensitivity": ["personal_data"],
  "quality": {"resolution": "adequate", "rotation": 0, "cropped": false},
  "related_fact_ids": [],
  "related_claim_ids": [],
  "related_evidence_ids": [],
  "related_thesis_ids": [],
  "source_ref": "source-uuid"
}
```

### 7.3 Regras

- A página original deverá permanecer disponível para preservar contexto.
- Coordenadas usarão sistema normalizado e rotação explícita.
- Uma figura isolada não substituirá a página quando setas, legendas ou relações espaciais ficarem fora do recorte.
- O sistema não concluirá identidade, autenticidade, autoria, data, causalidade, incapacidade médica ou ocorrência do fato somente a partir da imagem.
- Anotações e legendas produzidas por uma parte serão tratadas como alegações.
- Conteúdo sensível poderá ser ocultado por padrão e revelado por ação do usuário.
- Falha de extração não poderá ser exibida como “documento sem imagens”.
- Imagens relevantes aparecerão nas seções relacionadas; todas as imagens ficarão disponíveis em galeria pesquisável.

### 7.4 Integração com código existente

Reutilizar e evoluir:

- `backend/app/models/document_figure.py`;
- extração por Docling/PyMuPDF em `backend/app/tasks/document_tasks.py`;
- inventário visual de `backend/app/core/extraction.py`;
- armazenamento seguro existente.

Adicionar ligação semântica entre `DocumentFigure`, `SourceReference` e os IDs do artefato. Não criar um segundo catálogo visual concorrente.

## 8. Arquitetura do pipeline

```text
ingresso seguro
  -> inventário e extração por revisão
  -> classificação multirrótulo
  -> planejamento de cobertura
  -> extração estruturada por lotes
  -> reconciliação global
  -> seleção de módulos jurídicos
  -> análise jurídica temática
  -> pesquisa jurídica
  -> cálculos determinísticos
  -> verificação
  -> composição
  -> publicação atômica
  -> revisão, comparação e exportação
```

### 8.1 IngestionService

Valida tipo real, tamanho, integridade, criptografia, duplicidade e autorização; calcula hash; cria revisão imutável e registra o arquivo no caso.

### 8.2 ExtractionService

Produz páginas, blocos, tabelas, imagens e diagnósticos. Mantém texto original, texto normalizado, offsets, ordem de leitura, coordenadas, rotação, método e qualidade.

OCR será decidido por cobertura espacial, presença de imagens e qualidade do corpo, não somente por quantidade total de caracteres.

### 8.3 ClassificationService

Retorna área principal, áreas relacionadas, tipos de documento, procedimento, fase e confiança técnica. Suporta correção humana e classificação multirrótulo.

### 8.4 CoveragePlanner

Divide o conteúdo por estrutura e orçamento, mantendo IDs dos blocos. Todo bloco deverá aparecer em um lote ou em `unprocessed_block_ids`. Sobreposição será explícita para permitir deduplicação.

### 8.5 StructuredExtractor

Extrai objetos estruturados sem decidir mérito: entidades, partes, eventos, pedidos, fatos, provas, imagens, referências, valores, datas, prazos e relações.

### 8.6 Reconciler

Une repetições, preserva ocorrências, registra conflitos e impede que a primeira versão apague versões divergentes.

### 8.7 LegalModuleRegistry

Seleciona o núcleo universal e zero ou mais módulos especializados. Cada módulo declara:

```python
module_id: str
version: str
supported_areas: list[str]
document_types: list[str]
required_sections: list[str]
issue_checklists: list[str]
calculation_rules: list[str]
research_sources: list[str]
evaluation_cases: list[str]
```

### 8.8 UniversalLegalAnalyzer

Analisa questões transversais usando somente objetos reconciliados e fontes registradas. Produz questões processuais, teses bilaterais, riscos, lacunas, perguntas e ações.

### 8.9 LegalResearchService

Consulta fontes autorizadas, registra consulta, versão, data, metadados e trecho. Se indisponível, preserva a análise documental e marca a pesquisa como bloqueada ou parcial.

### 8.10 CalculationService

Executa fórmulas versionadas com `Decimal`, datas e parâmetros explícitos. A IA poderá sugerir uma regra cadastrada, mas não executar aritmética jurídica livre como resultado final.

### 8.11 AnalysisVerifier

Verifica estrutura, cobertura, fontes, suporte, consistência, cálculos, datas, estados vazios e requisitos dos módulos. Um reparo automático poderá corrigir estrutura, mas nunca inventar fatos, fontes ou valores.

### 8.12 ReportComposer

Compõe a visão executiva e as abas exclusivamente a partir dos objetos validados. Não gera uma segunda interpretação livre capaz de divergir do artefato.

### 8.13 ReviewService e ExportService

Registram correções imutáveis, versões, aprovação e relatórios reproduzíveis.

## 9. Estados do processamento

### 9.1 Execução

- `queued`
- `running`
- `blocked`
- `partial`
- `completed`
- `failed`
- `cancelled`

### 9.2 Publicação

- `completed`: conteúdo útil e verificações materiais aprovadas;
- `partial`: conteúdo útil com lacunas declaradas;
- `blocked`: publicação aguardando requisito indispensável;
- `failed`: conteúdo confiável insuficiente; nenhum dossiê final é publicado.

### 9.3 Regras de transição

- Falha de provedor, parsing, OCR, pesquisa ou cálculo nunca vira `completed` automaticamente.
- Conclusão do documento legado não antecederá a decisão do artefato V2.
- O estágio persistido deverá avançar monotonicamente ou registrar retomada.
- Cancelamento impedirá publicação tardia.
- A publicação será atômica e idempotente.
- Um run concluído deverá terminar em `composition`/`publication`, nunca em `extraction`.

## 10. Modelo de dados

### 10.1 Entidades persistidas

- `Case`: agrupador do assunto jurídico.
- `CaseDocument`: associação documento/caso e seu papel.
- `DocumentRevision`: conteúdo imutável identificado por hash.
- `SourceBlock`: bloco textual, tabular ou visual localizável.
- `DocumentFigure`: imagem ou região visual extraída.
- `AnalysisRun`: snapshot de entrada, configuração, módulos e estado.
- `AnalysisStageRun`: telemetria e retomada por estágio.
- `AnalysisArtifact`: conteúdo JSON publicado, hash e versões.
- `SourceReference`: referência resolvível a documento, página, bloco, região ou fonte externa.
- `LegalResearchResult`: fonte externa consultada e verificada.
- `CalculationResult`: fórmula, entradas e saída determinística.
- `ReviewEvent`: correção, autoria e versão esperada.

### 10.2 Conteúdo do artefato

Evoluir `ArtifactContent` para incluir:

```python
class ArtifactContent(BaseModel):
    schema_version: Literal["3.0"]
    run_id: str
    case_id: str
    status: ArtifactStatus
    review_status: ReviewStatus
    scope: AnalysisScope
    module_activations: list[ModuleActivation]
    coverage: Coverage
    section_states: dict[SectionName, SectionState]
    executive_summary: ExecutiveSummary
    parties: list[Party]
    events: list[TimelineEvent]
    claims: list[Claim]
    facts: list[Fact]
    controversies: list[Controversy]
    evidence: list[EvidenceItem]
    visuals: list[VisualEvidence]
    legal_references: list[LegalReference]
    procedural_issues: list[ProceduralIssue]
    theses: list[Thesis]
    calculations: list[Calculation]
    risks: list[Risk]
    action_plan: list[ActionItem]
    client_questions: list[ClientQuestion]
    sources: list[SourceRef]
    limitations: list[Limitation]
```

Os schemas deverão ser Pydantic no backend e gerar ou validar tipos equivalentes no frontend. Campos obrigatórios não poderão depender de coerção silenciosa.

### 10.3 Invariantes

- IDs internos únicos no artefato.
- Toda referência interna aponta para objeto existente.
- Toda afirmação material tem fonte ou limitação.
- Páginas estão dentro da revisão referenciada.
- Regiões têm coordenadas entre 0 e 1.
- Valores monetários normalizados usam string decimal e moeda.
- Datas incertas preservam literal e precisão.
- Pedido explícito contado deve possuir objeto correspondente.
- Cada seção possui `SectionState`.
- `completed` exige cobertura integral conforme regras do núcleo e módulos.
- Fonte externa não substitui a fonte documental do fato.

## 11. API

### 11.1 Casos e documentos

- `POST /api/v2/cases`
- `GET /api/v2/cases/{case_id}`
- `POST /api/v2/cases/{case_id}/documents`
- `GET /api/v2/cases/{case_id}/documents`

### 11.2 Execuções

- `POST /api/v2/analysis-runs`
- `GET /api/v2/analysis-runs?case_id=&document_id=`
- `GET /api/v2/analysis-runs/{run_id}`
- `POST /api/v2/analysis-runs/{run_id}/cancel`
- `POST /api/v2/analysis-runs/{run_id}/resume`

Criação recebe snapshot explícito:

```json
{
  "case_id": "uuid",
  "document_ids": ["uuid"],
  "represented_side": "claimant | respondent | third_party | neutral",
  "objective": "texto",
  "reference_date": "2026-09-27",
  "area_overrides": [],
  "idempotency_key": "client-key"
}
```

### 11.3 Artefatos

- `GET /api/v2/analyses/{artifact_id}`
- `GET /api/v2/analyses/{artifact_id}/sections/{section}`
- `GET /api/v2/analyses/{artifact_id}/sources`
- `GET /api/v2/analyses/{artifact_id}/visuals`
- `GET /api/v2/analyses/{artifact_id}/versions`
- `GET /api/v2/analyses/{artifact_id}/compare?against=`
- `POST /api/v2/analyses/{artifact_id}/reanalyze`

Listas grandes terão paginação, filtros e ordenação. Artefatos usarão ETag.

### 11.4 Fontes e imagens

- `GET /api/v2/sources/{source_id}`
- `GET /api/v2/visuals/{visual_id}`
- `GET /api/v2/visuals/{visual_id}/thumbnail`
- `GET /api/v2/document-revisions/{revision_id}/pages/{page_number}/render`

Todos os endpoints validarão organização, usuário, caso, documento e revisão. URLs de armazenamento serão temporárias e não exporão caminhos internos.

### 11.5 Revisão e exportação

- `POST /api/v2/analyses/{artifact_id}/review-events`
- `GET /api/v2/analyses/{artifact_id}/review-events`
- `POST /api/v2/analyses/{artifact_id}/review-status`
- `POST /api/v2/analyses/{artifact_id}/exports`
- `GET /api/v2/exports/{job_id}`

### 11.6 Erros

Formato obrigatório:

```json
{
  "code": "STRUCTURED_EXTRACTION_FAILED",
  "stage": "structured_extraction",
  "retryable": true,
  "user_message": "Não foi possível concluir a extração estruturada.",
  "correlation_id": "uuid",
  "details": {"safe": "metadata sem conteúdo jurídico"}
}
```

O envelope nunca incluirá prompt, trecho confidencial, chave, stack trace ou caminho interno.

## 12. Interface

### 12.1 Regras gerais

- Frontend não deriva tese, estratégia, risco ou argumento a partir de pedidos.
- Componentes renderizam apenas dados publicados pelo contrato.
- Cada aba exibe seu estado, cobertura, filtros e pendências.
- Estados vazios usam motivo proveniente do backend.
- Conteúdo não verificado recebe sinalização visual.
- Fontes abrem em painel lateral, com página, trecho e região destacados.
- Layout funciona em desktop e tablet; visualização móvel mantém conteúdo essencial.
- Navegação por teclado, foco, rótulos e contraste atendem WCAG 2.1 AA.

### 12.2 Galeria visual

- grade de miniaturas;
- filtros por documento, página, tipo, relevância, status e sensibilidade;
- visualização ampliada;
- comparação recorte/página original;
- itens jurídicos relacionados;
- confirmação de relevância pelo advogado;
- ocultação inicial de material sensível configurável.

### 12.3 Progresso

O usuário verá estágios reais, não porcentagem fictícia. O progresso será derivado de unidades mensuráveis, como documentos, páginas, lotes e verificações concluídas.

## 13. Módulos jurídicos

### 13.1 Núcleo universal — Onda 0

Obrigatório para todas as áreas:

- identificação e partes;
- cronologia;
- pedidos e relações;
- fatos e controvérsias;
- provas e imagens;
- fundamentos citados;
- questões processuais universais;
- teses bilaterais;
- riscos;
- valores e cálculos básicos cadastrados;
- estratégia, ações e perguntas;
- fontes, limitações e revisão.

### 13.2 Onda 1

- Cível e processo civil;
- Família e sucessões;
- Trabalhista;
- Consumidor;
- Previdenciário.

### 13.3 Onda 2

- Empresarial e societário;
- Contratos;
- Tributário;
- Administrativo;
- Imobiliário.

### 13.4 Onda 3

- Penal e processo penal;
- Ambiental;
- Eleitoral;
- Constitucional;
- Propriedade intelectual;
- Proteção de dados.

### 13.5 Regra de fallback

Quando nenhum módulo especializado cobrir integralmente o assunto:

1. o núcleo universal permanece ativo;
2. a classificação e as áreas detectadas são exibidas;
3. a seção afetada recebe `partial` e explica a ausência de especialização;
4. não são inventadas regras específicas;
5. o usuário ainda recebe fatos, pedidos, provas, fontes, riscos e ações universais.

## 14. Pesquisa jurídica

- Usar apenas integrações e fontes aprovadas por jurisdição.
- Priorizar fontes oficiais.
- Registrar URL, data de consulta, órgão, identificador, trecho e metadados.
- Separar conteúdo citado nos autos de conteúdo pesquisado.
- Validar existência e pertinência.
- Tratar mudanças legislativas e jurisprudenciais conforme data de referência.
- Não enviar nomes ou dados pessoais quando a consulta puder ser feita por tema.
- Queda da pesquisa não apaga a análise documental; gera estado parcial e ação pendente.

## 15. Segurança, privacidade e LGPD

- Escopo por usuário e organização em todas as consultas.
- Autorização em artefatos, casos, documentos, fontes, imagens, páginas, versões e exportações.
- Originais e revisões imutáveis, com hash.
- Criptografia em trânsito e em repouso conforme infraestrutura disponível.
- URLs temporárias para arquivos.
- Logs estruturados sem conteúdo jurídico ou segredo.
- Retenção e exclusão configuráveis.
- Trilha de auditoria para leitura, exportação, revisão e exclusão.
- Documentos tratados como dados não confiáveis; instruções neles contidas não alteram o sistema.
- Modelos e ferramentas recebem apenas o conteúdo necessário ao estágio.
- Conteúdo do cliente não é usado para treinamento sem consentimento específico.
- Material sensível visual pode ser ocultado por padrão.

## 16. Observabilidade e custos

Registrar por run e estágio:

- correlação, usuário/organização por identificador não sensível e caso;
- versão do pipeline, schemas, módulos, provedor e modelo;
- documentos, páginas, blocos, imagens e lotes;
- tokens estimados e observados quando disponíveis;
- duração, tentativas, filas e erros;
- fontes encontradas, verificadas e rejeitadas;
- status e motivos de cada seção;
- custo quando calculável, ou `unavailable`;
- número de correções humanas.

Alertas mínimos:

- crescimento de artefatos sem fatos, provas ou fontes;
- `completed` com página ou bloco não processado;
- divergência entre estágio e progresso;
- taxa elevada de falha de OCR, provedor ou parsing;
- custo ou duração fora do limite;
- acesso negado repetido a fontes ou imagens.

## 17. Testes e avaliação

### 17.1 Unitários

- schemas e invariantes;
- estados por seção;
- planejamento de cobertura;
- reconciliação e conflitos;
- validação de fontes;
- coordenadas e imagens;
- seleção de módulos;
- fórmulas e arredondamento;
- decisão de publicação;
- sanitização de erros e logs.

### 17.2 Integração

- arquivo até artefato publicado;
- vários documentos no mesmo caso;
- retomada por estágio;
- idempotência e cancelamento;
- pesquisa indisponível;
- OCR parcial;
- persistência de fontes e imagens;
- revisão concorrente;
- reanálise e comparação;
- exportação reproduzível.

### 17.3 Contrato e segurança

- tipos backend/frontend;
- paginação e filtros;
- ETag;
- isolamento entre usuários e organizações;
- tentativa de acesso por IDs conhecidos;
- URL expirada;
- prompt injection em documento;
- logs sem dados sensíveis.

### 17.4 E2E

- criar caso e enviar documentos;
- acompanhar progresso real;
- navegar por todas as abas;
- abrir fonte em página/região;
- abrir imagem e página original;
- filtrar galeria;
- corrigir e aprovar item;
- reanalisar preservando versão;
- comparar versões;
- exportar relatório.

### 17.5 Corpus adversarial

Incluir:

- PDF curto e longo;
- documento totalmente digitalizado;
- cabeçalho textual com corpo em imagem;
- página rotacionada;
- duas colunas;
- tabela complexa;
- fotografia com legenda externa ao recorte;
- documentos duplicados e revisões diferentes;
- pedidos no final da peça;
- pedido repetido com valores divergentes;
- datas incompatíveis;
- anexos mencionados e ausentes;
- múltiplas áreas no mesmo caso;
- ausência de módulo especializado;
- texto tentando instruir o modelo a ignorar regras;
- falha de provedor e saída JSON inválida.

### 17.6 Avaliação jurídica

Advogados revisores usarão rubrica de:

- cobertura;
- precisão factual;
- qualidade e pertinência das fontes;
- separação entre alegação e prova;
- completude dos pedidos;
- utilidade das teses e contrapontos;
- transparência das limitações;
- correção dos cálculos;
- utilidade do plano de ação.

Estrutura sintaticamente válida não comprova qualidade jurídica.

## 18. Critérios de aceite

### AC-01 — Não publicar dossiê ficticiamente completo

**Dado** que o provedor de IA falhou ou retornou saída inválida

**Quando** a execução terminar

**Então** o run será `failed` ou `partial` conforme exista conteúdo validado

**E** nenhuma tese genérica será criada

**E** o usuário receberá mensagem acionável.

### AC-02 — Popular todas as seções aplicáveis

**Dado** um documento com partes, fatos, pedidos, provas e fundamentos

**Quando** o pipeline universal concluir

**Então** cada objeto será representado em sua seção

**E** seção vazia terá `reason` e status explícitos.

### AC-03 — Cobertura integral

**Dado** um PDF de 35 páginas com pedidos nas últimas páginas

**Quando** o planejamento for executado

**Então** as 35 páginas serão inventariadas

**E** todos os blocos serão processados ou listados como não processados

**E** os pedidos finais serão incluídos.

### AC-04 — Fontes resolvíveis

**Dado** um fato material exibido

**Quando** o usuário selecionar “Ver fonte”

**Então** verá documento, revisão, página, trecho e região disponíveis

**E** o acesso respeitará autorização.

### AC-05 — Imagens no dossiê

**Dado** um documento com fotografia ou diagrama relevante

**Quando** o pipeline concluir

**Então** a imagem aparecerá na galeria e na prova relacionada

**E** poderá ser ampliada

**E** a página original poderá ser aberta

**E** falha de extração não será descrita como ausência de imagens.

### AC-06 — Caso multiarea

**Dado** um caso com aspectos cíveis, contratuais e tributários

**Quando** a classificação terminar

**Então** uma área principal e áreas relacionadas serão registradas

**E** mais de um módulo poderá ser ativado

**E** objetos duplicados serão reconciliados.

### AC-07 — Área sem módulo especializado

**Dado** um assunto sem especialização instalada

**Quando** a análise for executada

**Então** o núcleo universal produzirá conteúdo útil

**E** a limitação da especialização será declarada

**E** nenhuma regra específica será inventada.

### AC-08 — Cálculo reproduzível

**Dado** um cálculo exibido

**Quando** o advogado abrir os detalhes

**Então** verá fórmula, versão, entradas, premissas, índices e arredondamento

**E** a execução repetida produzirá o mesmo resultado.

### AC-09 — Revisão versionada

**Dado** um artefato publicado

**Quando** um revisor corrigir um item

**Então** o original, a correção, a autoria, a justificativa e a versão serão preservados

**E** conflito concorrente retornará `409`.

### AC-10 — Autorização

**Dado** um usuário sem acesso ao caso

**Quando** tentar obter artefato, fonte, imagem, página ou exportação por ID

**Então** receberá `404` ou resposta equivalente que não revele existência.

### AC-11 — Progresso honesto

**Dado** uma execução em extração

**Quando** o status for consultado

**Então** não exibirá 100%

**E** mostrará estágio e unidades processadas.

### AC-12 — Compatibilidade legada honesta

**Dado** um artefato originado da análise antiga

**Quando** for aberto

**Então** será identificado como legado e não verificado

**E** oferecerá reprocessamento

**E** não será apresentado como Dossiê Universal completo.

## 19. Impacto esperado no repositório

Esta lista orienta o planejamento; caminhos deverão ser reconfirmados antes da edição.

### 19.1 Backend — modificar

- `backend/app/tasks/document_tasks.py`: separar pipeline legado e universal; orquestrar estágios reais.
- `backend/app/core/schemas_v2.py`: contrato 3.0, estados por seção e novos objetos.
- `backend/app/core/coverage_planner.py`: cobertura por revisão, lote e tipo de bloco.
- `backend/app/core/extraction.py`: inventário visual, qualidade e regiões.
- `backend/app/core/reconciler.py`: reconciliação de todas as entidades.
- `backend/app/core/analysis_verifier.py`: verificações universais e modulares.
- `backend/app/api/routes/analysis_v2.py`: casos, imagens, versões, comparação e retomada.
- `backend/app/schemas/analysis_v2.py`: contratos HTTP.
- `backend/app/crud/run.py`: estágios, publicação atômica e consultas por caso.
- `backend/app/models/document_figure.py`: vínculo a revisão e metadados visuais, se ausentes.
- `backend/app/models/analysis_run.py`: snapshot, módulos, estágio e progresso mensurável.
- `backend/app/models/analysis_artifact.py`: schema 3.0 e relação com caso.
- `backend/app/models/source_reference.py`: regiões e fontes externas.
- `backend/app/core/v2_export.py`: relatório universal e imagens referenciadas.

### 19.2 Backend — criar

- `backend/app/core/pipeline/orchestrator.py`
- `backend/app/core/pipeline/stages.py`
- `backend/app/core/structured_extractor.py`
- `backend/app/core/classification.py`
- `backend/app/core/universal_legal_analyzer.py`
- `backend/app/core/module_registry.py`
- `backend/app/core/report_composer.py`
- `backend/app/core/visual_evidence.py`
- `backend/app/modules/universal/`
- diretórios dos módulos especializados por onda;
- modelos `case.py`, `case_document.py`, `analysis_stage_run.py`, `legal_research_result.py` e `calculation_result.py`, se ainda inexistentes;
- migrações Alembic correspondentes.

### 19.3 Frontend — modificar ou decompor

- `src/pages/analysis/v2/[id].tsx`: manter apenas composição de página e carregamento.
- `src/types/workflow.ts`: contrato completo do artefato.
- `src/lib/axios.ts`: endpoints e erros, se necessário.

### 19.4 Frontend — criar

- `src/components/dossier/DossierHeader.tsx`
- `src/components/dossier/SectionState.tsx`
- `src/components/dossier/SourceViewer.tsx`
- `src/components/dossier/VisualGallery.tsx`
- `src/components/dossier/VisualViewer.tsx`
- componentes de cada seção;
- hooks para artefato, seções, fontes, revisão e progresso;
- testes unitários e E2E correspondentes.

## 20. Sequência de entrega para o DeepCode

O DeepCode deverá executar em incrementos testáveis, sem implementar todas as ondas de uma vez.

1. Congelar contratos e fixtures de regressão do defeito atual.
2. Introduzir schema 3.0 e estados por seção, mantendo leitura do schema 2.0.
3. Criar casos, associações documentais e estágios persistidos.
4. Tornar inventário, cobertura e fontes requisitos do pipeline.
5. Implementar extração estruturada por lotes.
6. Implementar reconciliação global.
7. Implementar núcleo jurídico universal.
8. Integrar imagens e página-fonte.
9. Implementar verificador e publicação atômica.
10. Implementar API universal e autorização.
11. Decompor e completar a interface.
12. Implementar revisão, versões, comparação e exportação.
13. Adicionar observabilidade, limites e rollout.
14. Entregar Onda 1 módulo por módulo, cada um com corpus e gate próprios.
15. Prosseguir para Ondas 2 e 3 somente após métricas e avaliação da onda anterior.

Cada incremento deverá seguir testes primeiro, migração reversível, compatibilidade explícita e commit isolado. Não misturar especializações de ondas posteriores com a fundação universal.

## 21. Restrições obrigatórias para implementação

- Não resolver o problema apenas aumentando prompt, contexto ou modelo.
- Não usar `coerce_legacy_analysis()` no pipeline novo.
- Não preencher campos ausentes com frases genéricas.
- Não marcar `completed` quando cobertura material falhar.
- Não criar citações, páginas, valores, datas ou precedentes inexistentes.
- Não misturar conteúdo de usuários, organizações, casos ou revisões.
- Não depender de um único prompt monolítico.
- Não executar cálculo jurídico final somente no modelo de linguagem.
- Não apresentar análise gerada como fonte primária.
- Não apagar conflitos durante deduplicação.
- Não considerar extração de figura bem-sucedida apenas porque a lista retornou vazia.
- Não modificar o artefato publicado; toda mudança cria evento ou nova versão.

## 22. Migração e rollout

1. Manter leitura dos artefatos 2.0.
2. Identificar visualmente análises legadas.
3. Oferecer reprocessamento para o schema 3.0.
4. Não converter conteúdo ausente em dados inventados durante migração.
5. Habilitar o novo pipeline por feature flag para usuários internos.
6. Executar shadow runs com corpus anonimizado e amostra autorizada.
7. Comparar cobertura, fontes, duração, custo e correções.
8. Liberar gradualmente o núcleo universal.
9. Ativar módulos especializados individualmente.
10. Manter rollback para o fluxo anterior sem corromper artefatos novos.

## 23. Métricas de produto e qualidade

- percentual de runs `completed`, `partial`, `blocked` e `failed`;
- seções vazias por motivo;
- cobertura de páginas e blocos;
- pedidos explícitos encontrados versus confirmados pelo revisor;
- afirmações materiais com fonte válida;
- fontes abertas pelos usuários;
- imagens relevantes confirmadas ou descartadas;
- correções por seção;
- tempo até primeira informação útil e conclusão;
- custo por página, documento e caso;
- taxa de reanálise;
- aprovação jurídica por módulo;
- incidentes de autorização ou privacidade.

Não usar quantidade de texto como métrica de qualidade.

## 24. Definição de pronto

O Dossiê Universal só será considerado pronto quando:

- todos os critérios de aceite aplicáveis estiverem automatizados;
- o caso de regressão não produzir somente Pedidos;
- as demais seções aplicáveis tiverem conteúdo real ou estado justificado;
- cobertura e progresso forem honestos;
- fontes textuais e visuais abrirem com autorização;
- pelo menos um corpus multiarea passar pelo gate técnico e jurídico;
- falhas de provedor e extração resultarem em estados honestos;
- revisão, versão e exportação forem reproduzíveis;
- segurança e isolamento forem testados;
- dashboards e alertas mínimos estiverem ativos;
- documentação operacional e de rollback estiver disponível;
- advogados revisores aprovarem a utilidade do núcleo universal.

## 25. Matriz de rastreabilidade resumida

| Necessidade | Componentes | Testes/aceite |
|---|---|---|
| Evitar abas vazias | StructuredExtractor, UniversalLegalAnalyzer, SectionState | AC-02 |
| Cobertura integral | ExtractionService, CoveragePlanner, Verifier | AC-03 |
| Fontes verificáveis | SourceReference, SourceViewer | AC-04 |
| Imagens no dossiê | DocumentFigure, VisualEvidence, VisualGallery | AC-05 |
| Todas as áreas | ClassificationService, ModuleRegistry, fallback universal | AC-06, AC-07 |
| Cálculos confiáveis | CalculationService | AC-08 |
| Revisão humana | ReviewService, ReviewEvent | AC-09 |
| Segurança | autorização por organização/usuário/caso | AC-10 |
| Estado honesto | StageRun, Verifier, Publisher | AC-01, AC-11 |
| Legado | schema reader, reprocessamento | AC-12 |

## 26. Resultado esperado da primeira entrega

Ao concluir a Onda 0, qualquer caso deverá gerar um dossiê universal substancial, mesmo quando sua área ainda não possuir módulo especializado. O advogado verá o que foi localizado, onde foi localizado, como os elementos se relacionam, o que permanece incerto e o que deve fazer a seguir.

No caso que originou esta especificação, o resultado não poderá se limitar aos seis pedidos. Deverá apresentar, conforme o conteúdo dos documentos: partes, cronologia, alegações, controvérsias, provas, imagens, fundamentos, questões processuais, teses bilaterais, riscos, cálculos possíveis, ações, perguntas, limitações e fontes. Se qualquer seção não puder ser preenchida, a causa deverá estar explícita e tecnicamente rastreável.
