import Head from 'next/head';
import Link from 'next/link';
import { useEffect, useState } from 'react';
import { useAuth } from '../components/auth/AuthProvider';
import AuthGuard from '../components/auth/AuthGuard';
import Layout from '../components/layout';
import api, { getApiErrorMessage } from '../lib/axios';
import {
  isActiveStatus,
  isFailureStatus,
  isSuccessStatus,
  type ProcessItem,
} from '../types/workflow';

export default function DashboardPage() {
  const { user } = useAuth();
  const [processes, setProcesses] = useState<ProcessItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState('');

  const totalProcesses = processes.length;
  const processingCount = processes.filter((process) => isActiveStatus(process.status)).length;
  const readyCount = processes.filter((process) => isSuccessStatus(process.status) && process.analysis_id).length;
  const failedCount = processes.filter((process) => isFailureStatus(process.status)).length;
  const userLabel = user?.username || user?.email || 'Advogado';

  const fetchProcesses = async (backgroundRefresh = false) => {
    if (backgroundRefresh) {
      setIsRefreshing(true);
    } else {
      setIsLoading(true);
    }

    setError('');

    try {
      const response = await api.get<ProcessItem[]>('/processes');
      setProcesses(Array.isArray(response.data) ? response.data : []);
    } catch (fetchError) {
      setError(getApiErrorMessage(fetchError, 'Não foi possível carregar os processos.'));
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    fetchProcesses();
  }, []);

  return (
    <AuthGuard>
      <Layout>
        <Head>
          <title>Painel - SmartLawer</title>
        </Head>

        <div className="min-h-[calc(100vh-4rem)] px-4 py-10 text-slate-300 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-7xl">
            <div className="flex flex-col gap-6 border-b border-ouro-700/20 pb-8 md:flex-row md:items-end md:justify-between">
              <div className="max-w-3xl">
                <p className="font-mono text-xs uppercase tracking-[0.32em] text-ouro-400">Central de operações</p>
                <h1 className="mt-4 font-display text-4xl font-black tracking-tight text-slate-50 sm:text-5xl">
                  Bem-vindo(a) de volta, <span className="text-ouro-300">{userLabel}</span>
                </h1>
                <p className="mt-3 text-sm leading-7 text-zinc-400">
                  Seus documentos processados em tempo real. Sem análise pronta, o item segue na fila até o sistema concluir.
                </p>
              </div>

              <div className="flex flex-col gap-3 sm:flex-row">
                <button
                  type="button"
                  onClick={() => fetchProcesses(true)}
                  className="inline-flex items-center justify-center rounded-full border border-zinc-700 px-5 py-3 text-sm font-medium text-zinc-300 transition-colors hover:border-ouro-600/60 hover:bg-tribunal-900 hover:text-ouro-200"
                >
                  {isRefreshing ? 'Atualizando...' : 'Atualizar'}
                </button>
                <Link
                  href="/upload"
                  className="inline-flex items-center justify-center rounded-full bg-ouro-500 px-6 py-3 text-sm font-bold uppercase tracking-[0.2em] text-tribunal-950 shadow-[0_0_24px_rgba(201,162,39,0.2)] transition-all hover:-translate-y-0.5 hover:bg-ouro-400"
                >
                  Nova análise
                </Link>
              </div>
            </div>

            <div className="mt-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
              <StatCard title="Documentos" value={String(totalProcesses)} tone="ouro" />
              <StatCard title="Em andamento" value={String(processingCount)} tone="amber" />
              <StatCard title="Prontos p/ revisar" value={String(readyCount)} tone="emerald" />
              <StatCard title="Com falha" value={String(failedCount)} tone="rose" />
            </div>

            <section className="mt-10 rounded-[2rem] border border-zinc-800 bg-tribunal-900/70 shadow-2xl shadow-black/20">
              <div className="flex flex-col gap-4 border-b border-zinc-800 px-6 py-6 sm:flex-row sm:items-end sm:justify-between sm:px-8">
                <div>
                  <p className="font-mono text-xs uppercase tracking-[0.3em] text-zinc-500">Processos recentes</p>
                  <h2 className="mt-2 font-display text-2xl font-bold text-slate-50">Fila atual do sistema</h2>
                </div>
                <p className="max-w-xl text-sm leading-6 text-zinc-500">
                  Itens concluídos abrem a análise direto. Itens pendentes ficam visíveis aqui com o detalhe do andamento.
                </p>
              </div>

              {isLoading ? (
                <div className="grid gap-4 px-6 py-8 sm:px-8">
                  {Array.from({ length: 3 }).map((_, index) => (
                    <div key={index} className="animate-pulse rounded-[1.5rem] border border-zinc-800 bg-zinc-950/70 p-6">
                      <div className="h-4 w-40 rounded bg-zinc-800" />
                      <div className="mt-4 h-3 w-56 rounded bg-zinc-800" />
                      <div className="mt-6 h-10 rounded-xl bg-zinc-900" />
                    </div>
                  ))}
                </div>
              ) : error ? (
                <div className="px-6 py-12 text-center sm:px-8">
                  <div className="mx-auto max-w-xl rounded-[1.75rem] border border-rose-900/80 bg-rose-950/50 px-6 py-6">
                    <p className="text-xs uppercase tracking-[0.3em] text-rose-300">Erro no painel</p>
                    <p className="mt-3 text-sm leading-7 text-rose-100">{error}</p>
                    <button
                      type="button"
                      onClick={() => fetchProcesses()}
                      className="mt-5 inline-flex items-center justify-center rounded-full border border-rose-800 px-5 py-2.5 text-sm font-medium text-rose-100 transition-colors hover:bg-rose-900/40"
                    >
                      Tentar de novo
                    </button>
                  </div>
                </div>
              ) : processes.length === 0 ? (
                <div className="px-6 py-16 text-center sm:px-8">
                  <div className="mx-auto max-w-2xl">
                    <p className="font-mono text-xs uppercase tracking-[0.3em] text-zinc-500">Nenhum processo ainda</p>
                    <h3 className="mt-3 font-display text-3xl font-bold text-slate-50">Sua fila está vazia</h3>
                    <p className="mt-4 text-sm leading-7 text-zinc-400">
                      Envie um PDF e o painel passa a mostrar andamento, detalhes e links de análise assim que existirem.
                    </p>
                    <Link
                      href="/upload"
                      className="mt-8 inline-flex items-center justify-center rounded-full bg-ouro-500 px-6 py-3 text-sm font-bold uppercase tracking-[0.2em] text-tribunal-950 transition-all hover:-translate-y-0.5 hover:bg-ouro-400"
                    >
                      Enviar primeiro documento
                    </Link>
                  </div>
                </div>
              ) : (
                <div className="grid gap-4 px-6 py-6 sm:px-8">
                  {processes.map((process) => {
                    const destination = process.analysis_id ? `/analysis/${process.analysis_id}` : null;
                    const createdAt = formatDate(process.created_at);
                    const detail = process.status_detail || fallbackStatusDetail(process.status);
                    const wrapperClassName = 'block rounded-[1.5rem] border border-zinc-800 bg-zinc-950/70 p-6 transition-all';

                    const content = (
                      <>
                        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                          <div className="min-w-0">
                            <div className="flex flex-wrap items-center gap-3">
                              <p className="text-lg font-medium text-slate-100">{process.title}</p>
                              <StatusBadge status={process.status} />
                            </div>
                            <p className="mt-3 max-w-3xl text-sm leading-7 text-zinc-400">{detail}</p>
                          </div>

                          <div className="lg:text-right">
                            <p className="font-mono text-xs uppercase tracking-[0.28em] text-zinc-500">Criado em</p>
                            <p className="mt-2 text-sm text-slate-300">{createdAt}</p>
                          </div>
                        </div>

                        <div className="mt-6 flex flex-col gap-3 border-t border-zinc-800 pt-4 text-sm text-zinc-500 sm:flex-row sm:items-center sm:justify-between">
                          <p className="truncate font-mono text-xs">Documento: {process.id}</p>
                          {destination ? (
                            <span className="inline-flex items-center font-medium text-ouro-300">
                              Abrir análise
                              <svg className="ml-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                              </svg>
                            </span>
                          ) : (
                            <span className="inline-flex items-center text-zinc-500">Aguardando o resultado</span>
                          )}
                        </div>
                      </>
                    );

                    if (destination) {
                      return (
                        <Link
                          key={process.id}
                          href={destination}
                          className={`${wrapperClassName} hover:-translate-y-0.5 hover:border-zinc-700 hover:bg-zinc-950`}
                        >
                          {content}
                        </Link>
                      );
                    }

                    return (
                      <div key={process.id} className={wrapperClassName}>
                        {content}
                      </div>
                    );
                  })}
                </div>
              )}
            </section>
          </div>
        </div>
      </Layout>
    </AuthGuard>
  );
}

