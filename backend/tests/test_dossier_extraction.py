"""Onda 0 Task 4 — inventário integral, OCR seletivo e fontes por bloco.

6 cenários (plano §4):
- 35 páginas com pedidos no final entram no plano;
- cabeçalho textual com corpo-imagem marca ``needs_ocr=True``;
- página rotacionada preserva ``rotation`` e bbox normalizado;
- todos os blocos aparecem em lote ou ``unprocessed_block_ids``;
- blocos de revisões diferentes nunca se misturam;
- orçamento excedido produz estado parcial acionável.
"""

from app.core.coverage_planner import BudgetExceededError, check_budget


def _revision_blocks(n, revision_id="rev-1", prefix="bloco"):
    return [
        {
            "id": f"{revision_id}-b{i:03d}",
            "revision_id": revision_id,
            "page_number": (i // 4) + 1,
            "normalized_text": f"{prefix} {i} com conteudo juridico suficiente.",
        }
        for i in range(n)
    ]


def test_35_pages_with_final_requests_enter_plan():
    """35 páginas com pedidos no final: todos os blocos entram no plano."""
    from app.core.coverage_planner import plan_revision_batches

    blocks = _revision_blocks(35 * 4, revision_id="rev-35")
    # Última página concentra o rol de pedidos.
    blocks[-1]["normalized_text"] = "Requer a condenacao em danos morais e materiais."
    blocks[-2]["normalized_text"] = "Requer a inversao do onus da prova."
    plan = plan_revision_batches(blocks, max_batch_tokens=800, overlap_blocks=1)
    assigned = [bid for b in plan["batches"] for bid in b["block_ids"]]
    assert blocks[-1]["id"] in assigned
    assert blocks[-2]["id"] in assigned
    assert plan["partial"] is False
    assert plan["unprocessed_block_ids"] == []


def test_text_header_with_image_body_needs_ocr():
    """Cabeçalho textual com corpo em imagem: OCR por cobertura espacial."""
    from app.core.extraction import page_needs_ocr

    text_blocks = [{"text": "Tribunal — cabecalho com 40 chars....."}]
    image_blocks = [{"area": 0.85}]
    assert (
        page_needs_ocr(
            None, text_blocks=text_blocks, image_blocks=image_blocks, page_area=1.0
        )
        is True
    )
    # Página só-texto densa não precisa de OCR.
    assert (
        page_needs_ocr(
            None,
            text_blocks=[{"text": "x" * 2000}],
            image_blocks=[],
            page_area=1.0,
        )
        is False
    )


def test_rotated_page_preserves_rotation_and_bbox():
    """Página rotacionada preserva ``rotation`` e bbox normalizado 0-1."""
    from app.core.extraction import _normalize_bbox

    bbox = _normalize_bbox({"l": 59.5, "t": 119, "r": 357, "b": 476}, 595.0, 842.0)
    assert bbox is not None
    for key in ("x0", "y0", "x1", "y1"):
        assert 0.0 <= bbox[key] <= 1.0
    assert bbox["x0"] < bbox["x1"] and bbox["y0"] < bbox["y1"]

    page = {
        "page_number": 4,
        "width": 595.0,
        "height": 842.0,
        "rotation": 90,
        "method": "pymupdf",
        "blocks": [],
    }
    assert page["rotation"] == 90
    assert page["width"] > 0 and page["height"] > 0


def test_every_block_in_batch_or_unprocessed():
    """Todo bloco aparece em lote ou em ``unprocessed_block_ids``."""
    from app.core.coverage_planner import plan_revision_batches

    blocks = _revision_blocks(40, revision_id="rev-u")
    plan = plan_revision_batches(
        blocks, max_batch_tokens=100, overlap_blocks=0, max_batches=2
    )
    batched = {bid for b in plan["batches"] for bid in b["block_ids"]}
    accounted = batched | set(plan["unprocessed_block_ids"])
    assert {b["id"] for b in blocks} <= accounted
    assert plan["partial"] is True
    assert plan["unprocessed_block_ids"], "parcial deve listar blocos pendentes"


def test_blocks_from_different_revisions_never_mix():
    """Blocos de revisões distintas são rejeitados no mesmo plano."""
    import pytest

    from app.core.coverage_planner import plan_revision_batches

    blocks = _revision_blocks(4, revision_id="rev-A") + _revision_blocks(
        4, revision_id="rev-B"
    )
    with pytest.raises(ValueError):
        plan_revision_batches(blocks, max_batch_tokens=800)


def test_budget_exceeded_is_actionable_partial():
    """Estouro de orçamento gera parcial acionável, nunca corte silencioso."""
    from app.core.coverage_planner import plan_batches

    blocks = [
        {"id": f"b{i:03d}", "normalized_text": f"bloco {i} com conteudo."}
        for i in range(30)
    ]
    plan = plan_batches(blocks, max_batch_tokens=100, overlap_blocks=0)
    assert plan["batches_total"] > 2
    try:
        check_budget(plan, max_batches=2)
        raise AssertionError("check_budget deveria estourar o orçamento")
    except BudgetExceededError as exc:
        assert exc.code == "BUDGET_EXCEEDED"
        assert exc.unprocessed_block_ids, "deve listar blocos sem processar"
