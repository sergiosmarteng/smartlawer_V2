import { renderHook, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { useAnalysisRun } from "@/hooks/useAnalysisRun";

function jsonResponse(body: unknown, status = 200) {
  return {
    ok: status >= 200 && status < 300,
    status,
    headers: { get: () => null },
    json: async () => body,
  };
}

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
  window.localStorage.clear();
});

describe("useAnalysisRun", () => {
  it("polling para em estado terminal", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse({
        run_id: "r1",
        status: "completed",
        stage: "publication",
        progress: 100,
        version: 2,
        stages: [],
      }),
    );
    vi.stubGlobal("fetch", fetchMock);
    const { result } = renderHook(() => useAnalysisRun("r1"));
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.run?.status).toBe("completed");
    const calls = fetchMock.mock.calls.length;
    await new Promise((resolve) => setTimeout(resolve, 50));
    expect(fetchMock.mock.calls.length).toBe(calls);
  });

  it("progresso de extração não aparece como 100%", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        jsonResponse({
          run_id: "r2",
          status: "running",
          stage: "extraction",
          progress: 100,
          version: 1,
          stages: [],
        }),
      ),
    );
    const { result } = renderHook(() => useAnalysisRun("r2"));
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.progress).toBeLessThan(100);
  });

  it("erro seguro vira mensagem em português sem detalhe técnico", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        jsonResponse(
          {
            detail: {
              code: "PROVIDER_UNAVAILABLE",
              user_message: "Provedor indisponível. Tente de novo.",
              correlation_id: "c9",
            },
          },
          500,
        ),
      ),
    );
    const { result } = renderHook(() => useAnalysisRun("r3"));
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.errorMessage).toBe(
      "Provedor indisponível. Tente de novo.",
    );
  });

  it("envia Bearer token do localStorage no polling", async () => {
    window.localStorage.setItem("access_token", "tok-run-1");
    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse({
        run_id: "r9",
        status: "completed",
        stage: "publication",
        progress: 100,
        version: 2,
        stages: [],
      }),
    );
    vi.stubGlobal("fetch", fetchMock);
    const { result } = renderHook(() => useAnalysisRun("r9"));
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(fetchMock).toHaveBeenCalled();
    const init = fetchMock.mock.calls[0][1] as
      { headers?: Record<string, string> } | undefined;
    expect(init?.headers?.Authorization).toBe("Bearer tok-run-1");
  });
});
