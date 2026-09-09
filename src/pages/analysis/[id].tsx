import Head from 'next/head';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { useCallback, useEffect, useState } from 'react';
import axios from 'axios';
import AuthGuard from '../../components/auth/AuthGuard';
import Layout from '../../components/layout';
import api, { getApiErrorMessage, normalizeApiPath } from '../../lib/axios';
import type {
  AnalysisDetailResponse,
  AnalysisNotReadyDetail,
  GeneratedVersion,
  NormalizedAnalysis,
  TemplateIncompatibilityDetail,
  UserTemplate,
} from '../../types/workflow';

const BASE_TEMPLATE_OPTION = '';

export default function AnalysisPage() {
  const router = useRouter();
  const routeId = Array.isArray(router.query.id) ? router.query.id[0] : router.query.id;

  const [analysis, setAnalysis] = useState<NormalizedAnalysis | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isDownloading, setIsDownloading] = useState(false);
  const [isDownloadingSummary, setIsDownloadingSummary] = useState(false);
  const [error, setError] = useState('');
  const [notReadyDetail, setNotReadyDetail] = useState<AnalysisNotReadyDetail | null>(null);
  const [templates, setTemplates] = useState<UserTemplate[]>([]);
  const [selectedTemplateId, setSelectedTemplateId] = useState<string>(BASE_TEMPLATE_OPTION);
  const [templatesHint, setTemplatesHint] = useState('');
  const [isUploadingTemplate, setIsUploadingTemplate] = useState(false);
  const [templateNotice, setTemplateNotice] = useState('');
  const [versions, setVersions] = useState<GeneratedVersion[]>([]);

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
        setError(getApiErrorMessage(fetchError, 'Não foi possível carregar a análise.'));
      } finally {
        setIsLoading(false);
      }
    };

    fetchAnalysis();
  }, [routeId]);

  useEffect(() => {
    const fetchTemplates = async () => {
      try {
        const response = await api.get<UserTemplate[]>('/templates');
        setTemplates(Array.isArray(response.data) ? response.data : []);
        setTemplatesHint('');
      } catch {
        setTemplates([]);
        setTemplatesHint('Could not load your templates — the default template stays available.');
      }
    };

    fetchTemplates();
  }, []);

  const fetchVersions = useCallback(async () => {
    if (!routeId) {
      return;
    }

    try {
      const response = await api.get<GeneratedVersion[]>(`/analysis/${routeId}/versions`);
      setVersions(Array.isArray(response.data) ? response.data : []);
    } catch {
      setVersions([]);
    }
  }, [routeId]);

  useEffect(() => {
    fetchVersions();
  }, [routeId, fetchVersions]);

  const handleTemplateUpload = async (file: File | undefined) => {
    if (!file || isUploadingTemplate) {
      return;
    }

    setIsUploadingTemplate(true);
    setTemplateNotice('');

    try {
      const formData = new FormData();
      formData.append('file', file);
      const response = await api.post<UserTemplate>('/templates', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      const uploaded = response.data;
      setTemplates((previous) => [uploaded, ...previous.filter((item) => item.id !== uploaded.id)]);
      setSelectedTemplateId(uploaded.id);
      const unsupported = uploaded.unsupportedPlaceholders || [];
      setTemplateNotice(
        unsupported.length > 0
          ? `Modelo enviado, mas estes campos não têm dado na análise e vão travar a geração: ${unsupported.join(', ')}.`
          : `Modelo "${uploaded.name}" enviado e selecionado.`,
      );
    } catch (uploadError) {
      setTemplateNotice(getApiErrorMessage(uploadError, 'Não foi possível enviar o modelo DOCX.'));
    } finally {
      setIsUploadingTemplate(false);
    }
  };

  const handleDownloadTemplate = async () => {
    if (!analysis || !routeId || isDownloading) {
      return;
    }

    setIsDownloading(true);
    setTemplateNotice('');

    try {
      const basePath = analysis.docxDownloadUrl || `/analysis/${routeId}/docx`;
      const downloadPath =
        selectedTemplateId !== BASE_TEMPLATE_OPTION
          ? `${basePath}${basePath.includes('?') ? '&' : '?'}template_id=${encodeURIComponent(selectedTemplateId)}`
          : basePath;
      const response = await api.get(normalizeApiPath(downloadPath), {
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
      fetchVersions();
    } catch (downloadError) {
      const incompatible = getTemplateIncompatibility(downloadError);
      if (incompatible) {
        setTemplateNotice(
          `Este modelo não serve para esta análise — campos desconhecidos: ${incompatible.join(', ')}. Use o modelo padrão ou suba um compatível.`,
        );
      } else {
        setError(getApiErrorMessage(downloadError, 'Não foi possível gerar o DOCX da defesa.'));
      }
    } finally {
      setIsDownloading(false);
    }
  };

  const handleDownloadSummary = async () => {
    if (!analysis || !routeId || isDownloadingSummary) {
      return;
    }

    setIsDownloadingSummary(true);

    try {
      const response = await api.get(`/analysis/${routeId}/summary.md`, {
        responseType: 'blob',
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute(
        'download',
        getFilenameFromHeaders(response.headers['content-disposition'], `${analysis.id}_summary`),
      );
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (summaryError) {
      setError(getApiErrorMessage(summaryError, 'Não foi possível baixar o resumo em Markdown.'));
    } finally {
      setIsDownloadingSummary(false);
    }
  };

  const handleDownloadVersion = async (version: GeneratedVersion) => {
    if (!routeId) {
      return;
    }

    try {
      const versionPath = version.downloadUrl || `/analysis/${routeId}/versions/${version.version}`;
      const response = await api.get(normalizeApiPath(versionPath), {
        responseType: 'blob',
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute(
        'download',
        getFilenameFromHeaders(response.headers['content-disposition'], `v${version.version}`),
      );
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (versionError) {
      setError(getApiErrorMessage(versionError, 'Não foi possível baixar essa versão gerada.'));
    }
  };

  const selectedTemplate =
    selectedTemplateId !== BASE_TEMPLATE_OPTION
      ? templates.find((template) => template.id === selectedTemplateId)
      : undefined;

  return (
    <AuthGuard>
      <Layout>
        <Head>
          <title>Análise da peça - SmartLawer</title>
        </Head>

        <div className="min-h-[calc(100vh-4rem)] px-4 py-10 text-slate-300 sm:px-6 lg:px-8">
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
                <p className="font-mono text-xs uppercase tracking-[0.32em] text-rose-300">Análise indisponível</p>
                <h1 className="mt-4 font-display text-3xl font-black text-rose-50">Ainda não abrimos esta análise</h1>
                <p className="mt-4 max-w-2xl text-sm leading-7 text-rose-100/90">{error}</p>
                {notReadyDetail && (
                  <div className="mt-5 rounded-2xl border border-rose-900/80 bg-black/10 p-4 text-sm text-rose-100/90">
                    <p>Estado: {notReadyDetail.status || 'PENDENTE'}</p>
                    {notReadyDetail.status_detail && <p className="mt-2">Detalhe: {notReadyDetail.status_detail}</p>}
                    {notReadyDetail.task_id && <p className="mt-2 font-mono text-xs">Tarefa: {notReadyDetail.task_id}</p>}
                  </div>
                )}
                <div className="mt-8 flex flex-col gap-3 sm:flex-row">
                  <button
                    type="button"
                    onClick={() => router.reload()}
                    className="inline-flex items-center justify-center rounded-full border border-rose-800 px-5 py-3 text-sm font-medium text-rose-100 transition-colors hover:bg-rose-900/40"
                  >
                    Tentar de novo
                  </button>
                  <Link
                    href="/dashboard"
                    className="inline-flex items-center justify-center rounded-full bg-slate-100 px-5 py-3 text-sm font-medium uppercase tracking-[0.24em] text-zinc-950"
                  >
                    Voltar ao painel
                  </Link>
                  {notReadyDetail?.task_id && (
                    <Link
                      href="/upload"
                      className="inline-flex items-center justify-center rounded-full border border-zinc-700 px-5 py-3 text-sm font-medium text-zinc-200 transition-colors hover:border-zinc-500 hover:bg-tribunal-900"
                    >
                      Ver processamento
                    </Link>
                  )}
                </div>
              </div>
            ) : !analysis ? (
              <div className="overflow-hidden rounded-[2rem] border border-zinc-800 bg-tribunal-900/70 px-8 py-12 shadow-2xl shadow-black/20">
                <p className="font-mono text-xs uppercase tracking-[0.32em] text-zinc-500">Sem registro</p>
                <h1 className="mt-4 font-display text-3xl font-black text-slate-100">Análise não encontrada</h1>
                <p className="mt-4 max-w-2xl text-sm leading-7 text-zinc-400">
                  O painel pode ainda estar aguardando o sistema. Volte à fila e atualize a lista de processos.
                </p>
                <Link
                  href="/dashboard"
                  className="mt-8 inline-flex items-center justify-center rounded-full bg-slate-100 px-5 py-3 text-sm font-medium uppercase tracking-[0.24em] text-zinc-950"
                >
                  Voltar ao painel
                </Link>
              </div>
            ) : (
              <div className="space-y-8">
                <section className="overflow-hidden rounded-[2rem] border border-zinc-800 bg-tribunal-900/70 shadow-2xl shadow-black/20">
                  <div className="border-b border-ouro-700/20 bg-[radial-gradient(circle_at_top_left,_rgba(201,162,39,0.12),_transparent_26%),radial-gradient(circle_at_top_right,_rgba(16,185,129,0.1),_transparent_24%)] px-8 py-10 sm:px-10">
                    <div className="flex flex-col gap-6 xl:flex-row xl:items-end xl:justify-between">
                      <div className="max-w-3xl">
                        <p className="font-mono text-xs uppercase tracking-[0.32em] text-ouro-400">Resultado da análise</p>
                        <h1 className="mt-4 font-display text-3xl font-black tracking-tight text-slate-50 sm:text-4xl">{analysis.title}</h1>
                        <p className="mt-3 text-sm leading-7 text-zinc-400">
                          Peça de origem: <span className="text-slate-200">{analysis.documentName}</span>
                        </p>
                      </div>

                      <div className="flex flex-col gap-3 sm:flex-row">
                        <Link
                          href="/dashboard"
                          className="inline-flex items-center justify-center rounded-full border border-zinc-700 px-5 py-3 text-sm font-medium text-zinc-300 transition-colors hover:border-zinc-500 hover:bg-tribunal-900 hover:text-slate-100"
                        >
                          Voltar à fila
                        </Link>
                        <button
                          type="button"
                          onClick={handleDownloadTemplate}
                          disabled={isDownloading}
                          className={`inline-flex items-center justify-center rounded-full px-6 py-3 text-sm font-bold uppercase tracking-[0.2em] transition-all ${
                            isDownloading
                              ? 'cursor-not-allowed bg-zinc-800 text-zinc-500'
                              : 'bg-ouro-500 text-tribunal-950 shadow-[0_0_24px_rgba(201,162,39,0.2)] hover:-translate-y-0.5 hover:bg-ouro-400'
                          }`}
                        >
                          {isDownloading ? 'Gerando DOCX...' : 'Baixar defesa DOCX'}
                        </button>
                        <button
                          type="button"
                          onClick={handleDownloadSummary}
                          disabled={isDownloadingSummary}
                          className="inline-flex items-center justify-center rounded-full border border-zinc-700 px-5 py-3 text-sm font-medium text-zinc-200 transition-colors hover:border-zinc-500 hover:bg-tribunal-900 disabled:cursor-not-allowed disabled:text-zinc-500"
                        >
                          {isDownloadingSummary ? 'Preparando...' : 'Resumo (.md)'}
                        </button>
                      </div>
                    </div>
                  </div>

                  <div className="border-b border-zinc-800 px-8 py-6 sm:px-10">
                    <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
                      <div className="max-w-2xl">
                        <h2 className="font-mono text-sm font-medium uppercase tracking-[0.28em] text-zinc-300">Modelo da peça</h2>
                        <p className="mt-2 text-sm leading-7 text-zinc-400">
                          {selectedTemplate?.name
                            ? `Gerando com "${selectedTemplate.name}" (${selectedTemplate.placeholders?.length || 0} campos).`
                            : 'Gerando com o modelo padrão de defesa.'}
                        </p>
                      </div>
                      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
                        <select
                          value={selectedTemplateId}
                          onChange={(event) => {
                            setSelectedTemplateId(event.target.value);
                            setTemplateNotice('');
                          }}
                          className="rounded-full border border-zinc-700 bg-tribunal-950 px-4 py-2.5 text-sm text-slate-200 outline-none transition-colors hover:border-zinc-500 focus:border-ouro-500"
                          aria-label="Escolher modelo DOCX"
                        >
                          <option value={BASE_TEMPLATE_OPTION}>Modelo padrão</option>
                          {templates.map((template) => (
                            <option key={template.id} value={template.id}>
                              {template.name}
                              {(template.unsupportedPlaceholders?.length || 0) > 0 ? ' (incompatível)' : ''}
                            </option>
                          ))}
                        </select>
                        <label className="inline-flex cursor-pointer items-center justify-center rounded-full border border-zinc-700 px-5 py-2.5 text-sm font-medium text-zinc-200 transition-colors hover:border-zinc-500 hover:bg-tribunal-900">
                          {isUploadingTemplate ? 'Enviando...' : 'Enviar .docx'}
                          <input
                            type="file"
                            accept=".docx,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                            className="hidden"
                            disabled={isUploadingTemplate}
                            onChange={(event) => {
                              handleTemplateUpload(event.target.files?.[0]);
                              event.target.value = '';
                            }}
                          />
                        </label>
                      </div>
                    </div>
                    {(templatesHint || templateNotice) && (
                      <p className="mt-3 text-sm leading-7 text-amber-200/90">{templateNotice || templatesHint}</p>
                    )}
                  </div>

                  {versions.length > 0 && (
                    <div className="border-b border-zinc-800 px-8 py-6 sm:px-10">
                      <h2 className="font-mono text-sm font-medium uppercase tracking-[0.28em] text-zinc-300">
                        Versões anteriores ({versions.length})
                      </h2>
                      <ul className="mt-4 flex flex-wrap gap-3">
                        {versions.map((version) => (
                          <li key={version.version}>
                            <button
                              type="button"
                              onClick={() => handleDownloadVersion(version)}
                              className="inline-flex items-center gap-2 rounded-full border border-zinc-700 px-4 py-2 text-sm text-zinc-200 transition-colors hover:border-ouro-600/60 hover:bg-tribunal-900"
                            >
                              v{version.version}
                              {version.created_at && (
                                <span className="text-xs text-zinc-500">
                                  {new Date(version.created_at).toLocaleString('pt-BR')}
                                </span>
                              )}
                            </button>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  <div className="grid gap-8 px-8 py-8 sm:px-10 lg:grid-cols-[minmax(0,0.95fr)_minmax(0,1.05fr)]">
                    <div className="space-y-6">
                      <Panel title="Resumo executivo" accent="ouro">
                        <p className="text-sm leading-7 text-slate-300">
                          {analysis.summary || 'O sistema devolveu um resumo vazio para esta análise.'}
                        </p>
                      </Panel>

                      <Panel title="Pedidos e argumentos" accent="emerald">
                        <BulletList
                          items={analysis.keyArguments.length > 0 ? analysis.keyArguments : analysis.requests}
                          emptyState="Nenhum pedido ou argumento extraído para esta análise."
                        />
                      </Panel>

                      <Panel title="Leis citadas" accent="amber">
                        <BulletList
                          items={analysis.laws}
                          emptyState="O sistema não incluiu referências legais neste resultado."
                        />
                      </Panel>

                      <Panel title="Provas" accent="zinc">
                        <BulletList
                          items={analysis.evidence}
                          emptyState="Sem detalhes estruturados de prova."
                        />
                      </Panel>
                    </div>

                    <div className="space-y-6">
                      <Panel title="Teses de defesa" accent="emerald">
                        <NumberedList
                          items={analysis.defenseTheses}
                          emptyState="Nenhuma tese defensiva foi produzida para esta análise."
                        />
                      </Panel>

                      <Panel title="Estratégia de defesa gerada" accent="ouro">
                        <div className="rounded-[1.5rem] border border-ouro-700/30 bg-tribunal-950/70 p-5">
                          <p className="whitespace-pre-wrap text-sm leading-8 text-slate-300">
                            {analysis.generatedDefenseStrategy || 'O sistema ainda não devolveu o texto da estratégia.'}
                          </p>
                        </div>
                      </Panel>

                      <Panel title="Rastreabilidade" accent="zinc">
                        <dl className="grid gap-4 sm:grid-cols-2">
                          <MetaItem label="Análise" value={analysis.id} />
                          <MetaItem label="Documento" value={analysis.documentId} />
                          <MetaItem label="Rota de download" value={analysis.docxDownloadUrl || `/analysis/${analysis.id}/docx`} />
                          <MetaItem label="Peça de origem" value={analysis.title} />
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
  accent: 'ouro' | 'emerald' | 'amber' | 'zinc';
}) {
  const accentClass = {
    ouro: 'text-ouro-300',
    emerald: 'text-emerald-300',
    amber: 'text-amber-300',
    zinc: 'text-zinc-300',
  }[accent];

  return (
    <section className="rounded-[1.75rem] border border-zinc-800 bg-tribunal-900/70 p-6 shadow-xl shadow-black/10">
      <div className="mb-5 flex items-center justify-between border-b border-zinc-800 pb-4">
        <h2 className={`font-mono text-sm font-medium uppercase tracking-[0.28em] ${accentClass}`}>{title}</h2>
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
          <span className="mt-2 inline-flex h-2.5 w-2.5 flex-shrink-0 rounded-full bg-ouro-400" />
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

function getTemplateIncompatibility(error: unknown): string[] | null {
  if (!axios.isAxiosError(error)) {
    return null;
  }

  const detail = error.response?.data?.detail as TemplateIncompatibilityDetail | undefined;
  const offenders = detail?.unsupported_placeholders;
  if (Array.isArray(offenders) && offenders.length > 0) {
    return offenders.map(String);
  }

  return null;
}

function getFilenameFromHeaders(contentDisposition: string | undefined, fallbackId: string) {
  const match = contentDisposition?.match(/filename="?([^"]+)"?/i);
  if (match?.[1]) {
    return match[1];
  }

  return `Defense_${fallbackId}.docx`;
}
