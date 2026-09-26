import Head from 'next/head';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import AuthGuard from '../../../components/auth/AuthGuard';
import Layout from '../../../components/layout';
import { apiV2, getApiErrorMessage } from '../../../lib/axios';
import type {
  V2Artifact,
  V2ReviewEvent,
  V2RunStatus,
  V2Source,
} from '../../../types/workflow';

const TABS = [
  { id: 'visao', label: 'Visão geral' },
  { id: 'pedidos', label: 'Pedidos' },
  { id: 'fatos', label: 'Fatos' },
  { id: 'provas', label: 'Provas' },
  { id: 'direito', label: 'Direito' },
  { id: 'teses', label: 'Teses' },
  { id: 'calculos', label: 'Cálculos' },
  { id: 'acoes', label: 'Ações' },
  { id: 'revisao', label: 'Revisão' },
] as const;

type TabId = (typeof TABS)[number]['id'];

function asArray(value: unknown): Array<Record<string, unknown>> {
  return Array.isArray(value) ? (value as Array<Record<string, unknown>>) : [];
}

function asText(value: unknown): string {
  if (typeof value === 'string') return value;
  if (value == null) return '';
  return String(value);
}

/** Texto puro (React escapa por padrão: sem HTML/script executável). */
function SafeText({ value }: { value: unknown }) {
  return <>{asText(value)}</>;
}

