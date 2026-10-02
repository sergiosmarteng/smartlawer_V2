import { SafeText } from "../dossier-helpers";

export interface ReviewEventLike {
  id?: string;
  target?: string;
  reason?: string | null;
}

/** Revisão humana versionada com aprovação e comparação (Onda 0 Task 15). */
export function ReviewSection({
  reviewStatus,
  reviewEvents,
  reviewReason,
  setReviewReason,
  submitReview,
  reviewNotice,
  reanalyze,
  reanalyzeNotice,
  onApprove,
  approvalNotice,
}: {
  reviewStatus: unknown;
  reviewEvents: ReviewEventLike[];
  reviewReason: string;
  setReviewReason: (value: string) => void;
  submitReview: () => void;
  reviewNotice: string;
  reanalyze: () => void;
  reanalyzeNotice: string;
  onApprove?: () => void;
  approvalNotice?: string;
}) {
  return (
    <div className="space-y-3">
      <p className="text-sm">
        Revisão: <SafeText value={reviewStatus} /> (sem selo sem aprovação de
        usuário habilitado)
      </p>
      <ul className="space-y-1 text-sm">
        {reviewEvents.map((event, index) => (
          <li key={String(event.id ?? index)} className="rounded border p-2">
            <SafeText value={event.target} /> —{" "}
            <SafeText value={event.reason} />
          </li>
        ))}
      </ul>
      <label className="block text-sm">
        Registrar correção
        <textarea
          value={reviewReason}
          onChange={(event) => setReviewReason(event.target.value)}
          className="mt-1 block w-full rounded border p-2"
          rows={3}
        />
      </label>
      <div className="flex gap-2">
        <button
          type="button"
          onClick={submitReview}
          className="rounded border px-3 py-1"
        >
          Enviar correção
        </button>
        <button
          type="button"
          onClick={reanalyze}
          className="rounded border px-3 py-1"
        >
          Reanalisar (nova execução)
        </button>
        {onApprove && (
          <button
            type="button"
            onClick={onApprove}
            className="rounded border px-3 py-1"
          >
            Aprovar revisão
          </button>
        )}
      </div>
      {reviewNotice && <p role="status">{reviewNotice}</p>}
      {reanalyzeNotice && <p role="status">{reanalyzeNotice}</p>}
      {approvalNotice && <p role="status">{approvalNotice}</p>}
    </div>
  );
}
