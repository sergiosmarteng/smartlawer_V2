import Head from 'next/head';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { useEffect, useState } from 'react';
import axios from 'axios';
import AuthGuard from '../../components/auth/AuthGuard';
import Layout from '../../components/layout';
import api, { getApiErrorMessage, normalizeApiPath } from '../../lib/axios';

interface AnalysisDetailResponse {
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

interface NormalizedAnalysis {
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

interface AnalysisNotReadyDetail {
  message?: string;
  task_id?: string;
  status?: string;
  status_detail?: string;
}

export default function AnalysisPage() {
  const router = useRouter();
  const routeId = Array.isArray(router.query.id) ? router.query.id[0] : router.query.id;

  const [analysis, setAnalysis] = useState<NormalizedAnalysis | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isDownloading, setIsDownloading] = useState(false);
  const [error, setError] = useState('');
  const [notReadyDetail, setNotReadyDetail] = useState<AnalysisNotReadyDetail | null>(null);

  useEffect(() => {
    if (!routeId) {
      return;
    }

    const fetchAnalysis = async () => {
      setIsLoading(true);
      setError('');

      try {
        const response = await api.get<AnalysisDetailResponse>(`/analysis/${routeId}`);
        setAnalysis(normalizeAnalysis(response.data));
        setNotReadyDetail(null);
      } catch (fetchError) {
        setAnalysis(null);
        setNotReadyDetail(getAnalysisNotReadyDetail(fetchError));
        setError(getApiErrorMessage(fetchError, 'Failed to load analysis data.'));
      } finally {
        setIsLoading(false);
      }
    };

    fetchAnalysis();
  }, [routeId]);