export default function DossieV2Page() {
  const router = useRouter();
  const routeId = Array.isArray(router.query.id) ? router.query.id[0] : router.query.id;
  const documentId = Array.isArray(router.query.document_id)
    ? router.query.document_id[0]
    : router.query.document_id;

  const [artifact, setArtifact] = useState<V2Artifact | null>(null);
  const [run, setRun] = useState<V2RunStatus | null>(null);
  const [activeTab, setActiveTab] = useState<TabId>('visao');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [source, setSource] = useState<V2Source | null>(null);
  const [sourceLoading, setSourceLoading] = useState(false);
  const [reviewEvents, setReviewEvents] = useState<V2ReviewEvent[]>([]);
  const [reviewReason, setReviewReason] = useState('');
  const [reviewNotice, setReviewNotice] = useState('');
  const [reanalyzeNotice, setReanalyzeNotice] = useState('');
  const tabRefs = useRef<Array<HTMLButtonElement | null>>([]);

  const fetchArtifact = useCallback(async (artifactId: string) => {
    const response = await apiV2.get<V2Artifact>(`/analyses/${artifactId}`);
    setArtifact(response.data);
    try {
      const events = await apiV2.get<V2ReviewEvent[]>(
        `/analyses/${artifactId}/review-events`
      );
      setReviewEvents(Array.isArray(events.data) ? events.data : []);
    } catch {
      setReviewEvents([]);
    }
    return response.data;
  }, []);

  useEffect(() => {
    if (!routeId && !documentId) return;
    const load = async () => {
      setIsLoading(true);
      setError('');
      try {
        let artifactId = routeId;
        if (!artifactId && documentId) {
          const runs = await apiV2.get<V2RunStatus[]>(
            `/analysis-runs?document_id=${documentId}`
          );
          const withArtifact = (runs.data || []).find((r) => r.artifact_id);
          if (!withArtifact?.artifact_id) {
            throw new Error('no-v2-run');
          }
          artifactId = withArtifact.artifact_id;
          setRun(withArtifact);
        }
        const data = await fetchArtifact(artifactId as string);
        if (data.run_id) {
          try {
            const runResp = await apiV2.get<V2RunStatus>(
              `/analysis-runs/${data.run_id}`
            );
            setRun(runResp.data);
          } catch {
            /* estado da execução é complementar */
          }
        }
      } catch (fetchError) {
        setArtifact(null);
        const message =
          fetchError instanceof Error && fetchError.message === 'no-v2-run'
            ? 'Este documento ainda não tem dossiê V2. Reenvie para gerar a primeira execução versionada.'
            : getApiErrorMessage(fetchError, 'Não foi possível carregar o dossiê V2.');
        setError(message);
      } finally {
        setIsLoading(false);
      }
    };
    load();
  }, [routeId, documentId, fetchArtifact]);

  const content = useMemo(
    () => (artifact?.content || {}) as Record<string, unknown>,
    [artifact]
  );

  const openSource = useCallback(async (sourceId: string) => {
    setSourceLoading(true);
    try {
      const response = await apiV2.get<V2Source>(`/sources/${sourceId}`);
      setSource(response.data);
    } catch {
      setSource(null);
    } finally {
      setSourceLoading(false);
    }
  }, []);

  const onTabKeyDown = useCallback(
    (event: React.KeyboardEvent, index: number) => {
      let next = index;
      if (event.key === 'ArrowRight') next = (index + 1) % TABS.length;
      else if (event.key === 'ArrowLeft') next = (index - 1 + TABS.length) % TABS.length;
      else if (event.key === 'Home') next = 0;
      else if (event.key === 'End') next = TABS.length - 1;
      else return;
      event.preventDefault();
      setActiveTab(TABS[next].id);
      tabRefs.current[next]?.focus();
    },
    []
  );

  const submitReview = useCallback(async () => {
    if (!artifact || !reviewReason.trim()) return;
    setReviewNotice('');
    try {
      await apiV2.post(`/analyses/${artifact.id}/review-events`, {
        target: 'artifact',
        reason: reviewReason.trim(),
        expected_version: run?.version,
      });
      setReviewReason('');
      setReviewNotice('Correção registrada. Compare a versão antes de aprovar.');
      const data = await fetchArtifact(artifact.id);
      setArtifact(data);
    } catch (submitError) {
      setReviewNotice(getApiErrorMessage(submitError, 'Falha ao registrar revisão.'));
    }
  }, [artifact, reviewReason, run, fetchArtifact]);

  const reanalyze = useCallback(async () => {
    if (!artifact) return;
    setReanalyzeNotice('');
    try {
      const response = await apiV2.post(`/analyses/${artifact.id}/reanalyze`);
      setReanalyzeNotice(
        `Nova execução criada: ${response.data.run_id}. O original foi preservado.`
      );
    } catch (reanalyzeError) {
      setReanalyzeNotice(getApiErrorMessage(reanalyzeError, 'Falha ao reanalisar.'));
    }
  }, [artifact]);

  return (
    <AuthGuard>
      <Layout>
        <Head>
          <title>Dossiê V2 — SmartLawer</title>
        </Head>
        <main className="mx-auto max-w-6xl px-4 py-6">
          <Link href="/dashboard" className="text-sm underline">
            ← Voltar ao painel
          </Link>
          <h1 className="mt-2 text-2xl font-bold">Dossiê jurídico V2</h1>

          {isLoading && <p role="status">Carregando dossiê…</p>}
          {!isLoading && error && (
            <p role="alert" className="mt-4 rounded border p-4">
              <SafeText value={error} />
            </p>
          )}

          {!isLoading && artifact && (
            <>
              <DossieHeader artifact={artifact} run={run} />
              {artifact.status === 'partial' && (
                <p role="status" className="mt-3 rounded border p-3">
                  Análise parcial: use o que está documentado e conclua as
                  pendências na aba Ações antes de aprovar.
                </p>
              )}

              <div className="mt-4 flex flex-col gap-4 lg:flex-row">
                <div className="flex-1">
                  <div role="tablist" aria-label="Seções do dossiê" className="flex flex-wrap gap-1">
                    {TABS.map((tab, index) => (
                      <button
                        key={tab.id}
                        ref={(el) => {
                          tabRefs.current[index] = el;
                        }}
                        role="tab"
                        aria-selected={activeTab === tab.id}
                        tabIndex={activeTab === tab.id ? 0 : -1}
                        onClick={() => setActiveTab(tab.id)}
                        onKeyDown={(event) => onTabKeyDown(event, index)}
                        className="rounded border px-3 py-1 text-sm"
                      >
                        {tab.label}
                      </button>
                    ))}
                  </div>

                  <section role="tabpanel" aria-label={activeTab} className="mt-3">
                    <TabPanel
                      tab={activeTab}
                      content={content}
                      artifact={artifact}
                      reviewEvents={reviewEvents}
                      reviewReason={reviewReason}
                      setReviewReason={setReviewReason}
                      submitReview={submitReview}
                      reviewNotice={reviewNotice}
                      reanalyze={reanalyze}
                      reanalyzeNotice={reanalyzeNotice}
                      openSource={openSource}
                    />
                  </section>
                </div>

                <aside aria-label="Fonte" className="w-full lg:w-80">
                  <div className="rounded border p-3">
                    <h2 className="font-semibold">Fonte</h2>
                    {sourceLoading && <p role="status">Abrindo fonte…</p>}
                    {!sourceLoading && !source && (
                      <p className="text-sm">Use “Ver fonte” em qualquer item.</p>
                    )}
                    {!sourceLoading && source && (
                      <dl className="mt-2 space-y-1 text-sm">
                        <div>
                          <dt className="font-semibold">Página</dt>
                          <dd>{source.page_number ?? '—'}</dd>
                        </div>
                        <div>
                          <dt className="font-semibold">Verificação</dt>
                          <dd>
                            <SafeText value={source.verification_status} />
                          </dd>
                        </div>
                        {source.quote && (
                          <div>
                            <dt className="font-semibold">Trecho</dt>
                            <dd>
                              <SafeText value={source.quote} />
                            </dd>
                          </div>
                        )}
                        {source.url && (
                          <div>
                            <dt className="font-semibold">URL</dt>
                            <dd>
                              <SafeText value={source.url} />
                            </dd>
                          </div>
                        )}
                      </dl>
                    )}
                  </div>
                </aside>
              </div>
            </>
          )}
        </main>
      </Layout>
    </AuthGuard>
  );
}

