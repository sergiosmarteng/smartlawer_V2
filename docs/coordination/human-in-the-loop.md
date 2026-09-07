# Human-in-the-Loop — Approval Gates (A5)

Nenhuma saída de IA do SmartLawer é definitiva. Toda resposta da API carrega
`ai_draft: true` + `requires_human_review: true`, e o frontend rotula o
conteúdo como rascunho. As gates abaixo são obrigatórias no produto.

## Gates

1. **Chat jurídico (`/chat`, `/chat/stream`)** — resposta é rascunho de pesquisa.
   O advogado deve abrir cada citação e conferir o trecho antes de usar.
   Proibido copiar a resposta direto para peça sem revisão.
2. **Análise de petição (`/analysis/{id}`)** — resumo, pedidos, teses e defesa
   gerada exigem leitura humana antes de qualquer uso externo.
3. **Geração DOCX (`/analysis/{id}/docx`)** — download não é aprovação: o
   documento só vale após revisão e assinatura do responsável.
4. **Proibição de protocolo automático** — o sistema NUNCA protocola, envia ou
   publica peça sozinho. Não existe endpoint de protocolo; qualquer evolução
   nessa direção exige gate explícita nova + trilha de auditoria (BL-018/024).

## Reviewer checklist (antes de aprovar uma saída)

- [ ] Cada afirmação jurídica tem citação `[N]` e o trecho confere.
- [ ] Números (prazos, valores, artigos) conferem com a fonte, não com a resposta.
- [ ] Itens sem fundamento estão marcados como "não encontrei", não inventados.
- [ ] Dados de outro cliente/processo não vazaram para a resposta (tenant).

## Implementação atual

- API: `ChatResponse.ai_draft` + `requires_human_review` sempre `true`;
  eventos SSE `done` carregam os mesmos flags.
- Frontend `/chat`: aviso permanente de rascunho + fontes clicáveis.
- Eval: itens de abstenção (a01–a06) garantem que "não sei" continua possível.
