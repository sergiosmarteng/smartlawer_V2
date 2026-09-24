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

        <div className="min-h-[calc(100vh-4rem)] bg-papel px-4 py-10 text-tinta sm:px-6 lg:px-8">
          <div className="mx-auto max-w-7xl">
            {isLoading ? (
              <div className="overflow-hidden rounded-[5px] border border-linha bg-white px-8 py-16 shadow-[0_4px_10px_rgba(41,69,50,0.05)]">
                <div className="animate-pulse space-y-5">
                  <div className="h-3 w-40 rounded bg-papel-areia" />
                  <div className="h-10 w-3/5 rounded bg-papel-areia" />
                  <div className="h-4 w-2/5 rounded bg-papel-areia" />
                  <div className="grid gap-6 pt-8 lg:grid-cols-2">
                    <div className="space-y-4 rounded-[5px] border border-linha bg-papel-alta p-6">
                      <div className="h-5 w-36 rounded bg-papel-areia" />
                      <div className="h-24 rounded bg-papel-areia" />
                    </div>
                    <div className="space-y-4 rounded-[5px] border border-linha bg-papel-alta p-6">
                      <div className="h-5 w-44 rounded bg-papel-areia" />
                      <div className="h-24 rounded bg-papel-areia" />
                    </div>
                  </div>
                </div>
              </div>
            ) : error ? (
              <div className="overflow-hidden rounded-[5px] border border-red-200 bg-red-50 px-8 py-12 shadow-[0_4px_10px_rgba(41,69,50,0.05)]">
                <p className="font-mono text-[9px] uppercase tracking-[2.25px] text-red-700">Análise indisponível</p>
                <h1 className="mt-4 font-display text-3xl font-normal tracking-tight text-red-700">Ainda não abrimos esta análise</h1>
                <p className="mt-4 max-w-2xl text-sm leading-7 text-red-700">{error}</p>
                {notReadyDetail && (
                  <div className="mt-5 rounded-[5px] border border-red-200 bg-white p-4 text-sm text-red-700">
                    <p>Estado: {notReadyDetail.status || 'PENDENTE'}</p>
                    {notReadyDetail.status_detail && <p className="mt-2">Detalhe: {notReadyDetail.status_detail}</p>}
                    {notReadyDetail.task_id && <p className="mt-2 font-mono text-xs text-tinta-muda">Tarefa: {notReadyDetail.task_id}</p>}
                  </div>
                )}
                <div className="mt-8 flex flex-col gap-3 sm:flex-row">
                  <button
                    type="button"
                    onClick={() => router.reload()}
                    className="inline-flex items-center justify-center rounded-[5px] border border-red-200 bg-white px-5 py-3 text-sm font-medium text-red-700 transition-colors hover:bg-red-100"
                  >
                    Tentar de novo
                  </button>
                  <Link
                    href="/dashboard"
                    className="inline-flex items-center justify-center rounded-[5px] bg-tinta-profunda px-5 py-3 text-sm font-medium uppercase tracking-[0.24em] text-white transition-colors hover:bg-tinta"
                  >
                    Voltar ao painel
                  </Link>
                  {notReadyDetail?.task_id && (
                    <Link
                      href="/upload"
                      className="inline-flex items-center justify-center rounded-[5px] border border-linha bg-white px-5 py-3 text-sm font-medium text-tinta-suave transition-colors hover:border-latiim hover:text-tinta"
                    >
                      Ver processamento
                    </Link>
                  )}
                </div>
              </div>
            ) : !analysis ? (
              <div className="overflow-hidden rounded-[5px] border border-linha bg-white px-8 py-12 shadow-[0_4px_10px_rgba(41,69,50,0.05)]">
                <p className="font-mono text-[9px] uppercase tracking-[2.25px] text-latiim-texto">Sem registro</p>
                <h1 className="mt-4 font-display text-3xl font-normal tracking-tight text-tinta">Análise não encontrada</h1>
                <p className="mt-4 max-w-2xl text-sm leading-7 text-tinta-suave">
                  O painel pode ainda estar aguardando o sistema. Volte à fila e atualize a lista de processos.
                </p>
                <Link
                  href="/dashboard"
                  className="mt-8 inline-flex items-center justify-center rounded-[5px] bg-tinta-profunda px-5 py-3 text-sm font-medium uppercase tracking-[0.24em] text-white transition-colors hover:bg-tinta"
                >
                  Voltar ao painel
                </Link>
              </div>
            ) : (
              <div className="space-y-8">
                <section className="overflow-hidden rounded-[5px] border border-linha bg-white shadow-[0_4px_10px_rgba(41,69,50,0.05)]">
                  <div className="border-b border-linha bg-papel-alta px-8 py-10 sm:px-10">
                    <div className="flex flex-col gap-6 xl:flex-row xl:items-end xl:justify-between">
                      <div className="max-w-3xl">
                        <p className="font-mono text-[9px] uppercase tracking-[2.25px] text-latiim-texto">Resultado da análise</p>
                        <h1 className="mt-4 font-display text-3xl font-normal tracking-tight text-tinta sm:text-4xl">{analysis.title}</h1>
                        <p className="mt-3 text-sm leading-7 text-tinta-suave">
                          Peça de origem: <span className="text-tinta">{analysis.documentName}</span>
                        </p>
                      </div>

                      <div className="flex flex-col gap-3 sm:flex-row">
                        <Link
                          href="/dashboard"
                          className="inline-flex items-center justify-center rounded-[5px] border border-linha bg-white px-5 py-3 text-sm font-medium text-tinta-suave transition-colors hover:border-latiim hover:text-tinta"
                        >
                          Voltar à fila
                        </Link>
                        <button
                          type="button"
                          onClick={handleDownloadTemplate}
                          disabled={isDownloading}
                          className={`inline-flex items-center justify-center rounded-[5px] px-6 py-3 text-sm font-medium uppercase tracking-[0.2em] transition-colors ${
                            isDownloading
                              ? 'cursor-not-allowed bg-papel-areia text-tinta-muda'
                              : 'bg-tinta-profunda text-white hover:bg-tinta'
                          }`}
                        >
                          {isDownloading ? 'Gerando DOCX...' : 'Baixar defesa DOCX'}
                        </button>
                        <button
                          type="button"
                          onClick={handleDownloadSummary}
                          disabled={isDownloadingSummary}
                          className="inline-flex items-center justify-center rounded-[5px] border border-linha bg-white px-5 py-3 text-sm font-medium text-tinta-suave transition-colors hover:border-latiim hover:text-tinta disabled:cursor-not-allowed disabled:text-tinta-muda"
                        >
                          {isDownloadingSummary ? 'Preparando...' : 'Resumo (.md)'}
                        </button>
                      </div>
                    </div>
                  </div>

                  <div className="border-b border-linha px-8 py-6 sm:px-10">
                    <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
                      <div className="max-w-2xl">
                        <h2 className="font-mono text-[9px] uppercase tracking-[2.25px] text-tinta-muda">Modelo da peça</h2>
                        <p className="mt-2 text-sm leading-7 text-tinta-suave">
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
                          className="rounded-[5px] border border-linha bg-white px-4 py-2.5 text-sm text-tinta outline-none transition-colors hover:border-latiim focus:border-latiim"
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
                        <label className="inline-flex cursor-pointer items-center justify-center rounded-[5px] border border-linha bg-white px-5 py-2.5 text-sm font-medium text-tinta-suave transition-colors hover:border-latiim hover:text-tinta">
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
                      <p className="mt-3 rounded-[5px] border border-amber-800/25 bg-amber-50 px-3 py-2 text-sm leading-7 text-amber-800">{templateNotice || templatesHint}</p>
                    )}
                  </div>

                  {versions.length > 0 && (
                    <div className="border-b border-linha px-8 py-6 sm:px-10">
                      <h2 className="font-mono text-[9px] uppercase tracking-[2.25px] text-tinta-muda">
                        Versões anteriores ({versions.length})
                      </h2>
                      <ul className="mt-4 flex flex-wrap gap-3">
                        {versions.map((version) => (
                          <li key={version.version}>
                            <button
                              type="button"
                              onClick={() => handleDownloadVersion(version)}
                              className="inline-flex items-center gap-2 rounded-[5px] border border-linha bg-white px-4 py-2 text-sm text-tinta transition-colors hover:border-latiim hover:bg-papel-alta"
                            >
                              v{version.version}
                              {version.created_at && (
                                <span className="text-xs text-tinta-muda">
                                  {new Date(version.created_at).toLocaleString('pt-BR')}
                                </span>
                              )}
                            </button>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  <div className="grid gap-8 bg-papel px-8 py-8 sm:px-10 lg:grid-cols-[minmax(0,0.95fr)_minmax(0,1.05fr)]">
                    <div className="space-y-6">
                      <Panel title="Resumo executivo" accent="ouro">
                        <p className="text-sm leading-7 text-tinta">
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
                        <div className="rounded-[5px] border border-latiim/50 bg-papel-alta p-5">
                          <p className="whitespace-pre-wrap text-sm leading-8 text-tinta">
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
    ouro: 'text-latiim-texto',
    emerald: 'text-green-800',
    amber: 'text-amber-800',
    zinc: 'text-tinta-muda',
  }[accent];

  return (
    <section className="rounded-[5px] border border-linha bg-white p-6 shadow-[0_4px_10px_rgba(41,69,50,0.05)]">
      <div className="mb-5 flex items-center justify-between border-b border-linha pb-4">
        <h2 className={`font-mono text-[9px] font-medium uppercase tracking-[2.25px] ${accentClass}`}>{title}</h2>
      </div>
      {children}
    </section>
  );
}

function BulletList({ items, emptyState }: { items: string[]; emptyState: string }) {
  if (items.length === 0) {
    return <p className="text-sm leading-7 text-tinta-muda">{emptyState}</p>;
  }

  return (
    <ul className="space-y-3">
      {items.map((item, index) => (
        <li key={`${item}-${index}`} className="flex items-start gap-3 text-sm leading-7 text-tinta">
          <span className="mt-2 inline-flex h-2.5 w-2.5 flex-shrink-0 rounded-full bg-tinta-profunda" />
          <span>{item}</span>
        </li>
      ))}
    </ul>
  );
}

function NumberedList({ items, emptyState }: { items: string[]; emptyState: string }) {
  if (items.length === 0) {
    return <p className="text-sm leading-7 text-tinta-muda">{emptyState}</p>;
  }

  return (
    <ol className="space-y-4">
      {items.map((item, index) => (
        <li key={`${item}-${index}`} className="flex items-start gap-4">
          <span className="inline-flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-full border border-tinta-profunda/25 bg-tinta-profunda/10 text-xs font-medium text-tinta-profunda">
            {index + 1}
          </span>
          <span className="text-sm leading-7 text-tinta">{item}</span>
        </li>
      ))}
    </ol>
  );
}

function MetaItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-[5px] border border-linha bg-papel-alta p-4">
      <dt className="font-mono text-[9px] uppercase tracking-[2.25px] text-tinta-muda">{label}</dt>
      <dd className="mt-2 break-all text-sm leading-7 text-tinta">{value}</dd>
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
