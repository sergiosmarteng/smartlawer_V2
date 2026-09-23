import Head from 'next/head';
import Link from 'next/link';
import { useEffect, useRef, useState } from 'react';
import AuthGuard from '../components/auth/AuthGuard';
import Layout from '../components/layout';
import api, { getApiErrorMessage } from '../lib/axios';
import {
  isSuccessStatus,
  type ProcessItem,
} from '../types/workflow';

const API_BASE = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1').replace(/\/+$/, '');

interface Citation {
  ref: string;
  chunk_id: string;
  document_id: string;
  document_name: string;
  page_start?: number | null;
  excerpt: string;
}

interface ChatMessage {
  role: 'user' | 'assistant';
  text: string;
  citations?: Citation[];
  suggestions?: string[];
}

function parseSseEvents(raw: string): Array<Record<string, unknown>> {
  const events: Array<Record<string, unknown>> = [];
  for (const line of raw.split('\n')) {
    if (line.startsWith('data: ')) {
      try {
        events.push(JSON.parse(line.slice('data: '.length)));
      } catch {
        // Ignore partial frames; the next flush completes them.
      }
    }
  }
  return events;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState('');
  const [documents, setDocuments] = useState<ProcessItem[]>([]);
  const [docsLoading, setDocsLoading] = useState(true);
  const [docsError, setDocsError] = useState('');
  const [documentId, setDocumentId] = useState('');
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    const fetchDocuments = async () => {
      setDocsLoading(true);
      setDocsError('');
      try {
        const response = await api.get<ProcessItem[]>('/processes');
        setDocuments(Array.isArray(response.data) ? response.data : []);
      } catch (fetchError) {
        setDocsError(getApiErrorMessage(fetchError, 'Não foi possível carregar o histórico.'));
      } finally {
        setDocsLoading(false);
      }
    };
    fetchDocuments();
  }, []);

  const handleScopeChange = (nextDocumentId: string) => {
    abortRef.current?.abort();
    setIsStreaming(false);
    setDocumentId(nextDocumentId);
    setMessages([]);
    setError('');
    setInput('');
  };

  const sendMessage = async (override?: string) => {
    const query = (override ?? input).trim();
    if (!query || isStreaming) {
      return;
    }

    // Backend requires min_length=3 (ChatRequest); fail fast with a
    // friendly message instead of a bare "HTTP 422".
    if (query.length < 3) {
      setError('Escreva uma pergunta com pelo menos 3 caracteres.');
      return;
    }

    const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
    if (!token) {
      setError('Sessão expirada. Entre novamente.');
      return;
    }

    setError('');
    setInput('');
    setIsStreaming(true);
    setMessages((current) => [...current, { role: 'user', text: query }, { role: 'assistant', text: '' }]);

    try {
      abortRef.current = new AbortController();
      const response = await fetch(`${API_BASE}/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(documentId ? { query, document_id: documentId } : { query }),
        signal: abortRef.current.signal,
      });

      if (!response.ok || !response.body) {
        throw new Error(`HTTP ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      for (;;) {
        const { done, value } = await reader.read();
        if (done) {
          break;
        }
        buffer += decoder.decode(value, { stream: true });
        const events = parseSseEvents(buffer);

        setMessages((current) => {
          const next = [...current];
          const last = next[next.length - 1];
          let text = '';
          let citations: Citation[] | undefined;
          let suggestions: string[] | undefined;
          for (const event of events) {
            if (typeof event.token === 'string') {
              text += event.token;
            }
            if (event.done === true) {
              citations = (event.citations as Citation[]) ?? [];
              if (Array.isArray(event.suggested_questions)) {
                suggestions = (event.suggested_questions as unknown[]).filter(
                  (item): item is string => typeof item === 'string' && item.trim().length > 0,
                );
              } else {
                suggestions = [];
              }
            }
          }
          next[next.length - 1] = {
            ...last,
            text,
            citations: citations ?? last.citations,
            suggestions: suggestions ?? last.suggestions,
          };
          return next;
        });
      }
    } catch (err) {
      if (err instanceof DOMException && err.name === 'AbortError') {
        return;
      }
      setError(getApiErrorMessage(err, 'Falha ao conversar com os documentos.'));
    } finally {
      setIsStreaming(false);
    }
  };

  return (
    <AuthGuard>
      <Layout>
        <Head>
          <title>Chat jurídico — SmartLawer</title>
        </Head>

        <div className="mx-auto flex h-[calc(100vh-10rem)] max-w-5xl flex-col px-4 sm:px-6">
          <div className="mb-4">
            <p className="font-mono text-xs uppercase tracking-[0.32em] text-ouro-400">Chat jurídico</p>
            <h1 className="mt-2 font-display text-3xl font-black text-slate-50">Pergunte com fundamento</h1>
            <p className="mt-1 text-sm text-zinc-400">
              Selecione o caso no histórico e questione. Cada afirmação vem com a fonte clicável.
            </p>
          </div>

          <div className="mb-4 rounded-2xl border border-zinc-800 bg-tribunal-900/60 p-4">
            <label
              htmlFor="chat-document-scope"
              className="font-mono text-xs uppercase tracking-[0.24em] text-zinc-500"
            >
              Caso em análise
            </label>
            <select
              id="chat-document-scope"
              value={documentId}
              onChange={(event) => handleScopeChange(event.target.value)}
              disabled={docsLoading || isStreaming}
              className="mt-2 w-full rounded-xl border border-zinc-700 bg-tribunal-950 px-3 py-2.5 text-sm text-slate-100 focus:border-ouro-500/60 focus:outline-none disabled:opacity-60"
            >
              <option value="">Todos os documentos do histórico</option>
              {documents.map((document) => (
                <option key={document.id} value={document.id}>
                  {document.title}
                  {isSuccessStatus(document.status) ? '' : ` — ${document.status}`}
                </option>
              ))}
            </select>
            {docsLoading && <p className="mt-2 text-xs text-zinc-500">Carregando histórico…</p>}
            {docsError && <p className="mt-2 text-xs text-red-400">{docsError}</p>}
            {!docsLoading && !docsError && documents.length === 0 && (
              <p className="mt-2 text-xs text-zinc-500">
                Nenhum documento no histórico ainda.{' '}
                <Link href="/upload" className="text-ouro-300 underline underline-offset-4 hover:text-ouro-200">
                  Envie o primeiro PDF
                </Link>
                .
              </p>
            )}
          </div>

          <div className="flex-1 space-y-4 overflow-y-auto rounded-3xl border border-zinc-800 bg-tribunal-900/40 p-5">
            {messages.length === 0 && (
              <div className="space-y-3">
                <p className="text-sm text-zinc-500">
                  Selecione o caso acima e pergunte como a um sócio sênior — o assistente
                  passa a atuar como especialista na área daquele documento.
                </p>
                <div className="flex flex-wrap gap-2">
                  {[
                    'Qual a tese de defesa mais forte deste caso?',
                    'Monte uma estratégia de ataque focando o juiz nos pontos da contestação',
                    'O que devo elucidar antes de protocolar?',
                  ].map((suggestion) => (
                    <button
                      key={suggestion}
                      type="button"
                      onClick={() => sendMessage(suggestion)}
                      disabled={isStreaming}
                      className="rounded-full border border-zinc-700 bg-tribunal-900/70 px-3 py-1.5 text-left text-xs text-zinc-300 transition-colors hover:border-ouro-500/40 hover:text-ouro-200 disabled:opacity-50"
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {messages.map((message, index) => (
              <div key={index} className={message.role === 'user' ? 'flex justify-end' : 'flex justify-start'}>
                <div
                  className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-6 ${
                    message.role === 'user'
                      ? 'bg-ouro-500/15 text-ouro-100'
                      : 'border border-zinc-800 bg-tribunal-950 text-slate-200'
                  }`}
                >
                  <p className="whitespace-pre-wrap">{message.text || '…'}</p>

                  {message.role === 'assistant' &&
                    message.suggestions &&
                    message.suggestions.length > 0 && (
                      <div className="mt-3 border-t border-zinc-800 pt-3">
                        <p className="text-xs uppercase tracking-[0.2em] text-zinc-500">
                          Aprofundar
                        </p>
                        <div className="mt-2 flex flex-wrap gap-2">
                          {message.suggestions.map((suggestion) => (
                            <button
                              key={suggestion}
                              type="button"
                              onClick={() => sendMessage(suggestion)}
                              disabled={isStreaming}
                              className="rounded-full border border-ouro-500/40 bg-ouro-500/10 px-3 py-1.5 text-left text-xs text-ouro-200 transition-colors hover:bg-ouro-500/20 disabled:opacity-50"
                            >
                              {suggestion}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}

                  {message.citations && message.citations.length > 0 && (
                    <div className="mt-3 space-y-2 border-t border-zinc-800 pt-3">
                      <p className="text-xs uppercase tracking-[0.2em] text-zinc-500">Fontes</p>
                      {message.citations.map((citation) => {
                        const isPrecedent = citation.document_name.startsWith('[Jurisprudência]');
                        const body = (
                          <>
                            <p className="text-xs font-medium text-ouro-300">
                              {citation.ref} {citation.document_name}
                              {typeof citation.page_start === 'number'
                                ? ` · p. ${citation.page_start}`
                                : ''}
                            </p>
                            <p className="mt-1 line-clamp-2 text-xs text-zinc-400">{citation.excerpt}</p>
                          </>
                        );
                        // Precedent chunks have no analysis page — render as a
                        // badge instead of a link (C5/BL-023).
                        return isPrecedent ? (
                          <div
                            key={citation.chunk_id}
                            className="block rounded-xl border border-amber-800/60 bg-amber-950/20 px-3 py-2"
                          >
                            {body}
                          </div>
                        ) : (
                          <Link
                            key={citation.chunk_id}
                            href={`/analysis/${citation.document_id}`}
                            className="block rounded-xl border border-zinc-800 bg-tribunal-900/80 px-3 py-2 transition-colors hover:border-ouro-500/40"
                          >
                            {body}
                          </Link>
                        );
                      })}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>

          {error && <p className="mt-3 text-sm text-red-400">{error}</p>}

          <div className="mt-4 flex gap-2">
            <input
              value={input}
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === 'Enter' && !event.shiftKey) {
                  event.preventDefault();
                  sendMessage();
                }
              }}
              placeholder="Pergunte sobre os seus documentos…"
              aria-label="Pergunta para o chat jurídico"
              disabled={isStreaming}
              className="flex-1 rounded-2xl border border-zinc-800 bg-tribunal-950 px-4 py-3 text-sm text-slate-100 placeholder:text-zinc-600 focus:border-ouro-500/60 focus:outline-none disabled:opacity-60"
            />
            <button
              type="button"
              onClick={() => sendMessage()}
              disabled={isStreaming || !input.trim()}
              className="rounded-2xl border border-ouro-500/40 bg-ouro-500/10 px-5 py-3 text-sm font-medium text-ouro-200 transition-colors hover:bg-ouro-500/20 disabled:opacity-50"
            >
              {isStreaming ? 'Aguarde…' : 'Enviar'}
            </button>
          </div>

          <p className="mt-2 text-xs text-zinc-600">
            Parecer e estratégia elaborados por IA — fatos com fonte citada; a decisão e a
            responsabilidade são do advogado. Nunca protocola sozinho.
          </p>
        </div>
      </Layout>
    </AuthGuard>
  );
}
