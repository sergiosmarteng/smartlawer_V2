import { useCallback, useEffect, useRef, useState } from "react";
import { DossierArtifactV3, toUserMessage } from "@/types/dossier";

export interface UseDossierInput {
  artifactId?: string;
  documentId?: string;
}

export interface UseDossierResult {
  artifact: DossierArtifactV3 | null;
  isLegacy: boolean;
  loading: boolean;
  errorMessage: string | null;
  reload: () => void;
}

async function fetchJson(
  input: string,
  init?: RequestInit,
): Promise<{ status: number; etag: string | null; body: unknown }> {
  const response = await fetch(input, init);
  const etag = response.headers.get("etag");
  if (response.status === 304) return { status: 304, etag, body: null };
  if (!response.ok) {
    let detail: unknown = null;
    try {
      detail = (await response.json())?.detail ?? null;
    } catch {
      detail = null;
    }
    throw (
      detail ?? {
        code: "REQUEST_FAILED",
        user_message: "Não foi possível carregar o dossiê. Tente novamente.",
      }
    );
  }
  return { status: response.status, etag, body: await response.json() };
}

/**
 * Acesso centralizado ao artefato do dossiê (Onda 0 Task 13).
 *
 * Resolve `documentId` para o último artefato publicado, preserva conteúdo
 * anterior em 304 (ETag) e nunca deixa componente fazer fetch direto.
 */
export function useDossier(input: UseDossierInput): UseDossierResult {
  const [artifact, setArtifact] = useState<DossierArtifactV3 | null>(null);
  const [loading, setLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const etagRef = useRef<string | null>(null);
  const [nonce, setNonce] = useState(0);

  const reload = useCallback(() => setNonce((n) => n + 1), []);

  useEffect(() => {
    let cancelled = false;
    async function resolveByDocument(documentId: string) {
      const runs = await fetchJson(
        `/api/v2/analysis-runs?document_id=${encodeURIComponent(documentId)}`,
      );
      const list = (runs.body as Array<{ artifact_id?: string | null }>) ?? [];
      const resolved = list.find((r) => r.artifact_id)?.artifact_id ?? null;
      if (!resolved)
        throw {
          code: "NOT_FOUND",
          user_message: "Nenhuma análise publicada para este documento.",
        };
      return resolved;
    }
    async function load() {
      setLoading(true);
      setErrorMessage(null);
      try {
        let resolvedId = input.artifactId ?? null;
        if (!resolvedId && input.documentId) {
          resolvedId = await resolveByDocument(input.documentId);
        }
        if (!resolvedId)
          throw {
            code: "NOT_FOUND",
            user_message: "Informe o documento ou a análise.",
          };
        const headers: Record<string, string> = {};
        if (etagRef.current) headers["If-None-Match"] = etagRef.current;
        let result: Awaited<ReturnType<typeof fetchJson>>;
        try {
          result = await fetchJson(
            `/api/v2/analyses/${encodeURIComponent(resolvedId)}`,
            { headers },
          );
        } catch (error) {
          // routeId pode ser um document_id (link "Abrir dossiê"), com ou
          // sem ?document_id=: 404 no artefato resolve pela última execução
          // publicada do documento.
          const code =
            error && typeof error === "object"
              ? (error as { code?: unknown }).code
              : null;
          const documentCandidate = input.documentId ?? input.artifactId;
          if (code !== "NOT_FOUND" || !documentCandidate) throw error;
          resolvedId = await resolveByDocument(documentCandidate);
          result = await fetchJson(
            `/api/v2/analyses/${encodeURIComponent(resolvedId)}`,
            { headers },
          );
        }
        if (cancelled) return;
        if (result.status === 304) {
          // Mantém conteúdo anterior (cache válido).
          setLoading(false);
          return;
        }
        if (result.etag) etagRef.current = result.etag;
        setArtifact(result.body as DossierArtifactV3);
      } catch (error) {
        if (!cancelled) setErrorMessage(toUserMessage(error));
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    void load();
    return () => {
      cancelled = true;
    };
  }, [input.artifactId, input.documentId, nonce]);

  return {
    artifact,
    isLegacy: (artifact?.schema_version ?? "") !== "3.0",
    loading,
    errorMessage,
    reload,
  };
}
