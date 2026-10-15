import { render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import {
  ChatFormattedText,
  downloadChatAnswerDocx,
} from "@/components/chat/ChatFormattedText";

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("ChatFormattedText", () => {
  it("converte títulos, listas, negrito, itálico e citações sem exibir Markdown cru", () => {
    const raw = [
      "### 1. Tese Principal",
      "",
      "A cláusula é **abusiva** segundo a jurisprudência [1] e o dossiê [A].",
      "",
      "- Violação ao **dever de informação**",
      "- Ausência de *assinatura* específica",
      "",
      "1. Pedir tutela de urgência",
      "2. Juntar contrato original",
    ].join("\n");

    const { container } = render(<ChatFormattedText text={raw} />);

    // Títulos, listas e ênfases estruturados
    expect(
      screen.getByRole("heading", { name: "1. Tese Principal" }),
    ).toBeTruthy();
    expect(container.querySelectorAll("ul li").length).toBe(2);
    expect(container.querySelectorAll("ol li").length).toBe(2);
    expect(container.querySelector("strong")?.textContent).toBe("abusiva");
    expect(container.querySelector("em")?.textContent).toBe("assinatura");

    // Badges de citação presentes
    expect(screen.getByText("[1]")).toBeTruthy();
    expect(screen.getByText("[A]")).toBeTruthy();

    // Nenhum marcador Markdown cru visível
    const visible = container.textContent ?? "";
    expect(visible).not.toContain("###");
    expect(visible).not.toContain("**");
  });

  it("tolera delimitadores incompletos durante streaming sem quebrar", () => {
    const { container } = render(
      <ChatFormattedText text="Analisando **ponto em aberto durante o stream" />,
    );
    expect(container.textContent).toContain(
      "Analisando ponto em aberto durante o stream",
    );
    expect(container.textContent).not.toContain("**");
  });

  it("downloadChatAnswerDocx envia payload e dispara download do arquivo .docx", async () => {
    const postFn = vi.fn().mockResolvedValue({
      data: new Uint8Array([80, 75, 3, 4]),
      headers: {
        "content-disposition": 'attachment; filename="parecer-chat-caso.docx"',
      },
    });
    const createObjectUrl = vi.fn().mockReturnValue("blob:chat-docx");
    const revokeObjectUrl = vi.fn();
    vi.stubGlobal("URL", {
      ...window.URL,
      createObjectURL: createObjectUrl,
      revokeObjectURL: revokeObjectUrl,
    });
    const clickSpy = vi
      .spyOn(HTMLAnchorElement.prototype, "click")
      .mockImplementation(() => {});

    const filename = await downloadChatAnswerDocx(
      {
        question: "Qual a tese?",
        answer: "### Tese\n\nTexto **forte** [1].",
        document_id: "doc-123",
        citations: [
          {
            ref: "[1]",
            chunk_id: "ch-1",
            document_id: "doc-123",
            document_name: "Inicial.pdf",
            page_start: 2,
            excerpt: "Trecho",
          },
        ],
      },
      postFn,
    );

    expect(postFn).toHaveBeenCalledWith(
      "/chat/export-docx",
      expect.objectContaining({
        question: "Qual a tese?",
        document_id: "doc-123",
      }),
      { responseType: "blob" },
    );
    expect(filename).toBe("parecer-chat-caso.docx");
    await waitFor(() => expect(clickSpy).toHaveBeenCalledTimes(1));
    expect(revokeObjectUrl).toHaveBeenCalledWith("blob:chat-docx");
  });
});
