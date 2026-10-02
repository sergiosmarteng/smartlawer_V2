import { useCallback, useRef } from "react";

export const DOSSIER_TABS = [
  { id: "visao", label: "Visão geral" },
  { id: "pedidos", label: "Pedidos" },
  { id: "fatos", label: "Fatos" },
  { id: "provas", label: "Provas" },
  { id: "direito", label: "Direito" },
  { id: "teses", label: "Teses" },
  { id: "calculos", label: "Cálculos" },
  { id: "acoes", label: "Ações" },
  { id: "revisao", label: "Revisão" },
] as const;

export type DossierTabId = (typeof DOSSIER_TABS)[number]["id"];

export function DossierTabs({
  activeTab,
  onChange,
}: {
  activeTab: DossierTabId;
  onChange: (tab: DossierTabId) => void;
}) {
  const tabRefs = useRef<Array<HTMLButtonElement | null>>([]);

  const onKeyDown = useCallback(
    (event: React.KeyboardEvent, index: number) => {
      let next = index;
      if (event.key === "ArrowRight") next = (index + 1) % DOSSIER_TABS.length;
      else if (event.key === "ArrowLeft")
        next = (index - 1 + DOSSIER_TABS.length) % DOSSIER_TABS.length;
      else if (event.key === "Home") next = 0;
      else if (event.key === "End") next = DOSSIER_TABS.length - 1;
      else return;
      event.preventDefault();
      onChange(DOSSIER_TABS[next].id);
      tabRefs.current[next]?.focus();
    },
    [onChange],
  );

  return (
    <div
      role="tablist"
      aria-label="Seções do dossiê"
      className="flex flex-wrap gap-1"
    >
      {DOSSIER_TABS.map((tab, index) => (
        <button
          key={tab.id}
          ref={(el) => {
            tabRefs.current[index] = el;
          }}
          role="tab"
          aria-selected={activeTab === tab.id}
          tabIndex={activeTab === tab.id ? 0 : -1}
          onClick={() => onChange(tab.id)}
          onKeyDown={(event) => onKeyDown(event, index)}
          className="rounded border px-3 py-1 text-sm"
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}
