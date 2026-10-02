import { SafeText, SectionStateLike } from "./dossier-helpers";

/** Faixa de estado da seção: status + motivo + pendências (§6.4). */
export function SectionStateBanner({
  state,
}: {
  state: SectionStateLike | null;
}) {
  if (!state) return null;
  if (state.status === "complete") return null;
  return (
    <p role="status" className="rounded border p-2 text-sm">
      Seção {state.status}: <SafeText value={state.reason ?? ""} />
      {(state.pending_actions ?? []).length > 0 && (
        <> — pendências: {(state.pending_actions ?? []).join("; ")}</>
      )}
    </p>
  );
}
