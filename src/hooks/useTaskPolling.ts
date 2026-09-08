import { useEffect, useRef } from 'react';

/**
 * Polling scheduler for the workflow status loop (B5 frontend hygiene).
 *
 * Owns the `setTimeout` chain behind `GET /tasks/{id}` polling so pages
 * don't hand-roll timeout refs: schedules callbacks, cancels pending
 * work on demand, and always cleans up on unmount (no setState-after-
 * unmount from a stray poll tick). Reusable for future batch polling
 * (BL-021) — the status state machine itself stays in the page.
 */
export function useTaskPolling() {
  const timeoutRef = useRef<number | null>(null);

  const cancelPoll = () => {
    if (timeoutRef.current !== null) {
      window.clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
  };

  const schedulePoll = (callback: () => void, delay = 1800) => {
    cancelPoll();
    timeoutRef.current = window.setTimeout(callback, delay);
  };

  useEffect(() => {
    return () => {
      cancelPoll();
    };
  }, []);

  return { schedulePoll, cancelPoll };
}