  const handleDownloadTemplate = async () => {
    if (!analysis || !routeId || isDownloading) {
      return;
    }

    setIsDownloading(true);

    try {
      const downloadPath = normalizeApiPath(analysis.docxDownloadUrl || `/analysis/${routeId}/docx`);
      const response = await api.get(downloadPath, {
        responseType: 'blob',
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', getFilenameFromHeaders(response.headers['content-disposition'], analysis.id));
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (downloadError) {
      setError(getApiErrorMessage(downloadError, 'Failed to generate the DOCX defense file.'));
    } finally {
      setIsDownloading(false);
    }
  };

  return (
    <AuthGuard>
      <Layout>
        <Head>
          <title>AI Analysis - SmartLawer</title>
        </Head>

        <div className="min-h-[calc(100vh-4rem)] bg-zinc-950 px-4 py-10 text-slate-300 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-7xl">
            {isLoading ? (
              <div className="overflow-hidden rounded-[2rem] border border-zinc-800 bg-zinc-900 px-8 py-16 shadow-2xl shadow-black/20">
                <div className="animate-pulse space-y-5">
                  <div className="h-3 w-40 rounded bg-zinc-800" />
                  <div className="h-10 w-3/5 rounded bg-zinc-800" />
                  <div className="h-4 w-2/5 rounded bg-zinc-800" />
                  <div className="grid gap-6 pt-8 lg:grid-cols-2">
                    <div className="space-y-4 rounded-[1.75rem] border border-zinc-800 bg-zinc-950/60 p-6">
                      <div className="h-5 w-36 rounded bg-zinc-800" />
                      <div className="h-24 rounded bg-zinc-900" />
                    </div>
                    <div className="space-y-4 rounded-[1.75rem] border border-zinc-800 bg-zinc-950/60 p-6">
                      <div className="h-5 w-44 rounded bg-zinc-800" />
                      <div className="h-24 rounded bg-zinc-900" />
                    </div>
                  </div>
                </div>
              </div>
            ) : error ? (
              <div className="overflow-hidden rounded-[2rem] border border-rose-900/80 bg-rose-950/50 px-8 py-12 shadow-2xl shadow-black/20">
                <p className="text-xs uppercase tracking-[0.32em] text-rose-300">Analysis unavailable</p>
                <h1 className="mt-4 text-3xl font-light text-rose-50">We could not open this analysis yet</h1>
                <p className="mt-4 max-w-2xl text-sm leading-7 text-rose-100/90">{error}</p>
                {notReadyDetail && (
                  <div className="mt-5 rounded-2xl border border-rose-900/80 bg-black/10 p-4 text-sm text-rose-100/90">
                    <p>Status: {notReadyDetail.status || 'PENDING'}</p>
                    {notReadyDetail.status_detail && <p className="mt-2">Worker detail: {notReadyDetail.status_detail}</p>}
                    {notReadyDetail.task_id && <p className="mt-2">Task ID: {notReadyDetail.task_id}</p>}
                  </div>
                )}
                <div className="mt-8 flex flex-col gap-3 sm:flex-row">
                  <button
                    type="button"
                    onClick={() => router.reload()}
                    className="inline-flex items-center justify-center rounded-full border border-rose-800 px-5 py-3 text-sm font-medium text-rose-100 transition-colors hover:bg-rose-900/40"
                  >
                    Retry fetch
                  </button>
                  <Link
                    href="/dashboard"
                    className="inline-flex items-center justify-center rounded-full bg-slate-100 px-5 py-3 text-sm font-medium uppercase tracking-[0.24em] text-zinc-950"
                  >
                    Back to dashboard
                  </Link>
                  {notReadyDetail?.task_id && (
                    <Link
                      href="/upload"
                      className="inline-flex items-center justify-center rounded-full border border-zinc-700 px-5 py-3 text-sm font-medium text-zinc-200 transition-colors hover:border-zinc-500 hover:bg-zinc-900"
                    >
                      Back to processing
                    </Link>
                  )}
                </div>
              </div>
            ) : !analysis ? (
              <div className="overflow-hidden rounded-[2rem] border border-zinc-800 bg-zinc-900 px-8 py-12 shadow-2xl shadow-black/20">
                <p className="text-xs uppercase tracking-[0.32em] text-zinc-500">No analysis record</p>
                <h1 className="mt-4 text-3xl font-light text-slate-100">This analysis was not found</h1>
                <p className="mt-4 max-w-2xl text-sm leading-7 text-zinc-400">
                  The dashboard may still be waiting for an `analysis_id` from the backend. Return to the queue and refresh the process list.
                </p>
                <Link
                  href="/dashboard"
                  className="mt-8 inline-flex items-center justify-center rounded-full bg-slate-100 px-5 py-3 text-sm font-medium uppercase tracking-[0.24em] text-zinc-950"
                >
                  Back to dashboard
                </Link>
              </div>
            ) : (
              <div className="space-y-8">
                <section className="overflow-hidden rounded-[2rem] border border-zinc-800 bg-zinc-900 shadow-2xl shadow-black/20">
                  <div className="border-b border-zinc-800 bg-[radial-gradient(circle_at_top_left,_rgba(16,185,129,0.14),_transparent_26%),radial-gradient(circle_at_top_right,_rgba(56,189,248,0.14),_transparent_24%)] px-8 py-10 sm:px-10">
                    <div className="flex flex-col gap-6 xl:flex-row xl:items-end xl:justify-between">
                      <div className="max-w-3xl">
                        <p className="text-xs uppercase tracking-[0.32em] text-emerald-300">Analysis detail</p>
                        <h1 className="mt-4 text-3xl font-light tracking-tight text-slate-100 sm:text-4xl">{analysis.title}</h1>
                        <p className="mt-3 text-sm leading-7 text-zinc-400">
                          Source document: <span className="text-slate-200">{analysis.documentName}</span>
                        </p>
                      </div>

                      <div className="flex flex-col gap-3 sm:flex-row">
                        <Link
                          href="/dashboard"
                          className="inline-flex items-center justify-center rounded-full border border-zinc-800 px-5 py-3 text-sm font-medium text-zinc-300 transition-colors hover:border-zinc-700 hover:bg-zinc-900 hover:text-slate-100"
                        >
                          Back to queue
                        </Link>
                        <button
                          type="button"
                          onClick={handleDownloadTemplate}
                          disabled={isDownloading}
                          className={`inline-flex items-center justify-center rounded-full px-6 py-3 text-sm font-medium uppercase tracking-[0.24em] transition-all ${
                            isDownloading
                              ? 'cursor-not-allowed bg-zinc-800 text-zinc-500'
                              : 'bg-slate-100 text-zinc-950 shadow-[0_0_24px_rgba(255,255,255,0.08)] hover:-translate-y-0.5 hover:shadow-[0_0_36px_rgba(255,255,255,0.14)]'
                          }`}
                        >
                          {isDownloading ? 'Generating DOCX...' : 'Download DOCX defense'}
                        </button>
                      </div>
                    </div>
                  </div>

                  <div className="grid gap-8 px-8 py-8 sm:px-10 lg:grid-cols-[minmax(0,0.95fr)_minmax(0,1.05fr)]">
                    <div className="space-y-6">
                      <Panel title="Execution summary" accent="sky">
                        <p className="text-sm leading-7 text-slate-300">
                          {analysis.summary || 'The backend returned an empty summary for this analysis.'}
                        </p>
                      </Panel>

                      <Panel title="Requests and arguments" accent="emerald">
                        <BulletList
                          items={analysis.keyArguments.length > 0 ? analysis.keyArguments : analysis.requests}
                          emptyState="No requests or extracted arguments were returned for this analysis."
                        />
                      </Panel>

                      <Panel title="Referenced laws" accent="amber">
                        <BulletList
                          items={analysis.laws}
                          emptyState="The backend did not include any law references in this payload."
                        />
                      </Panel>

                      <Panel title="Evidence signals" accent="zinc">
                        <BulletList
                          items={analysis.evidence}
                          emptyState="No structured evidence details were returned."
                        />
                      </Panel>
                    </div>

                    <div className="space-y-6">
                      <Panel title="Defense theses" accent="emerald">
                        <NumberedList
                          items={analysis.defenseTheses}
                          emptyState="No defense theses were produced for this analysis."
                        />
                      </Panel>

                      <Panel title="Generated defense strategy" accent="sky">
                        <div className="rounded-[1.5rem] border border-zinc-800 bg-zinc-950/70 p-5">
                          <p className="whitespace-pre-wrap text-sm leading-8 text-slate-300">
                            {analysis.generatedDefenseStrategy || 'The backend did not return generated strategy text yet.'}
                          </p>
                        </div>
                      </Panel>

                      <Panel title="Traceability" accent="zinc">
                        <dl className="grid gap-4 sm:grid-cols-2">
                          <MetaItem label="Analysis ID" value={analysis.id} />
                          <MetaItem label="Document ID" value={analysis.documentId} />
                          <MetaItem label="Download route" value={analysis.docxDownloadUrl || `/analysis/${analysis.id}/docx`} />
                          <MetaItem label="Source title" value={analysis.title} />
                        </dl>
                      </Panel>
                    </div>
                  </div>
                </section>
              </div>
            )}
          </div>
        </div>
      </Layout>
    </AuthGuard>
  );
}

function normalizeAnalysis(payload: AnalysisDetailResponse): NormalizedAnalysis {
  return {
    id: payload.id,
    documentId: payload.document_id,
    documentName: payload.documentName || payload.document_name || payload.title,
    title: payload.title,
    summary: payload.summary || '',
    keyArguments: payload.keyArguments || payload.key_arguments || [],
    requests: payload.requests || [],
    laws: payload.laws || [],
    evidence: normalizeEvidence(payload.evidence),
    defenseTheses: payload.defense_theses || [],
    generatedDefenseStrategy: payload.generatedDefenseStrategy || payload.generated_defense_strategy || '',
    docxDownloadUrl: payload.docxDownloadUrl || payload.docx_download_url || null,
  };
}

function getAnalysisNotReadyDetail(error: unknown): AnalysisNotReadyDetail | null {
  if (!axios.isAxiosError(error)) {
    return null;
  }

  const detail = error.response?.data?.detail;
  if (!detail || typeof detail !== 'object') {
    return null;
  }

  return {
    message: typeof detail.message === 'string' ? detail.message : undefined,
    task_id: typeof detail.task_id === 'string' ? detail.task_id : undefined,
    status: typeof detail.status === 'string' ? detail.status : undefined,
    status_detail: typeof detail.status_detail === 'string' ? detail.status_detail : undefined,
  };
}

function normalizeEvidence(evidence: unknown) {
  if (!evidence) {
    return [];
  }

  if (Array.isArray(evidence)) {
    return evidence.map((item) => String(item));
  }

  if (typeof evidence === 'object') {
    return Object.entries(evidence as Record<string, unknown>).map(([key, value]) => `${key}: ${String(value)}`);
  }

  return [String(evidence)];
}

function Panel({
  title,
  children,
  accent,
}: {
  title: string;
  children: React.ReactNode;
  accent: 'sky' | 'emerald' | 'amber' | 'zinc';
}) {
  const accentClass = {
    sky: 'text-sky-300',
    emerald: 'text-emerald-300',
    amber: 'text-amber-300',
    zinc: 'text-zinc-300',
  }[accent];

  return (
    <section className="rounded-[1.75rem] border border-zinc-800 bg-zinc-900/70 p-6 shadow-xl shadow-black/10">
      <div className="mb-5 flex items-center justify-between border-b border-zinc-800 pb-4">
        <h2 className={`text-sm font-medium uppercase tracking-[0.28em] ${accentClass}`}>{title}</h2>
      </div>
      {children}
    </section>
  );
}

function BulletList({ items, emptyState }: { items: string[]; emptyState: string }) {
  if (items.length === 0) {
    return <p className="text-sm leading-7 text-zinc-500">{emptyState}</p>;
  }

  return (
    <ul className="space-y-3">
      {items.map((item, index) => (
        <li key={`${item}-${index}`} className="flex items-start gap-3 text-sm leading-7 text-slate-300">
          <span className="mt-2 inline-flex h-2.5 w-2.5 flex-shrink-0 rounded-full bg-sky-400" />
          <span>{item}</span>
        </li>
      ))}
    </ul>
  );
}

function NumberedList({ items, emptyState }: { items: string[]; emptyState: string }) {
  if (items.length === 0) {
    return <p className="text-sm leading-7 text-zinc-500">{emptyState}</p>;
  }

  return (
    <ol className="space-y-4">
      {items.map((item, index) => (
        <li key={`${item}-${index}`} className="flex items-start gap-4">
          <span className="inline-flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-full border border-emerald-800 bg-emerald-900/30 text-xs font-medium text-emerald-300">
            {index + 1}
          </span>
          <span className="text-sm leading-7 text-slate-300">{item}</span>
        </li>
      ))}
    </ol>
  );
}

function MetaItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-zinc-800 bg-zinc-950/70 p-4">
      <dt className="text-xs uppercase tracking-[0.28em] text-zinc-500">{label}</dt>
      <dd className="mt-2 break-all text-sm leading-7 text-slate-300">{value}</dd>
    </div>
  );
}

function getFilenameFromHeaders(contentDisposition: string | undefined, fallbackId: string) {
  const match = contentDisposition?.match(/filename="?([^"]+)"?/i);
  if (match?.[1]) {
    return match[1];
  }

  return `Defense_${fallbackId}.docx`;
}
