import Head from "next/head";
import Link from "next/link";
import { useRouter } from "next/router";
import { useCallback, useEffect, useState } from "react";
import AuthGuard from "../../../components/auth/AuthGuard";
import Layout from "../../../components/layout";
import { DossierHeader } from "../../../components/dossier/DossierHeader";
import {
  DOSSIER_TABS,
  DossierTabId,
  DossierTabs,
} from "../../../components/dossier/DossierTabs";
import {
  SourceViewer,
  SourceDetail,
} from "../../../components/dossier/SourceViewer";
import { VisualGallery } from "../../../components/dossier/VisualGallery";
import {
  ActionsSection,
  CalculationsSection,
  ClaimsSection,
  EvidenceSection,
  FactsSection,
  LegalSection,
  OverviewSection,
  ThesesSection,
} from "../../../components/dossier/sections/sections";
import { ReviewSection } from "../../../components/dossier/sections/ReviewSection";
import { useAnalysisRun } from "../../../hooks/useAnalysisRun";
import { useDossier } from "../../../hooks/useDossier";
import { apiV2, getApiErrorMessage } from "../../../lib/axios";
import type { V2ReviewEvent } from "../../../types/workflow";

/**
 * Dossiê V2 — composição fina (Onda 0 Task 14).
 *
 * Dados via `useDossier`/`useAnalysisRun`; apresentação nos componentes
 * de `src/components/dossier/*`. Sem regras de domínio aqui.
 */
export default function DossieV2Page() {
  const router = useRouter();
  const routeId = Array.isArray(router.query.id)
    ? router.query.id[0]
    : router.query.id;
  const documentId = Array.isArray(router.query.document_id)
    ? router.query.document_id[0]
    : router.query.document_id;

  const { artifact, isLegacy, loading, errorMessage } = useDossier({
    artifactId: routeId,
    documentId,
  });
  const { run } = useAnalysisRun(artifact?.run_id);
  const [activeTab, setActiveTab] = useState<DossierTabId>("visao");
  const [source, setSource] = useState<SourceDetail | null>(null);
  const [sourceLoading, setSourceLoading] = useState(false);
  const [reviewEvents, setReviewEvents] = useState<V2ReviewEvent[]>([]);
  const [reviewReason, setReviewReason] = useState("");
  const [reviewNotice, setReviewNotice] = useState("");
  const [reanalyzeNotice, setReanalyzeNotice] = useState("");

  const artifactId = artifact?.id;

  useEffect(() => {
    if (!artifactId) return;
    let cancelled = false;
    apiV2
      .get<V2ReviewEvent[]>(`/analyses/${artifactId}/review-events`)
      .then((events) => {
        if (!cancelled)
          setReviewEvents(Array.isArray(events.data) ? events.data : []);
      })
      .catch(() => {
        if (!cancelled) setReviewEvents([]);
      });
    return () => {
      cancelled = true;
    };
  }, [artifactId]);

  const openSource = useCallback(async (sourceId: string) => {
    setSourceLoading(true);
    try {
      const response = await apiV2.get<SourceDetail>(`/sources/${sourceId}`);
      setSource(response.data);
    } catch {
      setSource(null);
    } finally {
      setSourceLoading(false);
    }
  }, []);

  const submitReview = useCallback(async () => {
    if (!artifactId || !reviewReason.trim()) return;
    setReviewNotice("");
    try {
      await apiV2.post(`/analyses/${artifactId}/review-events`, {
        target: "artifact",
        reason: reviewReason.trim(),
        expected_version: run?.version,
      });
      setReviewReason("");
      setReviewNotice(
        "Correção registrada. Compare a versão antes de aprovar.",
      );
    } catch (submitError) {
      setReviewNotice(
        getApiErrorMessage(submitError, "Falha ao registrar revisão."),
      );
    }
  }, [artifactId, reviewReason, run]);

  const reanalyze = useCallback(async () => {
    if (!artifactId) return;
    setReanalyzeNotice("");
    try {
      const response = await apiV2.post(`/analyses/${artifactId}/reanalyze`);
      setReanalyzeNotice(
        `Nova execução criada: ${response.data.run_id}. O original foi preservado.`,
      );
    } catch (reanalyzeError) {
      setReanalyzeNotice(
        getApiErrorMessage(reanalyzeError, "Falha ao reanalisar."),
      );
    }
  }, [artifactId]);

  const content = ((artifact?.content || {}) as Record<string, unknown>) ?? {};
  const activeTabLabel =
    DOSSIER_TABS.find((tab) => tab.id === activeTab)?.label ?? activeTab;

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

          {loading && <p role="status">Carregando dossiê…</p>}
          {!loading && errorMessage && (
            <p role="alert" className="mt-4 rounded border p-4">
              {errorMessage}
            </p>
          )}

          {!loading && artifact && (
            <>
              <DossierHeader
                artifact={{
                  schema_version: artifact.schema_version,
                  status: artifact.status,
                  review_status: artifact.review_status,
                  content,
                }}
                run={
                  run
                    ? {
                        progress: run.progress,
                        stage: run.stage,
                        status: run.status,
                      }
                    : null
                }
              />
              {isLegacy && (
                <p role="status" className="mt-3 rounded border p-3">
                  Análise legada sem fontes localizadas — reanalise para gerar o
                  Dossiê Universal.
                </p>
              )}
              {artifact.status === "partial" && (
                <p role="status" className="mt-3 rounded border p-3">
                  Análise parcial: use o que está documentado e conclua as
                  pendências na aba Ações antes de aprovar.
                </p>
              )}

              <div className="mt-4 flex flex-col gap-4 lg:flex-row">
                <div className="flex-1">
                  <DossierTabs activeTab={activeTab} onChange={setActiveTab} />

                  <section
                    role="tabpanel"
                    aria-label={activeTabLabel}
                    className="mt-3"
                  >
                    {activeTab === "visao" && (
                      <>
                        <OverviewSection content={content} />
                        <VisualGallery
                          visuals={content.visuals}
                          onOpenPage={() => setActiveTab("provas")}
                        />
                      </>
                    )}
                    {activeTab === "pedidos" && (
                      <ClaimsSection
                        content={content}
                        openSource={openSource}
                      />
                    )}
                    {activeTab === "fatos" && (
                      <FactsSection content={content} openSource={openSource} />
                    )}
                    {activeTab === "provas" && (
                      <>
                        <EvidenceSection content={content} />
                        <VisualGallery visuals={content.visuals} />
                      </>
                    )}
                    {activeTab === "direito" && (
                      <LegalSection content={content} />
                    )}
                    {activeTab === "teses" && (
                      <ThesesSection content={content} />
                    )}
                    {activeTab === "calculos" && (
                      <CalculationsSection content={content} />
                    )}
                    {activeTab === "acoes" && (
                      <ActionsSection content={content} />
                    )}
                    {activeTab === "revisao" && (
                      <ReviewSection
                        reviewStatus={artifact.review_status}
                        reviewEvents={reviewEvents}
                        reviewReason={reviewReason}
                        setReviewReason={setReviewReason}
                        submitReview={submitReview}
                        reviewNotice={reviewNotice}
                        reanalyze={reanalyze}
                        reanalyzeNotice={reanalyzeNotice}
                      />
                    )}
                  </section>
                </div>

                <SourceViewer source={source} loading={sourceLoading} />
              </div>
            </>
          )}
        </main>
      </Layout>
    </AuthGuard>
  );
}
