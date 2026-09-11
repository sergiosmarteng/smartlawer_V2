import Head from 'next/head';
import { useRouter } from 'next/router';
import { useState } from 'react';
import AuthGuard from '../components/auth/AuthGuard';
import Layout from '../components/layout';
import { useTaskPolling } from '../hooks/useTaskPolling';
import api, { getApiErrorMessage, normalizeApiPath } from '../lib/axios';
import {
  isActiveStatus,
  isFailureStatus,
  isSuccessStatus,
  normalizeWorkflowStatus,
  type BatchUploadResponse,
  type TaskStatusResponse,
  type UploadResponse,
} from '../types/workflow';

const MAX_BATCH_FILES = 10;

export default function UploadPage() {
  const router = useRouter();
  const { schedulePoll, cancelPoll } = useTaskPolling();

  const [files, setFiles] = useState<File[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState('');
  const [statusMessage, setStatusMessage] = useState('Selecione PDFs para iniciar novas análises.');

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const picked = Array.from(event.target.files ?? []);
    setError('');

    if (picked.length === 0) {
      setFiles([]);
      setStatusMessage('Selecione PDFs para iniciar novas análises.');
      return;
    }

    const pdfs = picked.filter((item) => item.type === 'application/pdf');
    const rejected = picked.length - pdfs.length;
    if (pdfs.length === 0) {
      setFiles([]);
      setStatusMessage('Selecione PDFs para iniciar novas análises.');
      setError('O sistema aceita apenas PDFs por enquanto.');
      event.target.value = '';
      return;
    }

    if (pdfs.length > MAX_BATCH_FILES) {
      setFiles([]);
      setStatusMessage('Selecione PDFs para iniciar novas análises.');
      setError(`No máximo ${MAX_BATCH_FILES} arquivos por lote.`);
      event.target.value = '';
      return;
    }

    setFiles(pdfs);
    setStatusMessage(
      pdfs.length === 1
        ? `Pronto para enviar ${pdfs[0].name}.`
        : `Pronto para enviar ${pdfs.length} PDFs em um lote.` +
          (rejected > 0 ? ` (${rejected} arquivo(s) fora do padrão ignorado(s).)` : ''),
    );
  };

  const handleUpload = async () => {
    if (files.length === 0) {
      setError('Selecione ao menos um PDF antes de iniciar.');
      return;
    }

    setIsProcessing(true);
    setError('');
    setProgress(1);
    setStatusMessage(
      files.length === 1
        ? 'Enviando documento para análise...'
        : `Enviando ${files.length} documentos para análise...`,
    );

    try {
      const formData = new FormData();
      let endpoint = '/documents/upload';
      if (files.length > 1) {
        files.forEach((item) => formData.append('files', item));
        endpoint = '/documents/batch-upload';
      } else {
        formData.append('file', files[0]);
      }

      const uploadResponse = await api.post<UploadResponse | BatchUploadResponse>(
        endpoint,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          // Real byte-level upload progress (1-20% band); the backend
          // pipeline progress takes over once the POST completes.
          onUploadProgress: (progressEvent) => {
            if (progressEvent.total) {
              const percent = Math.round((progressEvent.loaded / progressEvent.total) * 20);
              setProgress(Math.max(1, Math.min(percent, 20)));
            }
          },
        },
      );

      // Batch shape: follow the first accepted item through the usual
      // polling machine; report the rest as a queue summary.
      let first: UploadResponse | undefined;
      if ('items' in uploadResponse.data) {
        const batch = uploadResponse.data;
        if (batch.items.length === 0) {
          const reasons = batch.errors.map((item) => `${item.filename}: ${item.detail}`).join('; ');
          throw new Error(reasons || 'O sistema recusou todos os arquivos do lote.');
        }
        first = batch.items[0];
        const queued = batch.items.length - 1;
        const rejected = batch.errors.length;
        setStatusMessage(
          `Lote aceito (${batch.items.length} na fila` +
            (rejected > 0 ? `, ${rejected} recusado(s)` : '') +
            '). Acompanhando o primeiro documento abaixo' +
            (queued > 0 ? '; os demais estão no painel' : '') +
            '.',
        );
      } else {
        first = uploadResponse.data;
      }

      const taskId = first?.id;
      if (!taskId) {
        throw new Error('O sistema não devolveu o identificador para acompanhar a tarefa.');
      }

      // BL-014: task_id == document id by design; poll the canonical URL
      // from the backend, falling back to the identity convention.
      const taskStatusUrl = first?.taskStatusUrl;
      const pollPath =
        (taskStatusUrl && normalizeApiPath(taskStatusUrl)) || `/tasks/${taskId}`;

      setProgress(24);
      setStatusMessage('Envio concluído. Extraindo e analisando...');

      const pollTask = async () => {
        try {
          const taskResponse = await api.get<TaskStatusResponse>(pollPath);
          const {
            status = 'PENDING',
            progress: nextProgress,
            analysis_id,
            status_detail,
            error_message,
          } = taskResponse.data;
          const normalizedStatus = normalizeWorkflowStatus(status);

          if (status_detail) {
            setStatusMessage(status_detail);
          }

          if (typeof nextProgress === 'number') {
            setProgress(Math.max(15, Math.min(nextProgress, 100)));
          } else if (isActiveStatus(normalizedStatus)) {
            setProgress((current) => Math.min(current + 8, 92));
          }

          if (isSuccessStatus(normalizedStatus)) {
            if (analysis_id) {
              setProgress(100);
              setStatusMessage('Análise pronta. Abrindo o resultado...');
              schedulePoll(() => {
                router.push(`/analysis/${analysis_id}`);
              }, 600);
              return;
            }

            setStatusMessage('Análise concluída no sistema. Finalizando o registro...');
            setProgress(95);
            schedulePoll(pollTask, 1500);
            return;
          }

          if (isFailureStatus(normalizedStatus)) {
            setError(error_message || 'O sistema marcou esta análise como falha.');
            setStatusMessage('O processamento parou antes de concluir a análise.');
            setIsProcessing(false);
            return;
          }

          schedulePoll(pollTask);
        } catch (pollError) {
          setError(getApiErrorMessage(pollError, 'Perdemos a conexão com o andamento do processamento.'));
          setStatusMessage('Andamento temporariamente indisponível.');
          setIsProcessing(false);
        }
      };

      schedulePoll(pollTask, 1200);
    } catch (uploadError) {
      setError(getApiErrorMessage(uploadError, 'Não foi possível enviar o documento.'));
      setStatusMessage('O envio não pôde ser iniciado.');
      setIsProcessing(false);
    }
  };

  const resetFlow = () => {
    cancelPoll();

    setFiles([]);
    setIsProcessing(false);
    setProgress(0);
    setError('');
    setStatusMessage('Selecione PDFs para iniciar novas análises.');
  };

  return (
    <AuthGuard>
      <Layout>
        <Head>
          <title>Upload Legal Document - SmartLawer</title>
        </Head>

        <div className="min-h-[calc(100vh-4rem)] bg-zinc-950 px-4 py-10 text-slate-300 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-5xl">
            <div className="overflow-hidden rounded-[2rem] border border-zinc-800 bg-zinc-900 shadow-2xl shadow-black/20">
              <div className="border-b border-zinc-800 bg-[radial-gradient(circle_at_top_left,_rgba(56,189,248,0.14),_transparent_28%),radial-gradient(circle_at_top_right,_rgba(16,185,129,0.12),_transparent_22%)] px-8 py-10 sm:px-10">
                <p className="font-mono text-xs uppercase tracking-[0.32em] text-ouro-400">Envio de peças</p>
                <div className="mt-4 flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
                  <div className="max-w-2xl">
                    <h1 className="font-display text-3xl font-black tracking-tight text-slate-50 sm:text-4xl">Iniciar análise de documento</h1>
                    <p className="mt-3 text-sm leading-7 text-zinc-400">
                      O sistema aceita PDFs, devolve o identificador na hora e usa esse identificador até a análise ficar pronta.
                    </p>
                  </div>
                  <div className="rounded-2xl border border-zinc-800 bg-tribunal-950/70 px-5 py-4">
                    <p className="font-mono text-xs uppercase tracking-[0.3em] text-zinc-500">Entrada aceita</p>
                    <p className="mt-2 text-lg font-medium text-slate-100">Somente PDF</p>
                    <p className="mt-1 text-sm text-zinc-500">Até {MAX_BATCH_FILES} PDFs por lote</p>
                  </div>
                </div>
              </div>

              <div className="grid gap-8 px-8 py-8 sm:px-10 lg:grid-cols-[minmax(0,1.2fr)_minmax(20rem,0.8fr)]">
                <section className="space-y-6">
                  {error && (
                    <div className="rounded-2xl border border-rose-900/80 bg-rose-950/50 px-5 py-4 text-sm text-rose-200">
                      <p className="font-medium uppercase tracking-[0.24em] text-rose-300">Algo travou</p>
                      <p className="mt-2 leading-6">{error}</p>
                    </div>
                  )}

                  <label className="group relative block cursor-pointer overflow-hidden rounded-[1.75rem] border border-dashed border-zinc-700 bg-zinc-950 p-10 transition-colors hover:border-zinc-500">
                    <input
                      type="file"
                      className="absolute inset-0 cursor-pointer opacity-0"
                      onChange={handleFileChange}
                      accept=".pdf,application/pdf"
                      multiple
                      disabled={isProcessing}
                    />
                    <div className="flex flex-col items-center justify-center text-center">
                      <div className="inline-flex h-16 w-16 items-center justify-center rounded-2xl border border-ouro-700/40 bg-ouro-500/10 text-ouro-300">
                        <svg className="h-8 w-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                        </svg>
                      </div>
                      <h2 className="mt-6 font-display text-xl font-bold text-slate-100">Solte a petição aqui ou busque no disco</h2>
                      <p className="mt-3 max-w-xl text-sm leading-7 text-zinc-500">
                        Aceito o envio, o sistema acompanha o mesmo identificador até a análise ficar pronta para revisão.
                      </p>
                    </div>
                  </label>

                  <div className="rounded-[1.75rem] border border-zinc-800 bg-zinc-950/70 p-6">
                    <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                      <div>
                        <p className="font-mono text-xs uppercase tracking-[0.3em] text-zinc-500">Arquivos escolhidos</p>
                        <p className="mt-2 text-lg font-medium text-slate-100">
                          {files.length === 0
                            ? 'Nenhum documento ainda'
                            : files.length === 1
                              ? files[0].name
                              : `${files.length} PDFs escolhidos`}
                        </p>
                        <p className="mt-1 text-sm text-zinc-500">
                          {files.length === 0
                            ? 'Escolha PDFs para liberar o processamento.'
                            : `${(files.reduce((total, item) => total + item.size, 0) / (1024 * 1024)).toFixed(2)} MB no total`}
                        </p>
                        {files.length > 1 && (
                          <ul className="mt-3 max-h-28 space-y-1 overflow-y-auto text-sm text-zinc-400">
                            {files.map((item) => (
                              <li key={`${item.name}-${item.size}`} className="truncate">
                                {item.name}
                              </li>
                            ))}
                          </ul>
                        )}
                      </div>

                      {!isProcessing && files.length > 0 && (
                        <button
                          type="button"
                          onClick={resetFlow}
                            className="inline-flex items-center justify-center rounded-full border border-zinc-800 px-4 py-2 text-sm font-medium text-zinc-300 transition-colors hover:border-zinc-700 hover:bg-tribunal-900 hover:text-slate-100"
                          >
                            Limpar
                          </button>
                      )}
                    </div>
                  </div>
                </section>

                <aside className="space-y-5 rounded-[1.75rem] border border-zinc-800 bg-zinc-950/60 p-6">
                  <div>
                    <p className="font-mono text-xs uppercase tracking-[0.3em] text-zinc-500">Estado do processamento</p>
                    <h2 className="mt-2 font-display text-2xl font-bold text-slate-100">
                      {isProcessing ? 'Processando documento' : 'Pronto para começar'}
                    </h2>
                    <p className="mt-3 text-sm leading-7 text-zinc-400">{statusMessage}</p>
                  </div>

                  <div className="rounded-2xl border border-zinc-800 bg-zinc-900/80 p-5">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-zinc-400">Andamento</span>
                      <span className="font-mono font-medium tabular-nums text-ouro-300">{progress}%</span>
                    </div>
                    <div className="mt-4 h-2 overflow-hidden rounded-full bg-zinc-800">
                      <div
                        className="h-full rounded-full bg-gradient-to-r from-ouro-600 via-ouro-400 to-ouro-200 transition-all duration-500"
                        style={{ width: `${progress}%` }}
                      />
                    </div>
                  </div>

                  <div className="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-5">
                    <p className="font-mono text-xs uppercase tracking-[0.3em] text-zinc-500">Etapas do sistema</p>
                    <ul className="mt-4 space-y-3 text-sm text-zinc-400">
                      <li className="flex items-start gap-3">
                        <StatusDot active={progress >= 24} />
                        O envio guarda o arquivo e devolve o identificador na hora.
                      </li>
                      <li className="flex items-start gap-3">
                        <StatusDot active={progress >= 24} />
                        O acompanhamento mostra estado, andamento e a análise quando pronta.
                      </li>
                      <li className="flex items-start gap-3">
                        <StatusDot active={progress >= 95} />
                        O sistema só abre a análise depois que ela existe de verdade.
                      </li>
                    </ul>
                  </div>

                  <div className="flex flex-col gap-3">
                    <button
                      type="button"
                      onClick={handleUpload}
                      disabled={files.length === 0 || isProcessing}
                      className={`inline-flex items-center justify-center rounded-full px-6 py-3 text-sm font-bold uppercase tracking-[0.2em] transition-all ${
                        files.length === 0 || isProcessing
                          ? 'cursor-not-allowed bg-zinc-800 text-zinc-500'
                          : 'bg-ouro-500 text-tribunal-950 shadow-[0_0_25px_rgba(201,162,39,0.2)] hover:-translate-y-0.5 hover:bg-ouro-400'
                      }`}
                    >
                      {isProcessing ? 'Processando...' : 'Iniciar processamento'}
                    </button>

                    {(error || isProcessing) && (
                      <button
                        type="button"
                        onClick={resetFlow}
                        className="inline-flex items-center justify-center rounded-full border border-zinc-800 px-6 py-3 text-sm font-medium text-zinc-300 transition-colors hover:border-zinc-700 hover:bg-tribunal-900 hover:text-slate-100"
                      >
                        Recomeçar
                      </button>
                    )}
                  </div>
                </aside>
              </div>
            </div>
          </div>
        </div>
      </Layout>
    </AuthGuard>
  );
}

function StatusDot({ active }: { active: boolean }) {
  return (
    <span
      className={`mt-1 inline-flex h-2.5 w-2.5 flex-shrink-0 rounded-full ${
        active ? 'bg-emerald-400 shadow-[0_0_14px_rgba(52,211,153,0.65)]' : 'bg-zinc-700'
      }`}
    />
  );
}
