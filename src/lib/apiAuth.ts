/**
 * Cabeçalho de autenticação para `fetch` direto (hooks do dossiê).
 *
 * Os hooks `useDossier`/`useAnalysisRun` usam `fetch` global em vez do
 * cliente axios — sem este header, o backend responde 401 e a página do
 * dossiê nunca carrega no navegador. Mesma chave (`access_token`) e
 * mesmo formato (`Bearer`) do interceptor em `src/lib/axios.ts`.
 */
export function bearerHeaders(): Record<string, string> {
  if (typeof window === "undefined") return {};
  const token = window.localStorage.getItem("access_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}
