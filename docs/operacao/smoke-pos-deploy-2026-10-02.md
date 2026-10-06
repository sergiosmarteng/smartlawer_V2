# Smoke formal pós-deploy — Dossiê Universal Onda 0

**Status:** smoke operacional para validar a Onda 0 antes de iniciar o piloto real (50 execuções).
**Data:** 2 de outubro de 2026
**Módulos em validação:** núcleo universal + fallback universal (schema 3.0).
**Módulos fora de escopo deste smoke:** Onda 1 (cível/família/trabalhista/consumidor/previdenciário), Onda 2 (empresarial/contratos/tributário/administrativo/imobiliário), Onda 3 (penal/ambiental/eleitoral/constitucional/PI/proteção de dados). Eles ainda não foram implementados; suas specs (`2026-10-02-dossie-onda-{1,2,3}-design.md`) serão exercitadas em ondas futuras.

## 1. Resultado e dependências

Este smoke verifica que a **fundação** do [Dossiê Universal](file:///C:/Users/sergi/OneDrive%20-%20SSA%20Solu%C3%A7%C3%B5es%20Tecnologicas/SSA%20Solucoes%20Tecnologicas/Projetos%20prototipos/SmartLawer_V2/smartlawer_V2/docs/superpowers/specs/2026-09-27-dossie-juridico-universal-design.md) está de pé antes de liberar o piloto para advogados externos.

O [plano da Onda 0](../smartlawer_V2/docs/superpowers/plans/2026-10-02-dossie-juridico-universal-onda-0.md) define 15 tasks. Este documento valida apenas o que é **observável em produção** (não o código-fonte), mas segue os `Global Constraints` e `Review Focus` daquele plano.

**Resultado esperado:** em qualquer execução pós-deploy, o dossiê retornado tem `schema_version="3.0"`, todas as seções expõem `SectionState` com `status/reason/coverage/pending_actions`, toda afirmação material tem fonte resolvível ou limitação explícita, e o usuário foi capaz de abrir pelo menos uma fonte em página original. Quando nenhum módulo especializado existir para a área, o núcleo universal ainda produz conteúdo útil com `partial`/`blocked` justificado.

**Quando executar:** após cada deploy de merge em `main` (submódulo) e bump na raiz, antes de abrir o piloto para advogado externo.

## 2. Conexão e pré-condições

```bash
ssh smartlawer@164.152.35.112   # deploy key SSH (ver docs/runbooks/rotacao-pat-2026-10-02.md)
cd /opt/smartlawer
```

Pré-condições (todas devem estar **PASS** antes de iniciar):

- [ ] VPS acessível sem PAT (`ssh -T git@github.com` na VPS retorna saudação de sucesso).
- [ ] Tag `v0.3.0` em `origin/main`.
- [ ] Sem segredos em scripts de deploy: `grep -rnE 'ghp_|github_pat_|https://[^:]+:[^@]+@github' /opt/smartlawer/scripts/` → **vazio**.
- [ ] Sem `coerce_legacy_analysis()` em caminho de produção (`grep -rn 'coerce_legacy_analysis' backend/app/tasks/ backend/app/core/pipeline/` → apenas imports legados para leitura, não produção).

## 3. Gates comuns (Global Constraints do plano + Review Focus)

Cada gate abaixo é um **bloco de smoke**. Marca **PASS** quando o comando retorna o esperado; marca **FAIL** com evidência quando não.

### Bloco A — Saúde dos containers (infraestrutura)

```bash
docker compose -f docker-compose.prod.yml ps --format json | jq -r '.[] | "\(.Name) \(.State) \(.Health.Status // "n/a")"'
```

| Esperado | Resultado |
|---|---|
| `smartlawer-api` `running` `healthy` | `<…>` |
| `smartlawer-worker` `running` `healthy` | `<…>` |
| `smartlawer-frontend` `running` `n/a` | `<…>` |
| `smartlawer-db` `running` `healthy` | `<…>` |
| `smartlawer-redis` `running` `healthy` | `<…>` |

**Pass / Fail:** `<…>` | **Evidência:** `<…>`

### Bloco B — Versão, migração e tag

```bash
# Versão do backend (o pacote não expõe `__version__`; conferir via git + API)
git -C /opt/smartlawer rev-parse --short HEAD
curl -sS -o /dev/null -w "%{http_code}\n" https://smartlawer.com.br/
# Esperado: hash do main atual; site 200

# HEAD do submódulo
docker compose -f docker-compose.prod.yml exec -T api \
  git -C /opt/smartlawer rev-parse --short HEAD
# Esperado: hash do main atual (igual ao `git rev-parse --short HEAD` local)

# Migração
docker compose -f docker-compose.prod.yml exec -T api alembic current
# Esperado: 20261002_0013 (head)

# Sem drift
docker compose -f docker-compose.prod.yml exec -T api alembic heads --verbose
# Esperado: 1 head, sem "(head) para migrations" extras
```

| Esperado | Resultado |
|---|---|
| `0.3.0` | `<…>` |
| HEAD em main atual | `<…>` |
| alembic current = `20261002_0013 (head)` | `<…>` |
| Sem drift de head | `<…>` |

**Pass / Fail:** `<…>` | **Evidência:** `<…>`

### Bloco C — Variáveis de ambiente (chaves IA, modelos, Docling)

```bash
docker compose -f docker-compose.prod.yml exec -T api \
  sh -c 'env | grep -E "^(OPENAI|GEMINI|OPENROUTER|ANTHROPIC)_API_KEY=" | sed "s/=.*/=<REDACTED>/"'
# Esperado: >=1 chave não vazia

docker compose -f docker-compose.prod.yml exec -T api \
  sh -c 'env | grep -E "^(CHAT_MODEL|DOCLING_ENABLED|AI_PROVIDER|MAX_RUN_TOKENS|MAX_RUN_USD)"'
# Esperado: CHAT_MODEL=gemini-3.8-flash; DOCLING_ENABLED=true; AI_PROVIDER conforme chave
```

| Esperado | Resultado |
|---|---|
| ≥1 chave de provedor de IA | `<…>` |
| `CHAT_MODEL=gemini-3.8-flash` | `<…>` |
| `DOCLING_ENABLED=true` | `<…>` |
| `AI_PROVIDER` consistente com chave presente | `<…>` |

**Pass / Fail:** `<…>` | **Evidência:** `<…>`

### Bloco D — Compatibilidade legada (AC-12 do spec universal)

```bash
# 1. Listar artefatos legados (schema 2.0) ainda legíveis
docker compose -f docker-compose.prod.yml exec -T api python <<'PY'
from app.core.schemas_v2 import coerce_legacy_analysis  # leitura
print("coerce_legacy_analysis disponível para leitura:", coerce_legacy_analysis is not None)

from app.models.analysis_artifact import ArtifactKind
legados = ArtifactKind.count_by_schema_version("2.0") if hasattr(ArtifactKind, "count_by_schema_version") else None
print("artefatos legados 2.0:", legados)
PY

# 2. Garantir que coerce_legacy_analysis NÃO está em produção
docker compose -f docker-compose.prod.yml exec -T api \
  grep -rn 'coerce_legacy_analysis' /app/app/tasks/ 2>/dev/null || echo "OK: não referenciado em tasks"
# Esperado: "OK: não referenciado em tasks"

docker compose -f docker-compose.prod.yml exec -T api \
  grep -rn 'coerce_legacy_analysis' /app/app/core/pipeline/ 2>/dev/null || echo "OK: não no pipeline V3"
# Esperado: "OK: não no pipeline V3"
```

| Esperado | Resultado |
|---|---|
| `coerce_legacy_analysis` importável para leitura | `<…>` |
| **Não** referenciado em `tasks/` (caminho de produção) | `<…>` |
| **Não** referenciado em `core/pipeline/` | `<…>` |

**Pass / Fail:** `<…>` | **Evidência:** `<…>`

### Bloco E — Publicação e progresso honestos (AC-01, AC-11, Review Focus)

```bash
# 1. Pegar um documento real já analisado em prod (NÃO criar novo agora — usar existente)
# O artefato liga-se ao documento via run -> document_id (sem join direto)
DOC_ID=$(docker compose -f docker-compose.prod.yml exec -T api python <<'PY'
from app.models.analysis_artifact import AnalysisArtifact
from app.models.analysis_run import AnalysisRun
from app.core.database import SessionLocal
db = SessionLocal()
arts = db.query(AnalysisArtifact).filter(
    AnalysisArtifact.schema_version == "3.0",
    AnalysisArtifact.status.in_(["completed", "partial"]),
).order_by(AnalysisArtifact.created_at.desc()).all()
doc_id = ""
for art in arts:
    run = db.query(AnalysisRun).filter(AnalysisRun.id == art.run_id).first()
    if run is not None and run.document_id:
        doc_id = run.document_id
        break
print(doc_id)
PY
)
echo "DOC_ID=$DOC_ID"

# 2. Conferir que schema_version=3.0 e SectionStates presentes
docker compose -f docker-compose.prod.yml exec -T api python <<PY
from app.models.analysis_artifact import AnalysisArtifact
from app.models.analysis_run import AnalysisRun
from app.core.database import SessionLocal
db = SessionLocal()
run = db.query(AnalysisRun).filter(AnalysisRun.document_id == "$DOC_ID").order_by(AnalysisRun.created_at.desc()).first()
art = db.query(AnalysisArtifact).filter(AnalysisArtifact.run_id == run.id).first() if run else None
content = art.content if art else None
print("schema_version:", content.get("schema_version") if content else None)
print("section_states:", len(content.get("section_states", {})) if content else 0)
print("cobertura.pages:", content.get("coverage", {}).get("pages_total") if content else None)
PY
# Esperado: schema_version == "3.0"; section_states >= 9 (todas as seções do spec §6.3);
#          coverage.pages_total > 0 (não pode ser 0/0 — defeito §3.1 do spec)
```

| Esperado | Resultado |
|---|---|
| `schema_version = 3.0` | `<…>` |
| `section_states` cobre todas as seções do spec | `<…>` |
| `coverage.pages_total > 0` (não 0/0) | `<…>` |
| Se `coverage.pages_total == 0`: indica defeito — FAIL | `<…>` |

**Pass / Fail:** `<…>` | **Evidência:** `<…>`

### Bloco F — Fontes resolvíveis (AC-04)

```bash
# Pegar um source_id do artefato acima
docker compose -f docker-compose.prod.yml exec -T api python <<PY
from app.models.analysis_artifact import AnalysisArtifact
from app.models.analysis_run import AnalysisRun
from app.core.database import SessionLocal
db = SessionLocal()
run = db.query(AnalysisRun).filter(AnalysisRun.document_id == "$DOC_ID").order_by(AnalysisRun.created_at.desc()).first()
art = db.query(AnalysisArtifact).filter(AnalysisArtifact.run_id == run.id).first() if run else None
content = art.content if art else {}
sources = content.get("sources", []) if content else []
print("n_sources:", len(sources))
print("sample_source:", sources[0] if sources else None)
PY
# Esperado: n_sources >= 1; cada source tem document_id + revision_id + (page number | region)

# Tentar resolver uma fonte via API (ART_ID via DB, sem endpoint de listagem)
ART_ID=$(docker compose -f docker-compose.prod.yml exec -T api python <<PY
from app.models.analysis_artifact import AnalysisArtifact
from app.models.analysis_run import AnalysisRun
from app.core.database import SessionLocal
db = SessionLocal()
run = db.query(AnalysisRun).filter(AnalysisRun.document_id == "$DOC_ID").order_by(AnalysisRun.created_at.desc()).first()
art = db.query(AnalysisArtifact).filter(AnalysisArtifact.run_id == run.id).first() if run else None
print(art.id if art else "")
PY
)
SOURCE_ID=$(docker compose -f docker-compose.prod.yml exec -T api python <<PY
from app.models.analysis_artifact import AnalysisArtifact
from app.models.analysis_run import AnalysisRun
from app.core.database import SessionLocal
db = SessionLocal()
run = db.query(AnalysisRun).filter(AnalysisRun.document_id == "$DOC_ID").order_by(AnalysisRun.created_at.desc()).first()
art = db.query(AnalysisArtifact).filter(AnalysisArtifact.run_id == run.id).first() if run else None
print((art.content.get("sources", [{}])[0].get("id") if art and art.content.get("sources") else ""))
PY
)
curl -fsS -o /dev/null -w "%{http_code}\n" -b /tmp/cookies.txt \
  "https://smartlawer.com.br/api/v2/sources/$SOURCE_ID"
# Esperado: 200
```

| Esperado | Resultado |
|---|---|
| `n_sources >= 1` no artefato | `<…>` |
| Cada source tem `document_id`+`revision_id`+página/região | `<…>` |
| `GET /api/v2/sources/{id}` retorna **200** | `<…>` |

**Pass / Fail:** `<…>` | **Evidência:** `<…>`

### Bloco G — Erros normalizados e sem segredo (Review Focus)

```bash
# Tentar IDs de outro usuário / inválidos — esperado: 404 (NÃO 500) e sem stack trace nem prompt
curl -sS -o /tmp/r.json -w "%{http_code}\n" -b /tmp/cookies.txt \
  "https://smartlawer.com.br/api/v2/analyses/00000000-0000-0000-0000-000000000000"
# Esperado: 404

cat /tmp/r.json | jq '. | {has_code: (.code != null), has_stack: (.stack != null or .traceback != null), has_prompt: (.prompt != null)}'
# Esperado: {has_code: true, has_stack: false, has_prompt: false}

# Buscar nos logs do backend se houve alguma exceção recente com stack trace ou chave
docker compose -f docker-compose.prod.yml logs --since=10m api 2>&1 | \
  grep -E 'Traceback|ghp_|sk-ant=|Authorization:' | head -5
# Esperado: vazio
```

| Esperado | Resultado |
|---|---|
| 404 (não 500) para ID inválido | `<…>` |
| Sem `stack`/`traceback` no JSON | `<…>` |
| Sem `prompt` no JSON | `<…>` |
| Logs sem stack trace nem chave | `<…>` |

**Pass / Fail:** `<…>` | **Evidência:** `<…>`

### Bloco H — Autorização (AC-10)

```bash
# Sem cookie (não autenticado) — esperado: 401/403, não 500
curl -sS -o /tmp/r.json -w "%{http_code}\n" \
  "https://smartlawer.com.br/api/v2/analyses?document_id=$DOC_ID"
# Esperado: 401 ou 403

# Cookie mas com user diferente (substituir ADMIN_EMAIL/ADMIN_PASS do usuário A)
# Pegar cookies do usuário B e tentar acessar artefato do usuário A
curl -fsS -X POST https://smartlawer.com.br/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"<USER_B_EMAIL>","password":"<USER_B_PASS>"}' \
  -c /tmp/cookies_b.txt

curl -sS -o /tmp/r.json -w "%{http_code}\n" -b /tmp/cookies_b.txt \
  "https://smartlawer.com.br/api/v2/analyses?document_id=$DOC_ID"
# Esperado: 200 com lista VAZIA (escopo por usuário) OU 404 (404 opaco)
# PROIBIDO: 200 com o artefato do usuário A
```

| Esperado | Resultado |
|---|---|
| Sem auth: 401/403 (não 500) | `<…>` |
| User B: **não** vê artefato do User A | `<…>` |

**Pass / Fail:** `<…>` | **Evidência:** `<…>`

### Bloco I — Cálculo reproduzível (AC-08)

```bash
# Se houver cálculos registrados no artefato, conferir reprodutibilidade
docker compose -f docker-compose.prod.yml exec -T api python <<PY
from app.models.analysis_artifact import AnalysisArtifact
from app.models.calculation_result import CalculationResult
from app.core.database import SessionLocal
db = SessionLocal()
arts = db.query(AnalysisArtifact).filter(
    AnalysisArtifact.schema_version == "3.0"
).order_by(AnalysisArtifact.created_at.desc()).limit(3).all()
for art in arts:
    calc_ids = (art.content.get("calculations") or [])
    for cid in calc_ids:
        c = db.query(CalculationResult).filter(CalculationResult.id == cid.get("id")).first()
        if c:
            print(f"calc {cid.get('id')[:8]} version={c.formula_version} hash={c.output_hash[:12]} reproducible={c.reproducible}")
PY
# Esperado: cada cálculo com formula_version, output_hash e reproducible=True
```

| Esperado | Resultado |
|---|---|
| Cada cálculo tem `formula_version` | `<…>` |
| Cada cálculo tem `output_hash` | `<…>` |
| `reproducible = True` (Decimal + half_up_centavos) | `<…>` |

**Pass / Fail:** `<…>` | **Evidência:** `<…>`

### Bloco J — Telemetria e custos (Review Focus)

```bash
docker compose -f docker-compose.prod.yml logs --since=10m api 2>&1 | \
  grep -E 'run_id|tokens_in|tokens_out|cost_usd|stage' | head -20
# Esperado: telemetria por run e estágio, sem conteúdo jurídico nem chave
```

| Esperado | Resultado |
|---|---|
| Logs estruturados com run/stage | `<…>` |
| Sem conteúdo jurídico (texto do doc) | `<…>` |
| Sem chave/credencial | `<…>` |

**Pass / Fail:** `<…>` | **Evidência:** `<…>`

### Bloco K — Segurança / SSL / Headers

```bash
# SSL válido (cert ECDSA até 23/12/2026)
echo | openssl s_client -connect smartlawer.com.br:443 -servername smartlawer.com.br 2>/dev/null | \
  openssl x509 -noout -dates
# Esperado: notAfter dentro da validade

curl -sSI https://smartlawer.com.br/ | grep -iE "^(strict-transport-security|content-security-policy|x-frame-options|referrer-policy)"
# Esperado: STS presente; CSP presente
```

| Esperado | Resultado |
|---|---|
| SSL válido | `<…>` |
| `Strict-Transport-Security` | `<…>` |
| `Content-Security-Policy` | `<…>` |

**Pass / Fail:** `<…>` | **Evidência:** `<…>`

## 4. Veredito

| Bloco | Pass / Fail | Evidência |
|---|---|---|
| A — containers | `<…>` | `<…>` |
| B — versão/migração | `<…>` | `<…>` |
| C — env vars | `<…>` | `<…>` |
| D — compatibilidade legada | `<…>` | `<…>` |
| E — schema 3.0 + SectionState | `<…>` | `<…>` |
| F — fontes resolvíveis | `<…>` | `<…>` |
| G — erros sem segredo | `<…>` | `<…>` |
| H — autorização | `<…>` | `<…>` |
| I — cálculo reproduzível | `<…>` | `<…>` |
| J — telemetria | `<…>` | `<…>` |
| K — SSL/headers | `<…>` | `<…>` |

### Go (liberação do piloto)

Todos os blocos A–K PASS, **e** o artefato do bloco E tem `coverage.pages_total > 0` com seções populadas (não "0/0", não todas `blocked`).

### Não-go (bloquear, voltar à engenharia)

Qualquer um:

- Bloco B FAIL (versão/migração inconsistente).
- Bloco D FAIL (`coerce_legacy_analysis` em produção) — defeito §3.4 do spec.
- Bloco E FAIL com `coverage.pages_total == 0` — defeito §3.1 do spec.
- Bloco F FAIL (fontes não resolvíveis) — AC-04 violado.
- Bloco G FAIL com stack trace em resposta (vaza informação).
- Bloco H FAIL com user B vendo artefato do user A (vaza entre organizações).
- Bloco I FAIL com cálculo `reproducible=False` ou sem `formula_version`.

## 5. Rollback (se Não-go)

1. Não abrir o piloto para advogado externo.
2. Reportar bloco(s) FAIL com evidência em `docs/operacao/incidente-<data>.md`.
3. Reverter via release doc vigente em `docs/implementation/` (retag `before-v030`, `up --no-deps`, restore pg_dump se necessário).
4. Corrigir root cause em branch apropriada; novo deploy só após smoke **PASS** em **todos os blocos**.

## 6. Não-objetivos

- Não testar Ondas 1/2/3 (especificadas, não exercitadas) — cobertura está em planos próprios.
- Não exercitar upload de PDF novo neste smoke — criação de execução está no Bloco E com docs já existentes.
- Não verificar carga / concorrência — pertence a teste de carga, fora deste escopo.