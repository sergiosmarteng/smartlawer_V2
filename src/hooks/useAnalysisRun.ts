import { useEffect, useState } from "react";
import {
  AnalysisRunStatus,
  honestProgress,
  isTerminalRunStatus,
  toUserMessage,
} from "@/types/dossier";
import { bearerHeaders } from "@/lib/apiAuth";

export interface UseAnalysisRunResult {
  run: AnalysisRunStatus | null;
  progress: number;
  loading: boolean;
  errorMessage: string | null;
}

const POLL_INTERVAL_MS = 2500;

/**
 * Polling mensurável da execução (Onda 0 Task 13).
 *
 * Para em estado terminal; progresso de extração nunca aparece como 100%;
 * erro seguro do backend vira mensagem em português.
 */
export function useAnalysisRun(runId?: string): UseAnalysisRunResult {
  const [run, setRun] = useState<AnalysisRunStatus | null>(null);
  const [loading, setLoading] = useState(Boolean(runId));
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!runId) {
      setLoading(false);
      return;
    }
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout> | null = null;

    async function poll() {
      try {
        const response = await fetch(
          `/api/v2/analysis-runs/${encodeURIComponent(runId as string)}`,
          { headers: bearerHeaders() },
        );
        if (!response.ok) {
          let detail: unknown = null;
          try {
            detail = (await response.json())?.detail ?? null;
          } catch {
            detail = null;
          }
          throw detail ?? { code: "REQUEST_FAILED" };
        }
        const body = (await response.json()) as AnalysisRunStatus;
        if (cancelled) return;
        setRun(body);
        setLoading(false);
        if (!isTerminalRunStatus(body.status)) {
          timer = setTimeout(poll, POLL_INTERVAL_MS);
        }
      } catch (error) {
        if (!cancelled) {
          setErrorMessage(toUserMessage(error));
          setLoading(false);
        }
      }
    }

    void poll();
    return () => {
      cancelled = true;
      if (timer) clearTimeout(timer);
    };
  }, [runId]);

  return {
    run,
    progress: run ? honestProgress(run.progress, run.stage) : 0,
    loading,
    errorMessage,
  };
}
