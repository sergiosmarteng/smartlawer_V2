import Head from 'next/head';
import { useCallback, useEffect, useState } from 'react';
import AuthGuard from '../components/auth/AuthGuard';
import Layout from '../components/layout';
import api, { getApiErrorMessage } from '../lib/axios';
import type { AuditEventItem } from '../types/workflow';

/**
 * Audit-trail viewer (C4/BL-018): the caller's own security/workflow
 * events, newest first, filterable by event type.
 */
const KNOWN_EVENT_TYPES = [
  'auth.register',
  'auth.login',
  'document.upload',
  'document.completed',
  'document.failed',
  'docx.generated',
  'template.upload',
  'prompt.created',
  'prompt.default',
  'prompt.deleted',
  'chat.query',
];

export default function AuditPage() {
  const [events, setEvents] = useState<AuditEventItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [eventType, setEventType] = useState('');
  const [error, setError] = useState('');

  const fetchEvents = useCallback(async () => {
    setIsLoading(true);
    setError('');

    try {
      const query = eventType ? `?event_type=${encodeURIComponent(eventType)}` : '';
      const response = await api.get<AuditEventItem[]>(`/audit${query}`);
      setEvents(Array.isArray(response.data) ? response.data : []);
    } catch (fetchError) {
      setEvents([]);
      setError(getApiErrorMessage(fetchError, 'Não foi possível carregar a auditoria.'));
    } finally {
      setIsLoading(false);
    }
  }, [eventType]);

  useEffect(() => {
    fetchEvents();
  }, [fetchEvents]);

  return (
    <AuthGuard>
      <Layout>
        <Head>
          <title>Auditoria - SmartLawer</title>
        </Head>

        <div className="min-h-[calc(100vh-4rem)] px-4 py-10 text-slate-300 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-6xl">
            <section className="overflow-hidden rounded-[2rem] border border-zinc-800 bg-tribunal-900/70 px-8 py-10 shadow-2xl shadow-black/20 sm:px-10">
              <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
                <div>
                  <p className="font-mono text-xs uppercase tracking-[0.32em] text-ouro-400">Governança</p>
                  <h1 className="mt-4 font-display text-3xl font-black tracking-tight text-slate-50 sm:text-4xl">
                    Trilha de auditoria
                  </h1>
                  <p className="mt-3 max-w-2xl text-sm leading-7 text-zinc-400">
                    Eventos de segurança e de fluxo da sua conta, do mais novo ao mais antigo. Conteúdo
                    de documentos e perguntas nunca ficam gravados aqui — só identificadores, estados e tempos.
                  </p>
                </div>
                <select
                  value={eventType}
                  onChange={(event) => setEventType(event.target.value)}
                  className="rounded-full border border-zinc-700 bg-tribunal-950 px-4 py-2.5 text-sm text-slate-200 outline-none transition-colors hover:border-zinc-500 focus:border-ouro-500"
                  aria-label="Filtrar por tipo de evento"
                >
                  <option value="">Todos os tipos</option>
                  {KNOWN_EVENT_TYPES.map((type) => (
                    <option key={type} value={type}>
                      {type}
                    </option>
                  ))}
                </select>
              </div>

              {error && (
                <p className="mt-4 rounded-2xl border border-rose-900/80 bg-rose-950/50 px-5 py-3 text-sm text-rose-200">
                  {error}
                </p>
              )}

              <div className="mt-6 overflow-hidden rounded-[1.5rem] border border-zinc-800">
                {isLoading ? (
                  <p className="px-5 py-8 text-sm text-zinc-500">Carregando…</p>
                ) : events.length === 0 ? (
                  <p className="px-5 py-8 text-sm leading-7 text-zinc-500">
                    Nada por aqui ainda. Envie um documento ou gere uma defesa para preencher esta trilha.
                  </p>
                ) : (
                  <ul className="divide-y divide-zinc-800">
                    {events.map((item) => (
                      <li key={item.id} className="px-5 py-4">
                        <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
                          <p className="text-sm font-medium text-slate-100">{item.event_type}</p>
                          {item.created_at && (
                            <p className="text-xs text-zinc-500">
                              {new Date(item.created_at).toLocaleString()}
                            </p>
                          )}
                        </div>
                        {(item.entity_type || item.entity_id) && (
                          <p className="mt-1 break-all text-xs text-zinc-500">
                            {[item.entity_type, item.entity_id].filter(Boolean).join(' · ')}
                          </p>
                        )}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </section>
          </div>
        </div>
      </Layout>
    </AuthGuard>
  );
}
