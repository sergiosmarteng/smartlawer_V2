import {
  EmptyState,
  SafeText,
  asArray,
  asText,
  sectionStateOf,
} from "../dossier-helpers";
import { SectionStateBanner } from "../SectionStateBanner";
import { SourceButton } from "../SourceViewer";

export interface SectionProps {
  content: Record<string, unknown>;
  openSource: (id: string) => void;
}

/** Visão geral composta do artefato (sem segunda interpretação livre). */
export function OverviewSection({
  content,
}: {
  content: Record<string, unknown>;
}) {
  const coverage = (content.coverage || {}) as Record<string, unknown>;
  const limitations = asArray(content.limitations);
  return (
    <div className="space-y-2">
      <SectionStateBanner
        state={sectionStateOf(content, "executive_summary")}
      />
      <p>
        Pedidos: {asArray(content.claims).length} · páginas{" "}
        {asText(coverage.pages_extracted ?? 0)}/
        {asText(coverage.pages_total ?? 0)}
      </p>
      <ModuleActivationsLine activations={content.module_activations} />
      {limitations.map((lim, i) => (
        <p key={i} className="text-sm">
          ⚠ <SafeText value={lim.message} />
        </p>
      ))}
    </div>
  );
}

/** Especializações ativas e limitações declaradas (Onda 1, spec §13.5). */
export function ModuleActivationsLine({
  activations,
}: {
  activations: unknown;
}) {
  const items = asArray(activations);
  if (!items.length) return null;
  return (
    <p className="text-sm">
      Módulos:{" "}
      {items.map((activation, i) => (
        <span key={asText(activation.module_id ?? i)}>
          {i > 0 ? " · " : ""}
          <SafeText value={activation.module_id} /> (
          <SafeText value={activation.status} />
          {asText(activation.reason)
            ? [" — ", <SafeText key="r" value={activation.reason} />]
            : null}
          )
        </span>
      ))}
    </p>
  );
}

export function ClaimsSection({ content, openSource }: SectionProps) {
  const claims = asArray(content.claims);
  if (!claims.length) {
    const state = sectionStateOf(content, "claims");
    return <EmptyState text={state?.reason ?? "Nenhum pedido registrado."} />;
  }
  return (
    <ul className="space-y-3">
      {claims.map((claim, i) => (
        <li key={asText(claim.id || i)} className="rounded border p-3">
          <p className="font-semibold">
            {asText(claim.original_number)
              ? `#${asText(claim.original_number)} — `
              : ""}
            <SafeText value={claim.title} />
          </p>
          {asText(claim.requested_relief) ? (
            <p className="text-sm">
              <SafeText value={claim.requested_relief} />
            </p>
          ) : null}
          <p className="text-sm">
            refs:{" "}
            {asArray(claim.source_refs).map((ref) => (
              <SourceButton
                key={asText(ref)}
                id={asText(ref)}
                openSource={openSource}
              />
            ))}
            {!asArray(claim.source_refs).length && "a confirmar"}
          </p>
        </li>
      ))}
    </ul>
  );
}

export function FactsSection({ content, openSource }: SectionProps) {
  const facts = asArray(content.facts);
  if (!facts.length) {
    const state = sectionStateOf(content, "facts");
    return <EmptyState text={state?.reason ?? "Nenhum fato registrado."} />;
  }
  return (
    <ul className="space-y-2">
      {facts.map((fact, i) => (
        <li key={i} className="rounded border p-3 text-sm">
          <p>
            <SafeText value={fact.statement} /> [{asText(fact.epistemic_status)}
            ]
          </p>
          <p>
            afirmado por: <SafeText value={fact.asserted_by} />
            {asArray(fact.source_refs).map((ref) => (
              <SourceButton
                key={asText(ref)}
                id={asText(ref)}
                openSource={openSource}
              />
            ))}
          </p>
        </li>
      ))}
    </ul>
  );
}

export function EvidenceSection({
  content,
}: {
  content: Record<string, unknown>;
}) {
  const evidence = asArray(content.evidence);
  if (!evidence.length) {
    const state = sectionStateOf(content, "evidence");
    return <EmptyState text={state?.reason ?? "Nenhuma prova registrada."} />;
  }
  return (
    <ul className="space-y-2">
      {evidence.map((item, i) => (
        <li key={asText(item.id || i)} className="rounded border p-3 text-sm">
          <p className="font-semibold">
            <SafeText value={item.kind} /> —{" "}
            <SafeText value={item.presence_status} />
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

export function LegalSection({
  content,
}: {
  content: Record<string, unknown>;
}) {
  const refs = asArray(content.legal_references);
  if (!refs.length) {
    const state = sectionStateOf(content, "legal_references");
    return (
      <EmptyState text={state?.reason ?? "Nenhum fundamento registrado."} />
    );
  }
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

export function ThesesSection({
  content,
}: {
  content: Record<string, unknown>;
}) {
  // Proibido derivar tese a partir de pedidos: renderiza só teses publicadas.
  const theses = asArray(content.theses);
  if (!theses.length) {
    const state = sectionStateOf(content, "theses");
    return <EmptyState text={state?.reason ?? "Nenhuma tese registrada."} />;
  }
  return (
    <ul className="space-y-2">
      {theses.map((thesis, i) => (
        <li key={asText(thesis.id || i)} className="rounded border p-3 text-sm">
          <p className="font-semibold">
            [{asText(thesis.represented_side)}]{" "}
            <SafeText value={thesis.issue} />
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

export function CalculationsSection({
  content,
}: {
  content: Record<string, unknown>;
}) {
  const calculations = asArray(content.calculations);
  if (!calculations.length) {
    const state = sectionStateOf(content, "calculations");
    return <EmptyState text={state?.reason ?? "Nenhum cálculo registrado."} />;
  }
  return (
    <ul className="space-y-2">
      {calculations.map((calc, i) => (
        <li key={asText(calc.id || i)} className="rounded border p-3 text-sm">
          <p className="font-semibold">
            <SafeText value={calc.formula} /> v
            <SafeText value={calc.formula_version} /> ={" "}
            <SafeText value={calc.result} />
          </p>
        </li>
      ))}
    </ul>
  );
}

export function ActionsSection({
  content,
}: {
  content: Record<string, unknown>;
}) {
  const risks = asArray(content.risks);
  const limitations = asArray(content.limitations);
  const state = sectionStateOf(content, "action_plan");
  return (
    <div className="space-y-2">
      <SectionStateBanner state={state} />
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
        <EmptyState text={state?.reason ?? "Nenhuma ação pendente."} />
      )}
    </div>
  );
}