function StatCard({
  title,
  value,
  tone,
}: {
  title: string;
  value: string;
  tone: 'ouro' | 'amber' | 'emerald' | 'rose';
}) {
  const toneStyles = {
    ouro: 'from-ouro-500/15 to-ouro-700/5 text-ouro-300',
    amber: 'from-amber-500/15 to-orange-400/5 text-amber-300',
    emerald: 'from-emerald-500/15 to-teal-400/5 text-emerald-300',
    rose: 'from-rose-500/15 to-pink-400/5 text-rose-300',
  }[tone];

  return (
    <div className={`rounded-[1.75rem] border border-zinc-800 bg-gradient-to-br ${toneStyles} p-6 shadow-2xl shadow-black/20`}>
      <p className="font-mono text-xs uppercase tracking-[0.3em] text-zinc-500">{title}</p>
      <p className="mt-4 font-display text-5xl font-black tabular-nums text-slate-50">{value}</p>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  if (isSuccessStatus(status)) {
    return <span className="rounded-full border border-emerald-800 bg-emerald-900/30 px-3 py-1 text-xs font-medium uppercase tracking-[0.2em] text-emerald-300">{status}</span>;
  }

  if (isActiveStatus(status)) {
    return <span className="rounded-full border border-amber-800 bg-amber-900/30 px-3 py-1 text-xs font-medium uppercase tracking-[0.2em] text-amber-300">{status}</span>;
  }

  return <span className="rounded-full border border-rose-800 bg-rose-900/30 px-3 py-1 text-xs font-medium uppercase tracking-[0.2em] text-rose-300">{status}</span>;
}

function formatDate(value?: string) {
  if (!value) {
    return 'Sem data disponível';
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat('pt-BR', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(date);
}

function fallbackStatusDetail(status: string) {
  if (isSuccessStatus(status)) {
    return 'Análise pronta para revisão e geração da peça.';
  }

  if (isActiveStatus(status)) {
    return 'O sistema segue extraindo, estruturando e gerando a análise.';
  }

  return 'Este documento precisa de atenção antes de continuar.';
}
