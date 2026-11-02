# SmartLawer V2 — Onda 2 planejada (2026-10-04)

## Dados

- **Data:** 2026-10-04 (checkpoint de continuidade; nenhum commit novo nesta data ainda).
- **Continue de:** `.opencode/sessions/2026-10-03-onda-1-completa.md` (Onda 1 completa, HEAD `d57ed72`).
- **Último commit:** `c612c67` (2026-10-03 02:04) — planos da Onda 2 consolidados.

## O que foi feito desde o último checkpoint

| Commit                 | Conteúdo                                                                                                                                                                                                                                                                                                                                                                                  |
| ---------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `c612c67` (docs/plans) | Planos de implementação da Onda 2 consolidados, task-by-task (sintaxe checkbox), reusando pipeline Onda 0/1: `docs/superpowers/plans/2026-10-03-dossie-onda-2a-contracts-corporate.md` (180 linhas) e `docs/superpowers/plans/2026-10-03-dossie-onda-2b-tax-administrative-real-estate.md` (176 linhas). Spec de referência: `docs/superpowers/specs/2026-10-02-dossie-onda-2-design.md`. |

Sem alteração de código, schema, tests ou deploy neste ciclo — sessão de planejamento/documentação.

## Decisões / constraints (preservadas verbatim onde crítico)

1. Flags off por padrão (`DOSSIER_MODULE_<ID>=false`); produção inalterada até gate próprio + piloto. Rollout um módulo por vez.
2. Módulos nunca mutam o núcleo (envelope `module_results` + falha isolada no runner).
3. "Nenhuma alteração silenciosa do schema 3.0; `module_results` já existe — extensão incompatível exigiria nova versão formal (spec §10)."
4. "Vínculo jurídico nunca afirmado por coocorrência de nomes; cláusula sem assinatura/versão nunca tratada como aceita; registro/publicidade nunca presumidos pelo nome do arquivo (§2)."
5. "Cálculos só com cláusula vigente, base, índice, termo e período; IA sugere regra cadastrada, nunca número final livre."
6. "Falha de um módulo vira `blocked` + limitação — nunca impede o dossiê universal nem o outro módulo do par."
7. Sem migration na Onda 1; Onda 2 mantém o mesmo princípio salvo dado consultável em SQL.
8. `.env` nunca versionado; PAT do GitHub ainda pendente de rotação (blocker de segurança).
9. Onda 2A (contracts+corporate) é par coeso: entidades/fatos/pedidos/fontes compartilhados por IDs estáveis; módulo primário não absorve o outro (§2).

## Andamento

### Feito

- [x] Onda 0 (Dossie Universal V3, Tasks 1–16) — 298 testes.
- [x] Onda 1 (fundação + 1A family/civil_procedure + 1B labor/consumer/social_security + integração atrás de flags) — pytest 337, gates verdes, corpus 35/35.
- [x] Planos da Onda 2 consolidados (2A + 2B) em `docs/superpowers/plans/`.

### Pendente (operador — fora desta máquina)

- [ ] Rotações PAT (deploy key na VPS; fine-grained PAT no dev) — blocker de segurança pré-piloto.
- [ ] Migrations VPS (head `20261002_0013`) com backup pg_dump; smoke pós-deploy 12 blocos A–K.
- [ ] Shadow runs V3 + piloto 50 execuções; habilitar `DOSSIER_MODULE_<ID>` um por vez.
- [ ] Gate jurídico humano por módulo (2 revisores/área, spec §9).

### Próximo (engenharia)

- [ ] Onda 2A: implementar `contracts@1.0.0` + `corporate@1.0.0` conforme `docs/superpowers/plans/2026-10-03-dossie-onda-2a-contracts-corporate.md` (teste falhando primeiro, flags off por padrão).
- [ ] Onda 2B: `tax` + `administrative` + `real_estate` conforme plano 2B.
- [ ] Onda 3 (após gates jurídicos da Onda 2).

## Bloqueadores / riscos

- PAT do GitHub exposto (`78c3e36`) sem rotação — blocker de segurança.
- VPS não acessível desta estação (Windows) — smoke/deploy in loco.
- E2E Playwright não executado (sem ambiente de teste).
- Gate jurídico humano depende de 2 revisores por área (processo externo).

## Evidência (base do último checkpoint, sem novas execuções neste ciclo)

- `pytest tests/ -q -p no:warnings` → 337 passed; `run_gate.py` → GATE PASSED; universal → 35/35; vitest 19; lint/tsc/build OK.
- Git: `d57ed72..c612c67`, `ahead_behind` 0 0 (origin `sergiosmarteng`).

Para retomar: reabrir o opencode no mesmo diretório e rodar `/retomar` (opções a/b/c).
