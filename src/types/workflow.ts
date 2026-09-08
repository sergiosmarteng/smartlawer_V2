/**
 * Shared workflow contract types (B5 frontend hygiene).
 *
 * Single source of truth for the pilot path
 * `upload -> /tasks/{id} -> /processes -> /analysis/{id} -> /docx`,
 * mirroring `docs/coordination/api-contract.md` and the backend
 * `app/schemas/workflow.py` shapes. Pages must import from here
 * instead of redeclaring inline interfaces.
 */

/** `POST /api/v1/documents/upload` response. */
export interface UploadResponse {
  id: string;
  task_id?: string;
  taskStatusUrl?: string;
  status: string;
}

/**
 * `GET /api/v1/tasks/{task_id}` response.
 *
 * BL-014 identity rule: `task_id == document_id` by design — one
 * document owns exactly one pipeline (single `Analysis` per document).
 */
export interface TaskStatusResponse {
  task_id?: string;
  document_id?: string;
  status?: string;
  progress?: number;
  analysis_id?: string | null;
  status_detail?: string | null;
  error_message?: string | null;
}

/** `GET /api/v1/processes` item (dashboard source of truth). */
export interface ProcessItem {
  id: string;
  analysis_id?: string | null;
  title: string;
  status: string;
  created_at?: string;
  status_detail?: string | null;
}

/** `GET /api/v1/analysis/{id}` response (camel + snake tolerant). */
export interface AnalysisDetailResponse {
  id: string;
  document_id: string;
  documentName?: string;
  document_name?: string;
  title: string;
  summary: string;
  keyArguments?: string[];
  key_arguments?: string[];
  requests?: string[];
  laws?: string[];
  evidence?: unknown;
  defense_theses?: string[];
  generatedDefenseStrategy?: string;
  generated_defense_strategy?: string;
  docxDownloadUrl?: string | null;
  docx_download_url?: string | null;
}

/** Normalized analysis shape used by the analysis page UI. */
export interface NormalizedAnalysis {
  id: string;
  documentId: string;
  documentName: string;
  title: string;
  summary: string;
  keyArguments: string[];
  requests: string[];
  laws: string[];
  evidence: string[];
  defenseTheses: string[];
  generatedDefenseStrategy: string;
  docxDownloadUrl: string | null;
}

/** Structured `404 analysis-not-ready` detail from the backend. */
export interface AnalysisNotReadyDetail {
  message?: string;
  task_id?: string;
  status?: string;
  status_detail?: string;
}

/**
 * `GET /api/v1/templates` item (C1 template MVP).
 *
 * `unsupportedPlaceholders` names `{{roots}}` with no normalized analysis
 * context key — generation with such a template fails with 422.
 */
export interface UserTemplate {
  id: string;
  name: string;
  placeholders?: string[];
  unsupportedPlaceholders?: string[];
  created_at?: string;
}

/** Structured `422 incompatible-template` detail from the backend. */
export interface TemplateIncompatibilityDetail {
  message?: string;
  unsupported_placeholders?: string[];
  supported_keys?: string[];
}

/** `GET /api/v1/analysis/{id}/versions` item (C2 generation history). */
export interface GeneratedVersion {
  version: number;
  template_id?: string | null;
  created_at?: string;
  downloadUrl?: string | null;
}

const ACTIVE_STATUSES = new Set(['PENDING', 'PROCESSING', 'STARTED', 'RETRY']);
const SUCCESS_STATUSES = new Set(['SUCCESS', 'COMPLETED', 'DONE']);
const FAILURE_STATUSES = new Set(['FAILURE', 'FAILED', 'ERROR']);

export function normalizeWorkflowStatus(status?: string | null): string {
  return (status || 'PENDING').toUpperCase();
}

export function isActiveStatus(status?: string | null): boolean {
  return ACTIVE_STATUSES.has(normalizeWorkflowStatus(status));
}

export function isSuccessStatus(status?: string | null): boolean {
  return SUCCESS_STATUSES.has(normalizeWorkflowStatus(status));
}

export function isFailureStatus(status?: string | null): boolean {
  return FAILURE_STATUSES.has(normalizeWorkflowStatus(status));
}
