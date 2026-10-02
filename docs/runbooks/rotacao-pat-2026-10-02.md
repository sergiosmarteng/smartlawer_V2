# Runbook — Rotação do PAT do GitHub exposto em `78c3e36`

**Data:** 2026-10-02
**Status:** pronto para execução manual (não automatizar — envolve conta Admin/CUI do GitHub)
**Janela de risco:** ativa até `git filter-repo` (ou BFG) rodar em todas as cópias e o token antigo ser revogado

## 1. Contexto

O commit `78c3e36 feat: implement Phase 3 Uploads, Celery Tasks and OCR. Closes #2` está em uma branch preservada em `git log --all` (não no `main` atual). Confirmado em 2026-10-02 com:

```bash
git log --all --oneline | grep 78c3e36
# 78c3e36 feat: implement Phase 3 Uploads, Celery Tasks and OCR. Closes #2
```

O token vazado naquele commit **não está no `main` deployável**, mas segue em:

- Histórico de outras branches (`feature/phase-3-…`, tags antigas, clones de quem clonou antes da rotação.
- Eventuais cópias locais em outras estações (WSL, outros devs).
- Backups fora do controle de versão.

### Decisão do usuário (2026-10-02): migrar VPS para **SSH deploy key**, não fine-grained PAT.

Tradeoff:

| Abordagem | Prós | Contras |
|---|---|---|
| Fine-grained PAT (90d) | já tem credencial; revogação central no GitHub | expira → precisa de rotação periódica manual; risco de "token colado em script" |
| **SSH deploy key (VPS)** | sem expiração automática; escopo por repo; revogação = deletar a chave no GitHub; audível em `/var/log/auth.log` | precisa de passphrase + `ssh-agent`; chave privada fica na VPS (risco se VPS for comprometida) |
| GitHub App (CI/CD) | escopo granular, sem precisar de usuário | overkill de cele para deploy manual da VPS |

Para VPS única fazendo fetch-only: **SSH deploy key read-only é a melhor escolha**. Para estação dev: PAT fine-grained continua sendo o padrão.

## 3. Pré-condições

Antes de executar:

- Acesso de Owner/Admin no GitHub da org `schinasergio` (raiz) e `sergiosmarteng` (smarteng remote).
- Acesso de Admin ao VPS `164.152.35.112` (`smartlawer` user).
- Lista de **todos os lugares** onde o PAT antigo está salvo: ver §4.

## 4. Inventário de uso do PAT (verificar antes de revogar)

| Local | Onde ver | Comando / caminho |
|---|---|---|
| GitHub raiz | remotes | `git remote -v` → `https://github.com/schinasergio/smartlawer_V2.git` |
| GitHub submódulo | remotes | `git remote -v` → `git@github-schina:…` e `git@github-smarteng:…` |
| WSL dev | `~/.ssh/config` | `grep -A3 github-schina ~/.ssh/config` |
| VPS | `/opt/smartlawer/scripts/*.sh` | `grep -l 'github\|GITHUB\|gh-' /opt/smartlawer/scripts/ 2>/dev/null` |
| CI/CD | GitHub Actions / Docker Hub | painel web de cada serviço |
| Local `.env` / `.netrc` | **PROIBIDO** | `.gitignore` já contém `.env` e `.env*.local` (raiz e submódulo, confirmado em 2026-10-02) |
| Backup local | disco externo, OneDrive | varredura manual `grep -r 'ghp_'…` no backup |

## 5. Procedimento (ordem importa)

### Passo 1 — Revogar token no GitHub

1. GitHub → Settings → Developer settings → **Personal access tokens** → **Tokens (classic)**.
2. Encontrar o token vazado (começa com `ghp_…`).
3. Clicar **Delete** e confirmar.
4. **Confirmar revogação**: a entrada some da lista e tentativas de uso do token antigo retornam `401 Bad credentials`.

> ⚠️ A partir daqui, qualquer `git push` com credencial antiga falha. Não prossiga sem ter o novo token em mãos.

### Passo 2 — Criar novo PAT (fine-grained, scoped) **para estação dev**

Recomendado: **Fine-grained personal access token** em vez de classic. **Aplicação: máquina dev (Windows/WSL). NÃO usa na VPS** — VPS vai para SSH deploy key (ver Passo 3d).

1. GitHub → Settings → Developer settings → **Personal access tokens** → **Fine-grained tokens** → **Generate new token**.
2. **Token name:** `schina-dev-2026-10-02`.
3. **Expiration:** **90 dias** (não "No expiration") — força rotação futura.
4. **Repository access:** `Public Repositories (read)` + repos privados específicos (`schinasergio/smartlawer_V2`, `sergiosmarteng/smartlawer_V2`).
5. **Permissions:**
   - Contents → Read and write (push de commits)
   - Pull requests → Read and write (se você usa PR)
   - Workflows → Read and write (se deploy via GH Actions)
6. **Generate token** → copiar **uma única vez** (não é mostrado de novo).
7. Salvar em gerenciador de senhas (1Password / Bitwarden / KeePass). **Nunca em `.env` versionado ou comentário de código.**

### Passo 3 — Atualizar credenciais locais

#### 3a. Máquina Windows (esta estação) — PAT fine-grained

```bash
# Apaga credencial antiga do Windows Credential Manager
cmdkey /delete:git:https://github.com/schinasergio/smartlawer_V2.git

# Quando o próximo git push pedir credencial, cole o NOVO token
# (ou use Git Credential Manager para memorizar)
```

Para HTTPS:
```bash
git config --global credential.helper manager
# agora o Windows Credential Manager guarda o token novo após 1º push
```

Para SSH (se usar `github-schina`/`github-smarteng`):
```bash
# Editar ~/.ssh/config — atualizar IdentityFile apenas se trocar de chave.
# Para trocar APENAS o token (PAT injetado via ssh-agent):
ssh-add -D                              # limpa agent
ssh-add ~/.ssh/id_ed25519_github_schina # chave nova (se aplicável)
```

#### 3b. Submódulo (dentro de smartlawer_V2/)

```bash
cd "C:\Users\sergi\…\SmartLawer_V2\smartlawer_V2"
git remote set-url origin git@github-schina:schinasergio/smartlawer_V2.git
git remote -v   # confere
```

(Manter o alias `smarteng` se você também publica lá.)

#### 3c. WSL (se usar)

```bash
# Mesma lógica do Windows. Se usa chave SSH, copiar a nova para ~/.ssh/
# e atualizar ~/.ssh/config.
```

#### 3d. VPS (`164.152.35.112`) — **SSH deploy key read-only**

**Decisão:** VPS passa a autenticar com SSH deploy key (sem PAT). É a melhor escolha porque:
- Sem expiração automática (chave só some se deletar no GitHub).
- Escopo: read-only de um repo específico.
- Sem risco de "token colado em script" — a chave privada vive em `~/.ssh/` da VPS, não na URL.
- Compromisso da VPS = revogação instantânea no GitHub (1 clique).

**Passos na VPS:**

```bash
ssh smartlawer@164.152.35.112

# 1. Gerar par de chaves exclusivo para deploy (se já não tiver)
test -f ~/.ssh/id_ed25519_smartlawer_deploy || ssh-keygen -t ed25519 -C "smartlawer-deploy-$(date -I)" -f ~/.ssh/id_ed25519_smartlawer_deploy
#   passphrase recomendado: salvar em gerenciador

# 2. Listar a chave pública
cat ~/.ssh/id_ed25519_smartlawer_deploy.pub

# 3. No GitHub: repo smartlawer/deploy-VPS (ou similar) → Deploy keys → "Add deploy key"
#    - Title: vps-smartlawer-2026-10-02
#    - Key: colar o conteúdo de id_ed25519_smartlawer_deploy.pub
#    - Allow read-only (NÃO marcar write — VPS não precisa)
#    - Add key

# 4. Configurar ~/.ssh/config para usar a chave certa automaticamente
cat >> ~/.ssh/config <<'EOF'
Host github-smartlawer-deploy
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed25519_smartlawer_deploy
    IdentitiesOnly yes
EOF
chmod 600 ~/.ssh/config

# 5. Trocar URL do remote na VPS
cd /opt/smartlawer  # ou onde o clone estiver
git remote set-url origin git@github-smartlawer-deploy:schinasergio/smartlawer_V2.git
git remote -v
#   deve mostrar git@github-smartlawer-deploy:schinasergio/smartlawer_V2.git (push)

# 6. Testar ANTES de qualquer deploy
ssh -T -i ~/.ssh/id_ed25519_smartlawer_deploy git@github.com
#   esperado: "Hi schinasergio/smartlawer_V2! You've been granted access."
git ls-remote origin   # lista refs sem pedir nada

# 7. (Se havia PAT embutido na URL antiga, remova:)
git remote set-url origin $(git config --get remote.origin.url | sed 's#://[^@]*@#://#g')
```

**Atul traíticas pós-deploy:**

Verificar que nenhum script de deploy (`/opt/smartlawer/scripts/deploy-*.sh`) tem PAT embutido em URL ou variável:

```bash
grep -rnE 'ghp_|github_pat_|https://[^:]+:[^@]+@github' /opt/smartlawer/scripts/ 2>/dev/null
#   esperado: vazio (zero matches)
```

**Documentar em `/opt/smartlawer/scripts/deploy-0.NOTE.md`:**

```bash
# Deploy key SSH (read-only) ativo desde 2026-10-02.
# Rotação: deletar chave no GitHub → `ssh-keygen` novo → trocar `~/.ssh/id_ed25519_smartlawer_deploy.pub` no GitHub.
# Sem rotação periódica obrigatória (chave não expira).
```

### Passo 4 — Validar antes de mexer no histórico

```bash
# Em CADA clone (Windows, WSL, VPS, backup externo):
git ls-remote origin     # se retorna refs, credencial nova funciona

# VPS: o teste acima já usa SSH (sem prompt).
# Estação dev: pode pedir PAT na primeira tentativa.
```

Se algum desses falhar: credencial não foi atualizada nesse local. Voltar ao §4.

### Passo 5 — Purga do histórico (decisão consciente)

**Esta etapa é opcional mas recomendada** se você quer garantir que o token não volte a vazar via `git clone` desatualizado.

**Quando FAZER purga:**

- Token tem escopo amplo (repo, admin).
- Token está em commit que não é seu (caso de token compartilhado).
- Compliance/auditoria exige.

**Quando NÃO fazer:**

- O commit `78c3e36` já está em branch órfã/merged-descartada e o token tem escopo limitado.
- Equipe pequena, todos cientes, rotação é o suficiente.

**Como purgar (BFG Repo-Cleaner):**

```bash
# Em CÓPIA NOVA do repo (NÃO no clone principal)
git clone --mirror https://github.com/schinasergio/smartlawer_V2.git smartlawer_V2.git

# Criar arquivo tokens.txt com o PAT antigo:
echo "ghp_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX" > tokens.txt

# Rodar BFG (download em https://rtyley.github.io/bfg-repo-cleaner/)
java -jar bfg.jar --replace-text tokens.txt smartlawer_V2.git

# Limpar refs órfãs
cd smartlawer_V2.git
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# Force push (COORDENAR COM A EQUIPE ANTES)
git push --force --all
git push --force --tags

# Limpar cópias antigas nos outros lugares (Windows, WSL, VPS, backup)
# Cada clone precisa de `git fetch && git reset --hard origin/main` após o force push
```

> ⚠️ `git push --force` reescreve histórico — hashes mudam. Qualquer clone / branch / fork passa a ficar inconsistente até `git fetch && git reset --hard origin/main`. Documente em `docs/runbooks/nota-force-push-2026-10-02.md`.

### Passo 6 — Sanity check do token novo

```bash
# Tentar push de um commit trivial (ex: bump de typo num doc) numa branch descartável:
cd smartlawer_V2
git checkout -b teste-pat-novo
echo "validado em staging: $(date -u)" >> docs/runbooks/rotacao-pat-2026-10-02.md
git add docs/runbooks/rotacao-pat-2026-10-02.md
git commit -m "chore(runbooks): validar PAT novo"
git push origin teste-pat-novo   # se pedir credencial, é o token novo

# Se OK, deletar:
git push origin --delete teste-pat-novo
git checkout main
git branch -D teste-pat-novo
```

### Passo 7 — Atualizar CONSTITUTION / SESSION_STATE

1. Em `.opencode/sessions/2026-10-02-fechamento-020.md`, marcar passo como concluído.
2. Em `docs/SESSION_STATE.json`, remover a constraint `PAT do GitHub ainda pendente de rotação` e atualizar `status`.

## 6. Critérios de "feito"

- [ ] Token antigo **revogado no GitHub** (verificado com `401 Bad credentials`).
- [ ] PAT fine-grained novo criado (90d, escopo mínimo) **aplicado na estação dev**.
- [ ] **SSH deploy key (read-only) da VPS adicionado no GitHub** (`vps-smartlawer-2026-10-02`).
- [ ] `~/.ssh/config` da VPS aponta a chave nova pro alias `github-smartlawer-deploy`.
- [ ] URL do remote na VPS aponta para `git@github-smartlawer-deploy:…` (sem token embutido).
- [ ] Cada clone local (Windows, WSL): `git fetch origin` funciona sem pedir credencial antiga.
- [ ] VPS: `ssh -T … git@github.com` retorna saudação de sucesso **sem** pedir passphrase.
- [ ] Nenhum PAT em URL de remote ou variável de script (`grep` no §3d limpo).
- [ ] (Opcional) Histórico purgado via BFG **e** `git push --force` coordenado.
- [ ] Push de smoke OK numa branch descartável.
- [ ] `SESSION_STATE.json` atualizado.

## 7. Rollback (se algo falhar)

- Token novo não funciona em algum local → voltar ao §3 e conferir escopo/expiração.
- BFG reescreveu hashes e quebrou clones alheios → reenviar `git fetch && git reset --hard origin/main` e comunicar hashes novos.
- VPS não consegue mais puxar updates → rodar manualmente `ssh smartlawer@164.152.35.112` e conferir `~/.git-credentials` ou `ssh-add -l`; nunca deixar credencial com falha em retry loop.

## 8. Não-objetivos (decisões deliberadas)

- **Não** vamos trocar a estratégia de autenticação (HTTPS token → SSH key ou GH App) nesta rotação. Decisão fora do escopo.
- **Não** vamos commitar o token novo em lugar nenhum. Nem em `.env` (já bloqueado pelo `.gitignore`), nem em comentário, nem em issue.
- **Não** vamos rodar purge via BFG automaticamente. Só após sua confirmação explícita.