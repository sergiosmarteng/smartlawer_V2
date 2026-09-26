"""V2 T05 — planejamento por cobertura (aceite do plano)."""

import pytest

from app.core.coverage_planner import (
    BudgetExceededError,
    build_prompt_window,
    check_budget,
    plan_batches,
)
from app.models.document import Document
from app.models.document_revision import DocumentRevision


def _blocks(n, prefix="bloco"):
    return [
        {"id": f"b{i:03d}", "normalized_text": f"{prefix} {i} com conteudo."}
        for i in range(n)
    ]


def test_plan_assigns_every_block_without_gaps():
    blocks = _blocks(50)
    plan = plan_batches(blocks, max_batch_tokens=200, overlap_blocks=2)
    seen = [bid for batch in plan["batches"] for bid in batch["block_ids"]]
    assert set(seen) == {b["id"] for b in blocks}
    # Ordem preservada; overlap referencia IDs para deduplicação.
    first_ids = [b["block_ids"][0] for b in plan["batches"]]
    assert first_ids[0] == "b000"
    assert plan["unprocessed_block_ids"] == []
    assert plan["blocks_total"] == 50


def test_oversized_block_gets_own_batch():
    blocks = [{"id": "giant", "normalized_text": "x" * 20000}]
    plan = plan_batches(blocks, max_batch_tokens=100, overlap_blocks=1)
    assert plan["batches_total"] == 1
    assert plan["batches"][0]["block_ids"] == ["giant"]


def test_budget_exceeded_lists_unprocessed_blocks():
    blocks = _blocks(30)
    plan = plan_batches(blocks, max_batch_tokens=100, overlap_blocks=0)
    assert plan["batches_total"] > 2
    with pytest.raises(BudgetExceededError) as excinfo:
        check_budget(plan, max_batches=2)
    assert excinfo.value.code == "BUDGET_EXCEEDED"
    assert excinfo.value.unprocessed_block_ids
    # Dentro do teto passa intacto.
    assert check_budget(plan, max_batches=plan["batches_total"]) is plan


def test_short_text_window_is_identical():
    text = "Peticao curta."
    window, coverage = build_prompt_window(text, budget_tokens=1000)
    assert window == text
    assert coverage["truncated"] is False
    assert coverage["tail_included"] is True


def test_long_window_preserves_final_requests():
    head = "INICIO " * 5000
    tail = "ROL FINAL DE PEDIDOS: item 13, pagina 35."
    text = head + "\n\n" + tail
    window, coverage = build_prompt_window(text, budget_tokens=2000)
    assert coverage["truncated"] is True
    assert coverage["omitted_chars"] > 0
    assert coverage["tail_included"] is True
    assert tail in window
    assert "orçamento" in window or "orcamento" in window


def _run_pipeline_task(tasks, document_id: str, pdf_path: str) -> None:
    target = getattr(tasks.process_pdf_task, "func", None)
    if target is not None:

        class _FakeTask:
            max_retries = 3

            def __init__(self):
                self.request = type("Req", (), {"retries": 0})()

            def retry(self, exc=None, countdown=None):
                raise RuntimeError("retry")

        target(_FakeTask(), str(document_id), pdf_path)
    else:
        tasks.process_pdf_task.run(str(document_id), pdf_path)


def test_pipeline_windows_long_text_and_records_coverage(
    monkeypatch, db_session, make_user, tmp_path
):
    import app.tasks.document_tasks as tasks

    user = make_user()
    pdf_path = tmp_path / "longa.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 stub")
    document = Document(
        user_id=user.id,
        filename="longa.pdf",
        file_path=str(pdf_path),
        content_type="application/pdf",
        status=Document.STATUS_UPLOADED,
    )
    db_session.add(document)
    db_session.commit()
    db_session.refresh(document)

    tail = "PEDIDO FINAL PAGINA 35"
    long_text = ("corpo " * 20000) + "\n\n" + tail
    monkeypatch.setattr(tasks.settings, "PROMPT_BUDGET_TOKENS", 2000)
    monkeypatch.setattr(
        tasks.PDFExtractor, "extract_text", staticmethod(lambda file_path: long_text)
    )
    monkeypatch.setattr(tasks, "extract_inventory", lambda fp, rev: ([], {}))
    monkeypatch.setattr(tasks.settings, "DOCLING_ENABLED", False)
    monkeypatch.setattr(tasks, "docling_extract_figures", lambda fp, out: [])
    monkeypatch.setattr(tasks, "_extract_figures_fitz", lambda fp, out: [])

    captured = {}

    def fake_analyze(self, text, strategy_prompt=None):
        captured["analysis_input"] = text
        return {"summary": "resumo"}

    monkeypatch.setattr(
        "app.core.ai_engine.LegalAnalyzer.analyze_petition", fake_analyze
    )

    _run_pipeline_task(tasks, document.id, str(pdf_path))

    assert tail in captured["analysis_input"]
    assert len(captured["analysis_input"]) < len(long_text)
    db_session.refresh(document)
    assert document.status == Document.STATUS_COMPLETED
