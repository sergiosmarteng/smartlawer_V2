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

        <div className="min-h-[calc(100vh-4rem)] bg-papel px-4 py-10 text-tinta sm:px-6 lg:px-8">
          <div className="mx-auto max-w-6xl">
            <section className="overflow-hidden rounded-[5px] border border-linha bg-white px-8 py-10 shadow-[0_4px_10px_rgba(41,69,50,0.05)] sm:px-10">
              <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
                <div>
                  <p className="font-mono text-[9px] uppercase tracking-[2.25px] text-latiim-texto">Governança</p>
                  <h1 className="mt-4 font-display text-3xl font-normal tracking-tight text-tinta sm:text-4xl">
                    Trilha de auditoria
                  </h1>
                  <p className="mt-3 max-w-2xl text-sm leading-7 text-tinta-suave">
                    Eventos de segurança e de fluxo da sua conta, do mais novo ao mais antigo. Conteúdo
                    de documentos e perguntas nunca ficam gravados aqui — só identificadores, estados e tempos.
                  </p>
                </div>
                <select
                  value={eventType}
                  onChange={(event) => setEventType(event.target.value)}
                  className="rounded-[5px] border border-linha bg-white px-4 py-2.5 text-sm text-tinta outline-none transition-colors hover:border-latiim focus:border-latiim"
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
                <p className="mt-4 rounded-[5px] border border-red-200 bg-red-50 px-5 py-3 text-sm text-red-700">
                  {error}
                </p>
              )}

              <div className="mt-6 overflow-hidden rounded-[5px] border border-linha">
                {isLoading ? (
                  <p className="bg-papel-alta px-5 py-8 text-sm text-tinta-muda">Carregando…</p>
                ) : events.length === 0 ? (
                  <p className="bg-papel-alta px-5 py-8 text-sm leading-7 text-tinta-muda">
                    Nada por aqui ainda. Envie um documento ou gere uma defesa para preencher esta trilha.
                  </p>
                ) : (
                  <ul className="divide-y divide-linha bg-white">
                    {events.map((item) => (
                      <li key={item.id} className="px-5 py-4">
                        <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
                          <p className="text-sm font-medium text-tinta">{item.event_type}</p>
                          {item.created_at && (
                            <p className="text-xs text-tinta-muda">
                              {new Date(item.created_at).toLocaleString()}
                            </p>
                          )}
                        </div>
                        {(item.entity_type || item.entity_id) && (
                          <p className="mt-1 break-all font-mono text-xs text-tinta-muda">
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
