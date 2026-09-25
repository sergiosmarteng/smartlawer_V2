# Landing page publicada em 24/09/2026

## Entrega

Página pública redesenhada em `https://smartlawer.com.br/`, com identidade verde/marfim/dourado, duas imagens originais geradas por IA, recursos, demonstração interativa, fluxo de uso, benefícios e perguntas frequentes. Os textos descrevem funcionalidades existentes e não prometem percentuais de produtividade nem cobertura integral de jurisprudência.

Implementação em `src/components/landing/`, consumida por `src/pages/index.tsx`. A descrição padrão saiu de `_document.tsx` e passou para o `Head` de `_app.tsx`, permitindo uma única descrição específica na homepage. Rotas e lógica de autenticação não foram alteradas.

Imagens e prompts: [landing-image-prompts.md](landing-image-prompts.md).

## Verificação

- TypeScript: `npx tsc --noEmit`, exit 0.
- Lint dos arquivos da página e componentes: sem avisos ou erros.
- Build Docker de produção na VPS, incluindo lint e checagem de tipos: exit 0.
- Inspeção visual da página em desktop e mobile, sem rolagem horizontal nos tamanhos verificados.
- Abas da demonstração por clique e teclado; menu mobile abre e fecha ao selecionar uma seção; perguntas frequentes abrem normalmente.
- Em produção: título correto, uma descrição, três painéis da demonstração com apenas um visível, âncoras válidas e nenhum erro de console observado.
- Navegação pública para os formulários existentes de cadastro e login confirmada; nenhuma conta criada ou autenticação submetida.

## Publicação e reversão

Código entregue por arquivo tar contendo apenas os arquivos desta mudança em `/opt/smartlawer`. A alteração preexistente no servidor em `enable-ssl.sh` foi preservada. Não houve push ou merge no GitHub; as mudanças de código permanecem nas árvores de trabalho local e da VPS.

Build: `sudo docker compose -f docker-compose.prod.yml build frontend`.

Ativação: `sudo docker compose -f docker-compose.prod.yml up -d --no-deps frontend`.

Imagem anterior preservada como `smartlawer-frontend:before-landing-20260924`. Os três arquivos de páginas anteriores foram copiados para `/home/ubuntu/smartlawer-backups/landing-20260924/`. Não foram executadas migrações nem reiniciados API, worker, banco ou Redis nesta entrega.

Para reversão imediata do frontend, retaggear a imagem preservada como `smartlawer-frontend:latest` e recriar somente o serviço frontend com `--no-deps --force-recreate`. Restaurar os arquivos de páginas da cópia de segurança antes de um novo build para manter código e imagem consistentes.
