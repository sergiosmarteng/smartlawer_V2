/**
 * Contrato do Dossiê Universal V3 (Onda 0 Task 13).
 *
 * Espelha `backend/app/core/schemas_v3.py` (schema 3.0). Nenhum componente
 * de apresentação deriva tese, estratégia, risco ou argumento a partir
 * de pedidos — tudo vem do artefato publicado.
 */

export type SectionStatus =
  "complete" | "partial" | "blocked" | "not_applicable";
export type ArtifactStatus = "completed" | "partial" | "blocked" | "failed";
export type ReviewStatus = "pending" | "in_review" | "approved" | "rejected";

export interface SectionCoverage {
  items_expected?: number | null;
  items_found: number;
  items_verified: number;
}

export interface SectionState {
  status: SectionStatus;
  reason: string;
  coverage: SectionCoverage;
  pending_actions: string[];
}

export interface DossierArtifactV3 {
  id: string;
  run_id: string;
  schema_version: string;
  status: ArtifactStatus;
  review_status: ReviewStatus;
  content: Record<string, unknown>;
  content_hash?: string | null;
  legacy?: boolean;
  reanalyze_available?: boolean;
}

export interface RunStage {
  stage: string;
  done: boolean;
}

export interface AnalysisRunStatus {
  run_id: string;
  status: string;
  stage?: string | null;
  progress: number;
  version: number;
  stages: RunStage[];
  error_code?: string | null;
  error_message?: string | null;
  artifact_id?: string | null;
}

export interface SafeApiError {
  code: string;
  stage?: string | null;
  retryable: boolean;
  user_message: string;
  correlation_id: string;
}

const TERMINAL_RUN_STATUSES = new Set([
  "completed",
  "partial",
  "failed",
  "cancelled",
]);

/** Execução terminou: polling deve parar. */
export function isTerminalRunStatus(
  status: string | null | undefined,
): boolean {
  return TERMINAL_RUN_STATUSES.has(status ?? "");
}

/** Progresso honesto: extração nunca exibe 100%. */
export function honestProgress(
  progress: number,
  stage?: string | null,
): number {
  if (stage === "extraction" && progress >= 100) return 95;
  return progress;
}

/** Mensagem PT-BR a partir de erro seguro do backend (sem detalhe técnico). */
export function toUserMessage(error: unknown): string {
  if (error && typeof error === "object" && "user_message" in error) {
    const message = (error as { user_message?: unknown }).user_message;
    if (typeof message === "string" && message.trim()) return message;
  }
  return "Não foi possível carregar o dossiê. Tente novamente.";
}