function DossieHeader({ artifact, run }: { artifact: V2Artifact; run: V2RunStatus | null }) {
  const content = artifact.content as Record<string, unknown>;
  const scope = (content.scope || {}) as Record<string, unknown>;
  const coverage = (content.coverage || {}) as Record<string, unknown>;
  return (
    <div className="mt-3 rounded border p-4">
      <p className="text-sm">
        polo: <SafeText value={scope.represented_side ?? 'neutral'} /> · versão{' '}
        <SafeText value={artifact.schema_version} /> · estado{' '}
        <SafeText value={artifact.status} /> · revisão{' '}
        <SafeText value={artifact.review_status} />
      </p>
      <p className="text-sm">
        páginas: <SafeText value={coverage.pages_extracted ?? 0} />/
        <SafeText value={coverage.pages_total ?? 0} />
        {run && (
          <>
            {' '}· andamento: <SafeText value={run.progress} />% (
            <SafeText value={run.stage ?? run.status} />)
          </>
        )}
      </p>
    </div>
  );
}

function SourceButton({ id, openSource }: { id: unknown; openSource: (id: string) => void }) {
  if (typeof id !== 'string' || !id) return null;
  return (
    <button
      type="button"
      onClick={() => openSource(id)}
      className="ml-2 text-sm underline"
      aria-label={`Ver fonte ${id}`}
    >
      Ver fonte
    </button>
  );
}

