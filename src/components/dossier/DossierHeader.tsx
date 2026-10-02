import { SafeText, asText } from "./dossier-helpers";

export interface DossierHeaderProps {
  artifact: {
    schema_version?: string;
    status?: string;
    review_status?: string;
    content?: Record<string, unknown>;
  };
  run?: { progress?: number; stage?: string | null; status?: string } | null;
}

/** Cabeçalho do dossiê: caso, cobertura honesta, estado e revisão (§6.2). */
export function DossierHeader({ artifact, run }: DossierHeaderProps) {
  const content = (artifact.content || {}) as Record<string, unknown>;
  const scope = (content.scope || {}) as Record<string, unknown>;
  const coverage = (content.coverage || {}) as Record<string, unknown>;
  return (
    <div className="mt-3 rounded border p-4">
      <p className="text-sm">
        polo: <SafeText value={scope.represented_side ?? "neutral"} /> · versão{" "}
        <SafeText value={artifact.schema_version} /> · estado{" "}
        <SafeText value={artifact.status} /> · revisão{" "}
        <SafeText value={artifact.review_status} />
      </p>
      <p className="text-sm">
        páginas: <SafeText value={asText(coverage.pages_extracted ?? 0)} />/
        <SafeText value={asText(coverage.pages_total ?? 0)} />
        {run && (
          <>
            {" "}
            · andamento: <SafeText value={run.progress} />% (
            <SafeText value={run.stage ?? run.status} />)
          </>
        )}
      </p>
    </div>
  );
}
