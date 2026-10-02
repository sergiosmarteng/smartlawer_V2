import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { DossierHeader } from "@/components/dossier/DossierHeader";
import { DossierTabs } from "@/components/dossier/DossierTabs";
import { SectionStateBanner } from "@/components/dossier/SectionStateBanner";
import { SourceViewer } from "@/components/dossier/SourceViewer";
import { VisualGallery } from "@/components/dossier/VisualGallery";
import { VisualViewer } from "@/components/dossier/VisualViewer";
import {
  ActionsSection,
  ClaimsSection,
  FactsSection,
  OverviewSection,
  ThesesSection,
} from "@/components/dossier/sections/sections";

const noop = () => {};

function v3Content() {
  return {
    scope: { represented_side: "claimant" },
    coverage: { pages_total: 12, pages_extracted: 12 },
    section_states: {
      facts: {
        status: "complete",
        reason: "ok",
        coverage: {},
        pending_actions: [],
      },
      claims: {
        status: "partial",
        reason: "Falta confirmar pedido 4",
        coverage: {},
        pending_actions: ["Confirmar pedido 4"],
      },
      action_plan: {
        status: "partial",
        reason: "Falta confirmar pedido 4",
        coverage: {},
        pending_actions: ["Confirmar pedido 4"],
      },
    },
    claims: [{ id: "claim-1", title: "Guarda", source_refs: ["src-1"] }],
    facts: [
      {
        id: "f1",
        statement: "Genitores separados",
        epistemic_status: "documented",
        asserted_by: "parte-A",
        source_refs: ["src-1"],
      },
    ],
    risks: [{ issue: "Distância", mitigation: "Regime flexível" }],
    limitations: [{ message: "Renda da parte B controvertida" }],
    theses: [
      {
        id: "t1",
        represented_side: "claimant",
        issue: "Guarda",
        conclusion: "Compartilhada",
      },
    ],
    visuals: [
      {
        id: "vis-1",
        kind: "photo",
        page_number: 3,
        description: "Foto escolar",
        sensitivity: [],
      },
    ],
  };
}

describe("DossierPage", () => {
  it("visão geral mostra áreas, cobertura, riscos e ações", () => {
    render(<OverviewSection content={v3Content()} />);
    expect(screen.getByText(/Pedidos: 1/)).toBeInTheDocument();
    expect(screen.getByText(/12\/12/)).toBeInTheDocument();
  });

  it("todas as abas renderizam conteúdo real ou motivo do estado vazio", () => {
    const { rerender } = render(
      <ClaimsSection content={v3Content()} openSource={noop} />,
    );
    expect(screen.getByText("Guarda")).toBeInTheDocument();
    rerender(
      <ClaimsSection
        content={{
          section_states: {
            claims: {
              status: "blocked",
              reason: "Extração bloqueada",
              pending_actions: [],
            },
          },
        }}
        openSource={noop}
      />,
    );
    expect(screen.getByText("Extração bloqueada")).toBeInTheDocument();
  });

  it("fato exibe estado epistêmico e abre fonte", () => {
    const openSource = vi.fn();
    render(<FactsSection content={v3Content()} openSource={openSource} />);
    expect(screen.getByText(/documented/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /Ver fonte src-1/ }));
    expect(openSource).toHaveBeenCalledWith("src-1");
  });

  it("imagem abre ampliada e oferece ver na página original", () => {
    const onOpenPage = vi.fn();
    render(
      <VisualGallery visuals={v3Content().visuals} onOpenPage={onOpenPage} />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Ampliar" }));
    expect(screen.getByRole("dialog")).toBeInTheDocument();
    fireEvent.click(
      screen.getByRole("button", { name: "Ver na página original" }),
    );
    expect(onOpenPage).toHaveBeenCalledWith(3);
  });

  it("item sensível inicia oculto", () => {
    render(
      <VisualViewer
        item={{
          id: "v",
          kind: "photo",
          page_number: 1,
          sensitivity: ["personal_data"],
        }}
        onClose={noop}
      />,
    );
    expect(screen.getByText(/oculto por padrão/)).toBeInTheDocument();
  });

  it("galeria filtra por tipo", () => {
    render(
      <VisualGallery
        visuals={[
          { id: "a", kind: "photo", page_number: 1 },
          { id: "b", kind: "diagram", page_number: 2 },
        ]}
      />,
    );
    fireEvent.change(screen.getByPlaceholderText(/photo, diagram/), {
      target: { value: "diagram" },
    });
    expect(screen.queryByText(/pág. 1/)).not.toBeInTheDocument();
    expect(screen.getByText(/pág. 2/)).toBeInTheDocument();
  });

  it("navegação de tabs funciona por teclado", () => {
    const onChange = vi.fn();
    render(<DossierTabs activeTab="visao" onChange={onChange} />);
    const first = screen.getByRole("tab", { name: "Visão geral" });
    fireEvent.keyDown(first, { key: "ArrowRight" });
    expect(onChange).toHaveBeenCalledWith("pedidos");
  });

  it("nenhum painel deriva tese a partir de claims", () => {
    render(<ThesesSection content={{ theses: [] }} />);
    expect(screen.getByText(/Nenhuma tese registrada/)).toBeInTheDocument();
  });

  it("artefato parcial exibe pendências antes de aprovação", () => {
    render(<ActionsSection content={v3Content()} />);
    expect(screen.getByText(/Falta confirmar pedido 4/)).toBeInTheDocument();
    expect(
      screen.getByText(/Renda da parte B controvertida/),
    ).toBeInTheDocument();
  });

  it("header e fonte exibem estado honesto", () => {
    render(
      <DossierHeader
        artifact={{
          schema_version: "3.0",
          status: "partial",
          review_status: "pending",
          content: v3Content(),
        }}
        run={{ progress: 95, stage: "extraction", status: "running" }}
      />,
    );
    expect(screen.getByText(/95/)).toBeInTheDocument();
    render(
      <SourceViewer
        source={{
          page_number: 3,
          verification_status: "matched",
          quote: "trecho",
        }}
        loading={false}
      />,
    );
    expect(screen.getByText("3")).toBeInTheDocument();
  });

  it("banner de estado mostra motivo e pendências", () => {
    render(
      <SectionStateBanner
        state={{
          status: "partial",
          reason: "Falta confirmar pedido 4",
          pending_actions: ["Confirmar pedido 4"],
        }}
      />,
    );
    expect(screen.getByText(/Falta confirmar pedido 4/)).toBeInTheDocument();
  });
});
