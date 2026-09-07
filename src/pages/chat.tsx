import Head from 'next/head';
import Link from 'next/link';
import { useRef, useState } from 'react';
import AuthGuard from '../components/auth/AuthGuard';
import Layout from '../components/layout';
import { getApiErrorMessage } from '../lib/axios';

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
  const abortRef = useRef<AbortController | null>(null);

  const sendMessage = async () => {
    const query = input.trim();
    if (!query || isStreaming) {
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
        body: JSON.stringify({ query }),
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
          for (const event of events) {
            if (typeof event.token === 'string') {
              text += event.token;
            }
            if (event.done === true) {
              citations = (event.citations as Citation[]) ?? [];
            }
          }
          next[next.length - 1] = { ...last, text, citations: citations ?? last.citations };
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
            <h1 className="text-xl font-medium text-slate-100">Chat jurídico fundamentado</h1>
            <p className="mt-1 text-sm text-zinc-400">
              Pergunte sobre os seus documentos. Cada afirmação vem com a fonte clicável.
            </p>
          </div>

          <div className="flex-1 space-y-4 overflow-y-auto rounded-3xl border border-zinc-800 bg-zinc-900/40 p-5">
            {messages.length === 0 && (
              <p className="text-sm text-zinc-500">
                Nenhuma mensagem ainda. Experimente: “Qual o prazo para contestação nos meus documentos?”
              </p>
            )}

            {messages.map((message, index) => (
              <div key={index} className={message.role === 'user' ? 'flex justify-end' : 'flex justify-start'}>
                <div
                  className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-6 ${
                    message.role === 'user'
                      ? 'bg-sky-500/15 text-sky-100'
                      : 'border border-zinc-800 bg-zinc-950 text-slate-200'
                  }`}
                >
                  <p className="whitespace-pre-wrap">{message.text || '…'}</p>

                  {message.citations && message.citations.length > 0 && (
                    <div className="mt-3 space-y-2 border-t border-zinc-800 pt-3">
                      <p className="text-xs uppercase tracking-[0.2em] text-zinc-500">Fontes</p>
                      {message.citations.map((citation) => (
                        <Link
                          key={citation.chunk_id}
                          href={`/analysis/${citation.document_id}`}
                          className="block rounded-xl border border-zinc-800 bg-zinc-900/80 px-3 py-2 transition-colors hover:border-sky-500/40"
                        >
                          <p className="text-xs font-medium text-sky-300">
                            {citation.ref} {citation.document_name}
                            {typeof citation.page_start === 'number' ? ` · p. ${citation.page_start}` : ''}
                          </p>
                          <p className="mt-1 line-clamp-2 text-xs text-zinc-400">{citation.excerpt}</p>
                        </Link>
                      ))}
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
              disabled={isStreaming}
              className="flex-1 rounded-2xl border border-zinc-800 bg-zinc-950 px-4 py-3 text-sm text-slate-100 placeholder:text-zinc-600 focus:border-sky-500/50 focus:outline-none disabled:opacity-60"
            />
            <button
              type="button"
              onClick={sendMessage}
              disabled={isStreaming || !input.trim()}
              className="rounded-2xl border border-sky-400/30 bg-sky-400/10 px-5 py-3 text-sm font-medium text-sky-200 transition-colors hover:bg-sky-400/20 disabled:opacity-50"
            >
              {isStreaming ? 'Aguarde…' : 'Enviar'}
            </button>
          </div>

          <p className="mt-2 text-xs text-zinc-600">
            Rascunho gerado por IA — revise antes de usar. Nunca protocola sozinho.
          </p>
        </div>
      </Layout>
    </AuthGuard>
  );
}
