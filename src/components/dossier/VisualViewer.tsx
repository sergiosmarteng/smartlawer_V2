import { useState } from "react";
import { SafeText } from "./dossier-helpers";
import type { VisualItem } from "./VisualGallery";

/** Visualização ampliada com confirmação para material sensível. */
export function VisualViewer({
  item,
  onClose,
}: {
  item: VisualItem;
  onClose: () => void;
}) {
  const sensitive =
    Array.isArray(item.sensitivity) && item.sensitivity.length > 0;
  const [revealed, setRevealed] = useState(!sensitive);

  return (
    <div
      role="dialog"
      aria-label="Imagem ampliada"
      className="mt-2 rounded border p-3"
    >
      <p className="font-semibold">
        <SafeText value={item.kind} /> · pág.{" "}
        <SafeText value={item.page_number} />
      </p>
      {!revealed ? (
        <>
          <p role="status">Conteúdo sensível oculto por padrão.</p>
          <button
            type="button"
            onClick={() => setRevealed(true)}
            className="mt-1 rounded border px-2 py-1 text-sm"
          >
            Exibir mesmo assim
          </button>
        </>
      ) : (
        <p>
          <SafeText value={item.description} />
        </p>
      )}
      <button
        type="button"
        onClick={onClose}
        className="mt-2 rounded border px-2 py-1 text-sm"
      >
        Fechar
      </button>
    </div>
  );
}
