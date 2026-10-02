/** Helpers compartilhados dos componentes do dossiê (Onda 0 Task 14). */

export function asArray(value: unknown): Array<Record<string, unknown>> {
  return Array.isArray(value) ? (value as Array<Record<string, unknown>>) : [];
}

export function asText(value: unknown): string {
  if (typeof value === "string") return value;
  if (value == null) return "";
  return String(value);
}

/** Texto puro (React escapa por padrão: sem HTML/script executável). */
export function SafeText({ value }: { value: unknown }) {
  return <>{asText(value)}</>;
}

export function EmptyState({ text }: { text: string }) {
  return <p className="rounded border p-3 text-sm">{text}</p>;
}

export interface SectionStateLike {
  status?: string;
  reason?: string;
  pending_actions?: string[];
}

export function sectionStateOf(
  content: Record<string, unknown>,
  section: string,
): SectionStateLike | null {
  const states = content.section_states as
    Record<string, SectionStateLike> | undefined;
  return states?.[section] ?? null;
}
