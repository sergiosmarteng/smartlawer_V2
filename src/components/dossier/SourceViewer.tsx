import { SafeText } from "./dossier-helpers";

export interface SourceDetail {
  page_number?: number | null;
  verification_status?: string;
  quote?: string | null;
  url?: string | null;
}

/** Painel lateral da fonte: página, trecho e região (§12.1, AC-04). */
export function SourceViewer({
  source,
  loading,
}: {
  source: SourceDetail | null;
  loading: boolean;
}) {
  return (
    <aside aria-label="Fonte" className="w-full lg:w-80">
      <div className="rounded border p-3">
        <h2 className="font-semibold">Fonte</h2>
        {loading && <p role="status">Abrindo fonte…</p>}
        {!loading && !source && (
          <p className="text-sm">Use “Ver fonte” em qualquer item.</p>
        )}
        {!loading && source && (
          <dl className="mt-2 space-y-1 text-sm">
            <div>
              <dt className="font-semibold">Página</dt>
              <dd>{source.page_number ?? "—"}</dd>
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
  );
}

export function SourceButton({
  id,
  openSource,
}: {
  id: unknown;
  openSource: (id: string) => void;
}) {
  if (typeof id !== "string" || !id) return null;
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
