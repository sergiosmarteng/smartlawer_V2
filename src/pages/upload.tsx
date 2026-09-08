import Head from 'next/head';
import { useRouter } from 'next/router';
import { useEffect, useRef, useState } from 'react';
import AuthGuard from '../components/auth/AuthGuard';
import Layout from '../components/layout';
import api, { getApiErrorMessage, normalizeApiPath } from '../lib/axios';

interface UploadResponse {
  id: string;
  task_id?: string;
  taskStatusUrl?: string;
  status: string;
}

interface TaskStatusResponse {
  task_id?: string;
  document_id?: string;
  status?: string;
  progress?: number;
  analysis_id?: string | null;
  status_detail?: string | null;
  error_message?: string | null;
}

const ACTIVE_STATUSES = new Set(['PENDING', 'PROCESSING', 'STARTED', 'RETRY']);
const SUCCESS_STATUSES = new Set(['SUCCESS', 'COMPLETED', 'DONE']);
const FAILURE_STATUSES = new Set(['FAILURE', 'FAILED', 'ERROR']);

export default function UploadPage() {
  const router = useRouter();
  const pollTimeoutRef = useRef<number | null>(null);

  const [file, setFile] = useState<File | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState('');
  const [statusMessage, setStatusMessage] = useState('Select a PDF to begin a new analysis.');

  useEffect(() => {
    return () => {
      if (pollTimeoutRef.current) {
        window.clearTimeout(pollTimeoutRef.current);
      }
    };
  }, []);

  const schedulePoll = (callback: () => void, delay = 1800) => {
    if (pollTimeoutRef.current) {
      window.clearTimeout(pollTimeoutRef.current);
    }

    pollTimeoutRef.current = window.setTimeout(callback, delay);
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const nextFile = event.target.files?.[0] ?? null;
    setError('');

    if (!nextFile) {
      setFile(null);
      setStatusMessage('Select a PDF to begin a new analysis.');
      return;
    }

    if (nextFile.type !== 'application/pdf') {
      setFile(null);
      setStatusMessage('Select a PDF to begin a new analysis.');
      setError('The backend currently accepts only PDF uploads.');
      event.target.value = '';
      return;
    }

    setFile(nextFile);
    setStatusMessage(`Ready to upload ${nextFile.name}.`);
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Select a PDF before starting the workflow.');
      return;
    }

    setIsProcessing(true);
    setError('');
    setProgress(12);
    setStatusMessage('Uploading document to the backend pipeline...');

    try {
      const formData = new FormData();
      formData.append('file', file);

      const uploadResponse = await api.post<UploadResponse>('/documents/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      const taskId = uploadResponse.data?.id;
      if (!taskId) {
        throw new Error('The backend did not return a document identifier for task tracking.');
      }

      // BL-014: task_id == document id by design; poll the canonical URL
      // from the backend, falling back to the identity convention.
      const taskStatusUrl = uploadResponse.data?.taskStatusUrl;
      const pollPath =
        (taskStatusUrl && normalizeApiPath(taskStatusUrl)) || `/tasks/${taskId}`;

      setProgress(24);
      setStatusMessage('Upload completed. Waiting for extraction and analysis...');

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
          const normalizedStatus = status.toUpperCase();

          if (status_detail) {
            setStatusMessage(status_detail);
          }

          if (typeof nextProgress === 'number') {
            setProgress(Math.max(15, Math.min(nextProgress, 100)));
          } else if (ACTIVE_STATUSES.has(normalizedStatus)) {
            setProgress((current) => Math.min(current + 8, 92));
          }

          if (SUCCESS_STATUSES.has(normalizedStatus)) {
            if (analysis_id) {
              setProgress(100);
              setStatusMessage('Analysis completed. Opening the detail view...');
              schedulePoll(() => {
                router.push(`/analysis/${analysis_id}`);
              }, 600);
              return;
            }

            setStatusMessage('Analysis finished on the backend. Finalizing the result record...');
            setProgress(95);
            schedulePoll(pollTask, 1500);
            return;
          }

          if (FAILURE_STATUSES.has(normalizedStatus)) {
            setError(error_message || 'The backend marked this analysis as failed.');
            setStatusMessage('Processing stopped before the analysis could finish.');
            setIsProcessing(false);
            return;
          }

          schedulePoll(pollTask);
        } catch (pollError) {
          setError(getApiErrorMessage(pollError, 'The connection to the processing status endpoint was lost.'));
          setStatusMessage('Processing status is temporarily unavailable.');
          setIsProcessing(false);
        }
      };

      schedulePoll(pollTask, 1200);
    } catch (uploadError) {
      setError(getApiErrorMessage(uploadError, 'Failed to upload the document.'));
      setStatusMessage('The upload could not be started.');
      setIsProcessing(false);
    }
  };

  const resetFlow = () => {
    if (pollTimeoutRef.current) {
      window.clearTimeout(pollTimeoutRef.current);
    }

    setFile(null);
    setIsProcessing(false);
    setProgress(0);
    setError('');
    setStatusMessage('Select a PDF to begin a new analysis.');
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
                <p className="text-xs uppercase tracking-[0.32em] text-sky-400">Upload Workflow</p>
                <div className="mt-4 flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
                  <div className="max-w-2xl">
                    <h1 className="text-3xl font-light tracking-tight text-slate-100 sm:text-4xl">Start a document analysis</h1>
                    <p className="mt-3 text-sm leading-7 text-zinc-400">
                      The current backend contract accepts PDF files, returns the document `id` immediately, and uses that identifier on `/tasks/{'{id}'}` until an `analysis_id` becomes available.
                    </p>
                  </div>
                  <div className="rounded-2xl border border-zinc-800 bg-zinc-950/70 px-5 py-4">
                    <p className="text-xs uppercase tracking-[0.3em] text-zinc-500">Accepted input</p>
                    <p className="mt-2 text-lg font-medium text-slate-100">PDF only</p>
                    <p className="mt-1 text-sm text-zinc-500">One file per analysis</p>
                  </div>
                </div>
              </div>

              <div className="grid gap-8 px-8 py-8 sm:px-10 lg:grid-cols-[minmax(0,1.2fr)_minmax(20rem,0.8fr)]">
                <section className="space-y-6">
                  {error && (
                    <div className="rounded-2xl border border-rose-900/80 bg-rose-950/50 px-5 py-4 text-sm text-rose-200">
                      <p className="font-medium uppercase tracking-[0.24em] text-rose-300">Workflow issue</p>
                      <p className="mt-2 leading-6">{error}</p>
                    </div>
                  )}

                  <label className="group relative block cursor-pointer overflow-hidden rounded-[1.75rem] border border-dashed border-zinc-700 bg-zinc-950 p-10 transition-colors hover:border-zinc-500">
                    <input
                      type="file"
                      className="absolute inset-0 cursor-pointer opacity-0"
                      onChange={handleFileChange}
                      accept=".pdf,application/pdf"
                      disabled={isProcessing}
                    />
                    <div className="flex flex-col items-center justify-center text-center">
                      <div className="inline-flex h-16 w-16 items-center justify-center rounded-2xl border border-zinc-800 bg-zinc-900 text-sky-300">
                        <svg className="h-8 w-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                        </svg>
                      </div>
                      <h2 className="mt-6 text-xl font-medium text-slate-100">Drop a legal PDF here or browse from disk</h2>
                      <p className="mt-3 max-w-xl text-sm leading-7 text-zinc-500">
                        Once the upload is accepted, the frontend tracks the same document identifier through the processing endpoint until the analysis detail view is ready.
                      </p>
                    </div>
                  </label>

                  <div className="rounded-[1.75rem] border border-zinc-800 bg-zinc-950/70 p-6">
                    <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                      <div>
                        <p className="text-xs uppercase tracking-[0.3em] text-zinc-500">Selected file</p>
                        <p className="mt-2 text-lg font-medium text-slate-100">{file?.name || 'No document selected yet'}</p>
                        <p className="mt-1 text-sm text-zinc-500">
                          {file ? `${(file.size / (1024 * 1024)).toFixed(2)} MB` : 'Pick a PDF to unlock processing.'}
                        </p>
                      </div>

                      {!isProcessing && file && (
                        <button
                          type="button"
                          onClick={resetFlow}
                          className="inline-flex items-center justify-center rounded-full border border-zinc-800 px-4 py-2 text-sm font-medium text-zinc-300 transition-colors hover:border-zinc-700 hover:bg-zinc-900 hover:text-slate-100"
                        >
                          Clear file
                        </button>
                      )}
                    </div>
                  </div>
                </section>

                <aside className="space-y-5 rounded-[1.75rem] border border-zinc-800 bg-zinc-950/60 p-6">
                  <div>
                    <p className="text-xs uppercase tracking-[0.3em] text-zinc-500">Pipeline status</p>
                    <h2 className="mt-2 text-2xl font-light text-slate-100">
                      {isProcessing ? 'Processing in progress' : 'Ready to begin'}
                    </h2>
                    <p className="mt-3 text-sm leading-7 text-zinc-400">{statusMessage}</p>
                  </div>

                  <div className="rounded-2xl border border-zinc-800 bg-zinc-900/80 p-5">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-zinc-400">Workflow completion</span>
                      <span className="font-medium text-slate-100">{progress}%</span>
                    </div>
                    <div className="mt-4 h-2 overflow-hidden rounded-full bg-zinc-800">
                      <div
                        className="h-full rounded-full bg-gradient-to-r from-sky-500 via-cyan-300 to-emerald-400 transition-all duration-500"
                        style={{ width: `${progress}%` }}
                      />
                    </div>
                  </div>

                  <div className="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-5">
                    <p className="text-xs uppercase tracking-[0.3em] text-zinc-500">Backend checkpoints</p>
                    <ul className="mt-4 space-y-3 text-sm text-zinc-400">
                      <li className="flex items-start gap-3">
                        <StatusDot active={progress >= 12} />
                        `POST /documents/upload` stores the file and returns the document id.
                      </li>
                      <li className="flex items-start gap-3">
                        <StatusDot active={progress >= 24} />
                        `GET /tasks/{'{id}'}` exposes status, progress, and `analysis_id` when ready.
                      </li>
                      <li className="flex items-start gap-3">
                        <StatusDot active={progress >= 95} />
                        The frontend redirects to `/analysis/{'{analysis_id}'}` only after the backend exposes it.
                      </li>
                    </ul>
                  </div>

                  <div className="flex flex-col gap-3">
                    <button
                      type="button"
                      onClick={handleUpload}
                      disabled={!file || isProcessing}
                      className={`inline-flex items-center justify-center rounded-full px-6 py-3 text-sm font-medium uppercase tracking-[0.24em] transition-all ${
                        !file || isProcessing
                          ? 'cursor-not-allowed bg-zinc-800 text-zinc-500'
                          : 'bg-slate-100 text-zinc-950 shadow-[0_0_25px_rgba(255,255,255,0.08)] hover:-translate-y-0.5 hover:shadow-[0_0_35px_rgba(255,255,255,0.15)]'
                      }`}
                    >
                      {isProcessing ? 'Processing...' : 'Start processing'}
                    </button>

                    {(error || isProcessing) && (
                      <button
                        type="button"
                        onClick={resetFlow}
                        className="inline-flex items-center justify-center rounded-full border border-zinc-800 px-6 py-3 text-sm font-medium text-zinc-300 transition-colors hover:border-zinc-700 hover:bg-zinc-900 hover:text-slate-100"
                      >
                        Reset workflow
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
