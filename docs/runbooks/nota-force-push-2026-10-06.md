# Nota de force-push — purga do PAT (2026-10-06)

**Status: ARQUIVADA — preparada-mas-não-executada (decisão 2026-10-06).**
Reativar somente se um auditor solicitar: basta confirmar o force-push
abaixo. Mirror pronto em `%TEMP%\smartlawer_V2.git` (se o TEMP for limpo,
reexecutar é barato — procedimento integral nesta nota).

## O que foi purgado

Token `github_pat_11BOTRJKQ0PfX0zJAB6iK1...` (já revogado no GitHub) removido
via BFG `--replace-text` de `.env` e `docs/CLAUDE.md` em todo o histórico
(3 commits afetados; 301 objetos reescritos). Verificação:
`git log -S '<token>' --all --oneline` → vazio.

## Hashes antes → depois

| Ref      | Antes     | Depois    |
| -------- | --------- | --------- |
| `main`   | `49740e0` | `a99e8b7` |
| `v0.1.1` | `9b4bb63` | `cdab9b9` |
| `v0.2.0` | `b59bd65` | `ddce2a3` |
| `v0.3.0` | `5a4569f` | `bc1b0c3` |

## Para executar (somente com confirmação explícita)

```bash
cd $env:TEMP/smartlawer_V2.git
git push --force --all
git push --force --tags
Remove-Item $env:TEMP/smartlawer_V2.git -Recurse -Force
```

## Reset obrigatório em cada clone após o force

```bash
git fetch origin
git checkout main
git reset --hard origin/main
```

- **VPS** (`/opt/smartlawer`, in loco): mesmo procedimento + `docker compose build api worker` + `up -d --no-deps` + `alembic current` (sem migration nova, só reconfirmação).
- **WSL/outros devs e backups:** idem; descartar stashes/branches locais não pushed ou fazer rebase manual.
- Pré-requisito: `git status` limpo em cada clone (nada não commitado) antes do reset.