function TabPanel(props: {
  tab: TabId;
  content: Record<string, unknown>;
  artifact: V2Artifact;
  reviewEvents: V2ReviewEvent[];
  reviewReason: string;
  setReviewReason: (value: string) => void;
  submitReview: () => void;
  reviewNotice: string;
  reanalyze: () => void;
  reanalyzeNotice: string;
  openSource: (id: string) => void;
}) {
  const { tab, content, artifact, openSource } = props;
  const limitations = asArray(content.limitations);

  if (tab === 'visao') {
    const coverage = (content.coverage || {}) as Record<string, unknown>;
    return (
      <div className="space-y-2">
        <p>
          Pedidos: {asArray(content.claims).length} · páginas{' '}
          {asText(coverage.pages_extracted ?? 0)}/{asText(coverage.pages_total ?? 0)}
        </p>
        {limitations.map((lim, i) => (
          <p key={i} className="text-sm">
            ⚠ <SafeText value={lim.message} />
          </p>
        ))}
      </div>
    );
  }

  if (tab === 'pedidos') {
    const claims = asArray(content.claims);
    if (!claims.length) return <EmptyState text="Nenhum pedido registrado — array vazio sem explicação é inválido; revise a extração." />;
    return (
      <ul className="space-y-3">
        {claims.map((claim, i) => (
          <li key={asText(claim.id || i)} className="rounded border p-3">
            <p className="font-semibold">
              {asText(claim.original_number) ? `#${asText(claim.original_number)} — ` : ''}
              <SafeText value={claim.title} />
            </p>
            {asText(claim.requested_relief) ? (
              <p className="text-sm">
                <SafeText value={claim.requested_relief} />
              </p>
            ) : null}
            <p className="text-sm">
              refs:{' '}
              {asArray(claim.source_refs).map((ref) => (
                <SourceButton key={asText(ref)} id={asText(ref)} openSource={openSource} />
              ))}
              {!asArray(claim.source_refs).length && 'a confirmar'}
            </p>
          </li>
        ))}
      </ul>
    );
  }

  if (tab === 'fatos') {
    const facts = asArray(content.facts);
    if (!facts.length) return <EmptyState text="Nenhum fato registrado." />;
    return (
      <ul className="space-y-2">
        {facts.map((fact, i) => (
          <li key={i} className="rounded border p-3 text-sm">
            <p>
              <SafeText value={fact.statement} /> [{asText(fact.epistemic_status)}]
            </p>
            <p>
              afirmado por: <SafeText value={fact.asserted_by} />
              {asArray(fact.source_refs).map((ref) => (
                <SourceButton key={asText(ref)} id={asText(ref)} openSource={openSource} />
              ))}
            </p>
          </li>
        ))}
      </ul>
    );
  }

  if (tab === 'provas') {
    const evidence = asArray(content.evidence);
    if (!evidence.length) return <EmptyState text="Nenhuma prova registrada." />;
    return (
      <ul className="space-y-2">
        {evidence.map((item, i) => (
          <li key={asText(item.id || i)} className="rounded border p-3 text-sm">
            <p className="font-semibold">
              <SafeText value={item.kind} /> — <SafeText value={item.presence_status} />
            </p>
            {asText(item.limitations) ? (
              <p>
                <SafeText value={item.limitations} />
              </p>
            ) : null}
          </li>
        ))}
      </ul>
    );
  }

  if (tab === 'direito') {
    const refs = asArray(content.legal_references);
    if (!refs.length) return <EmptyState text="Nenhum fundamento registrado." />;
    return (
      <ul className="space-y-2">
        {refs.map((ref, i) => (
          <li key={asText(ref.id || i)} className="rounded border p-3 text-sm">
            <p>
              <SafeText value={ref.literal_citation} /> (
              <SafeText value={ref.verification_status} />)
            </p>
          </li>
        ))}
      </ul>
    );
  }

  if (tab === 'teses') {
    const theses = asArray(content.theses);
    if (!theses.length) return <EmptyState text="Nenhuma tese registrada." />;
    return (
      <ul className="space-y-2">
        {theses.map((thesis, i) => (
          <li key={asText(thesis.id || i)} className="rounded border p-3 text-sm">
            <p className="font-semibold">
              [{asText(thesis.represented_side)}] <SafeText value={thesis.issue} />
            </p>
            <p>
              <SafeText value={thesis.conclusion} />
            </p>
            {asText(thesis.limitations) ? (
              <p>
                Limites: <SafeText value={thesis.limitations} />
              </p>
            ) : null}
          </li>
        ))}
      </ul>
    );
  }

  if (tab === 'calculos') {
    const calculations = asArray(content.calculations);
    if (!calculations.length) return <EmptyState text="Nenhum cálculo registrado." />;
    return (
      <ul className="space-y-2">
        {calculations.map((calc, i) => (
          <li key={asText(calc.id || i)} className="rounded border p-3 text-sm">
            <p className="font-semibold">
              <SafeText value={calc.formula} /> v<SafeText value={calc.formula_version} /> ={' '}
              <SafeText value={calc.result} />
            </p>
          </li>
        ))}
      </ul>
    );
  }

  if (tab === 'acoes') {
    const risks = asArray(content.risks);
    return (
      <div className="space-y-2">
        {risks.map((risk, i) => (
          <p key={i} className="rounded border p-3 text-sm">
            <SafeText value={risk.issue} /> — <SafeText value={risk.mitigation} />
          </p>
        ))}
        {limitations.map((lim, i) => (
          <p key={`lim-${i}`} className="rounded border p-3 text-sm">
            ⚠ <SafeText value={lim.message} />
          </p>
        ))}
        {!risks.length && !limitations.length && (
          <EmptyState text="Nenhuma ação pendente." />
        )}
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <p className="text-sm">
        Revisão: <SafeText value={artifact.review_status} /> (sem selo sem aprovação
        de usuário habilitado)
      </p>
      <ul className="space-y-1 text-sm">
        {props.reviewEvents.map((event) => (
          <li key={event.id} className="rounded border p-2">
            <SafeText value={event.target} /> — <SafeText value={event.reason} />
          </li>
        ))}
      </ul>
      <label className="block text-sm">
        Registrar correção
        <textarea
          value={props.reviewReason}
          onChange={(event) => props.setReviewReason(event.target.value)}
          className="mt-1 block w-full rounded border p-2"
          rows={3}
        />
      </label>
      <div className="flex gap-2">
        <button type="button" onClick={props.submitReview} className="rounded border px-3 py-1">
          Enviar correção
        </button>
        <button type="button" onClick={props.reanalyze} className="rounded border px-3 py-1">
          Reanalisar (nova execução)
        </button>
      </div>
      {props.reviewNotice && <p role="status">{props.reviewNotice}</p>}
      {props.reanalyzeNotice && <p role="status">{props.reanalyzeNotice}</p>}
    </div>
  );
}

function EmptyState({ text }: { text: string }) {
  return <p className="rounded border p-3 text-sm">{text}</p>;
}
