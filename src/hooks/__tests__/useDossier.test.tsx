import { act, renderHook, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { useDossier } from "@/hooks/useDossier";

function jsonResponse(body: unknown, status = 200, etag: string | null = null) {
  return {
    ok: status >= 200 && status < 300,
    status,
    headers: {
      get: (name: string) => (name.toLowerCase() === "etag" ? etag : null),
    },
    json: async () => body,
  };
}

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
  window.localStorage.clear();
});

describe("useDossier", () => {
  it("resolve routeId de documento para o último artefato publicado", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        jsonResponse([
          { run_id: "r1", artifact_id: null },
          { run_id: "r2", artifact_id: "art-9" },
        ]),
      )
      .mockResolvedValueOnce(
        jsonResponse({
          id: "art-9",
          run_id: "r2",
          schema_version: "3.0",
          status: "partial",
          content: {},
        }),
      );
    vi.stubGlobal("fetch", fetchMock);
    const { result } = renderHook(() => useDossier({ documentId: "doc-1" }));
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.artifact?.id).toBe("art-9");
    expect(result.current.isLegacy).toBe(false);
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it("schema 2.0 mostra estado legado com ação de reprocessamento", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        jsonResponse({
          id: "art-old",
          run_id: "r1",
          schema_version: "2.0",
          status: "partial",
          content: {},
        }),
      ),
    );
    const { result } = renderHook(() => useDossier({ artifactId: "art-old" }));
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.isLegacy).toBe(true);
    expect(result.current.artifact?.schema_version).toBe("2.0");
  });

  it("routeId=documento com 404 cai para resolução via runs", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        jsonResponse(
          {
            detail: {
              code: "NOT_FOUND",
              user_message: "Análise não encontrada.",
              correlation_id: "c9",
            },
          },
          404,
        ),
      )
      .mockResolvedValueOnce(
        jsonResponse([{ run_id: "r2", artifact_id: "art-9" }]),
      )
      .mockResolvedValueOnce(
        jsonResponse({
          id: "art-9",
          run_id: "r2",
          schema_version: "3.0",
          status: "completed",
          content: {},
        }),
      );
    vi.stubGlobal("fetch", fetchMock);
    const { result } = renderHook(() =>
      useDossier({ artifactId: "doc-1", documentId: "doc-1" }),
    );
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.errorMessage).toBeNull();
    expect(result.current.artifact?.id).toBe("art-9");
  });

  it("routeId=documento sem query param também resolve via runs", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        jsonResponse(
          {
            detail: {
              code: "NOT_FOUND",
              user_message: "Análise não encontrada.",
              correlation_id: "c8",
            },
          },
          404,
        ),
      )
      .mockResolvedValueOnce(
        jsonResponse([{ run_id: "r2", artifact_id: "art-9" }]),
      )
      .mockResolvedValueOnce(
        jsonResponse({
          id: "art-9",
          run_id: "r2",
          schema_version: "3.0",
          status: "completed",
          content: {},
        }),
      );
    vi.stubGlobal("fetch", fetchMock);
    const { result } = renderHook(() => useDossier({ artifactId: "doc-1" }));
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.errorMessage).toBeNull();
    expect(result.current.artifact?.id).toBe("art-9");
  });

  it("ETag 304 preserva conteúdo anterior", async () => {
    const first = {
      id: "art-1",
      run_id: "r1",
      schema_version: "3.0",
      status: "partial",
      content: { claims: [1] },
    };
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse(first, 200, '"etag-1"'))
      .mockResolvedValueOnce({
        ok: false,
        status: 304,
        headers: { get: () => null },
        json: async () => null,
      });
    vi.stubGlobal("fetch", fetchMock);
    const { result } = renderHook(() => useDossier({ artifactId: "art-1" }));
    await waitFor(() => expect(result.current.artifact?.id).toBe("art-1"));
    await act(async () => {
      result.current.reload();
    });
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
    expect(result.current.artifact?.id).toBe("art-1");
  });

  it("erro seguro do backend vira mensagem em português", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        jsonResponse(
          {
            detail: {
              code: "NOT_FOUND",
              user_message: "Análise não encontrada.",
              correlation_id: "c1",
            },
          },
          404,
        ),
      ),
    );
    const { result } = renderHook(() => useDossier({ artifactId: "missing" }));
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.errorMessage).toBe("Análise não encontrada.");
  });

  it("envia Bearer token do localStorage em todas as chamadas", async () => {
    window.localStorage.setItem("access_token", "tok-dossie-1");
    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse({
        id: "art-7",
        run_id: "r7",
        schema_version: "3.0",
        status: "completed",
        content: {},
      }),
    );
    vi.stubGlobal("fetch", fetchMock);
    const { result } = renderHook(() => useDossier({ artifactId: "art-7" }));
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.errorMessage).toBeNull();
    expect(fetchMock).toHaveBeenCalled();
    for (const call of fetchMock.mock.calls) {
      const init = call[1] as { headers?: Record<string, string> } | undefined;
      expect(init?.headers?.Authorization).toBe("Bearer tok-dossie-1");
    }
  });
});
