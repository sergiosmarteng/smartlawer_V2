import { useState } from "react";
import { SafeText, asArray, asText } from "./dossier-helpers";
import { VisualViewer } from "./VisualViewer";

export interface VisualItem {
  id?: unknown;
  page_number?: unknown;
  kind?: unknown;
  description?: unknown;
  sensitivity?: unknown;
}

/** Galeria visual com filtros e ocultação de material sensível (§12.2). */
export function VisualGallery({
  visuals,
  onOpenPage,
}: {
  visuals: unknown;
  onOpenPage?: (pageNumber: number) => void;
}) {
  const items = asArray(visuals) as VisualItem[];
  const [filter, setFilter] = useState("");
  const [enlargedId, setEnlargedId] = useState<string | null>(null);

  const filtered = items.filter((item) => {
    if (!filter) return true;
    return asText(item.kind).toLowerCase().includes(filter.toLowerCase());
  });

  if (!items.length) return null;

  const enlarged = enlargedId
    ? (items.find((item) => asText(item.id) === enlargedId) ?? null)
    : null;

  return (
    <div className="mt-4 rounded border p-3">
      <h2 className="font-semibold">Imagens como evidência</h2>
      <label className="mt-2 block text-sm">
        Filtrar por tipo
        <input
          value={filter}
          onChange={(event) => setFilter(event.target.value)}
          className="ml-2 rounded border px-2 py-1"
          placeholder="photo, diagram…"
        />
      </label>
      <ul className="mt-2 grid grid-cols-2 gap-2">
        {filtered.map((item, index) => {
          const sensitive =
            Array.isArray(item.sensitivity) && item.sensitivity.length > 0;
          return (
            <li
              key={asText(item.id ?? index)}
              className="rounded border p-2 text-sm"
            >
              <p>
                <SafeText value={item.kind} /> · pág.{" "}
                <SafeText value={item.page_number} />
              </p>
              {sensitive ? (
                <p role="status">
                  Conteúdo sensível oculto — confirme para exibir.
                </p>
              ) : (
                <p>
                  <SafeText value={item.description} />
                </p>
              )}
              <div className="mt-1 flex gap-2">
                <button
                  type="button"
                  onClick={() => setEnlargedId(asText(item.id))}
                  className="rounded border px-2 py-1 text-sm"
                >
                  Ampliar
                </button>
                {typeof item.page_number === "number" && onOpenPage && (
                  <button
                    type="button"
                    onClick={() => onOpenPage(item.page_number as number)}
                    className="rounded border px-2 py-1 text-sm"
                  >
                    Ver na página original
                  </button>
                )}
              </div>
            </li>
          );
        })}
      </ul>
      {enlarged && (
        <VisualViewer item={enlarged} onClose={() => setEnlargedId(null)} />
      )}
    </div>
  );
}
