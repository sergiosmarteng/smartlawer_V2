"""V2 T03 — extração com fontes: contrato página/bloco (aceite do plano)."""

import io

from app.core import extraction
from app.core.extraction import (
    assess_page_quality,
    build_coverage,
    build_pages_from_fitz,
    extract_inventory,
    figures_with_state,
    mark_navigation_noise,
    page_needs_ocr,
    text_without_noise,
)
from app.models.document import Document
from app.models.document_figure import DocumentFigure
from app.models.document_revision import DocumentRevision
from app.models.source_block import SourceBlock


def _make_pdf(path, *, pages: list[dict]) -> str:
    """Monta PDF sintético: cada item {header, body, image}."""
    import fitz
    from PIL import Image

    doc = fitz.open()
    for item in pages:
        page = doc.new_page()
        if item.get("header"):
            page.insert_text((72, 40), item["header"])
        if item.get("body"):
            page.insert_text((72, 100), item["body"])
        if item.get("image"):
            img = Image.new("RGB", (400, 500), color=(200, 30, 30))
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            page.insert_image(fitz.Rect(72, 150, 523, 700), stream=buf.getvalue())
    doc.save(path)
    doc.close()
    return path


def test_repeated_header_marked_as_noise_not_summary(tmp_path):
    pdf = _make_pdf(
        str(tmp_path / "noise.pdf"),
        pages=[
            {"header": "Advogados Associados", "body": f"Corpo da pagina {i} com conteudo relevante."}
            for i in range(4)
        ],
    )
    pages = build_pages_from_fitz(pdf, "rev-1")
    assert len(pages) == 4
    mark_navigation_noise(pages)
    flagged = [
        b
        for p in pages
        for b in p["blocks"]
        if extraction.FLAG_NAVIGATION_NOISE in b.get("quality_flags", [])
    ]
    assert len(flagged) >= 4
    clean = text_without_noise(pages)
    assert "Advogados Associados" not in clean
    assert "Corpo da pagina 0" in clean


def test_hybrid_page_detected_by_spatial_coverage(tmp_path):
    pdf = _make_pdf(
        str(tmp_path / "hybrid.pdf"),
        pages=[{"header": "Cabecalho do escritorio", "body": "x" * 200, "image": True}],
    )
    pages = build_pages_from_fitz(pdf, "rev-h")
    assert len(pages) == 1
    page = assess_page_quality(pages[0])
    assert page["image_area_ratio"] > 0.3
    assert extraction.FLAG_HYBRID_PAGE in page["quality_flags"]
    assert page_needs_ocr(page) is True


def test_text_only_long_page_needs_no_ocr(tmp_path):
    pdf = _make_pdf(
        str(tmp_path / "text.pdf"),
        pages=[{"body": "Peticao inicial. " * 100}],
    )
    pages = build_pages_from_fitz(pdf, "rev-t")
    assert page_needs_ocr(pages[0]) is False
    assert pages[0]["quality_flags"] == []


def test_pdf_extractor_ocrs_hybrid_body(monkeypatch, tmp_path):
    import pytesseract

    from app.core.pdf_processor import PDFExtractor

    pdf = _make_pdf(
        str(tmp_path / "hybrid_ocr.pdf"),
        pages=[{"header": "Cabecalho", "body": "y" * 200, "image": True}],
    )
    monkeypatch.setattr(
        pytesseract, "image_to_string", lambda *a, **k: "TEXTO_DO_CORPO_OCR"
    )
    out = PDFExtractor.extract_text(pdf)
    assert "TEXTO_DO_CORPO_OCR" in out


def test_coverage_counts_and_stable_ids(tmp_path):
    pdf = _make_pdf(
        str(tmp_path / "cov.pdf"),
        pages=[{"body": f"Pagina {i}."} for i in range(3)],
    )
    pages, coverage = extract_inventory(pdf, "rev-c")
    assert coverage["pages_total"] == 3
    assert coverage["pages_extracted"] == 3
    assert coverage["blocks_total"] > 0
    ids_first = [b["id"] for p in pages for b in p["blocks"]]
    pages_again, _ = extract_inventory(pdf, "rev-c")
    ids_second = [b["id"] for p in pages_again for b in p["blocks"]]
    assert ids_first == ids_second


def test_inventory_never_raises_on_broken_file(tmp_path):
    broken = tmp_path / "broken.pdf"
    broken.write_bytes(b"nao-e-um-pdf")
    pages, coverage = extract_inventory(str(broken), "rev-b")
    assert pages == []
    assert coverage["extraction_error"]


def test_figures_state_distinguishes_empty_from_failure():
    figs, state = figures_with_state([])
    assert (figs, state) == ([], extraction.FIGURES_OK_EMPTY)
    figs, state = figures_with_state(None, failed=True)
    assert (figs, state) == ([], extraction.FIGURES_FAILED)
    figs, state = figures_with_state([{"page_number": 3}], truncated=True)
    assert state == extraction.FIGURES_TRUNCATED


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


def test_pipeline_persists_revision_blocks_and_links_figures(
    monkeypatch, db_session, make_user, tmp_path
):
    import app.tasks.document_tasks as tasks

    user = make_user()
    pdf = _make_pdf(
        str(tmp_path / "peticao.pdf"),
        pages=[
            {"header": "Advogados", "body": "Fatos do caso.", "image": True},
            {"header": "Advogados", "body": "Pedidos finais."},
        ],
    )
    document = Document(
        user_id=user.id,
        filename="peticao.pdf",
        file_path=pdf,
        content_type="application/pdf",
        status=Document.STATUS_UPLOADED,
    )
    db_session.add(document)
    db_session.commit()
    db_session.refresh(document)

    monkeypatch.setattr(
        tasks.PDFExtractor, "extract_text", staticmethod(lambda file_path: "TEXTO")
    )

    def fake_analyze(self, text, strategy_prompt=None):
        return {"summary": "resumo", "requests": ["p1"]}

    monkeypatch.setattr(
        "app.core.ai_engine.LegalAnalyzer.analyze_petition", fake_analyze
    )
    monkeypatch.setattr(tasks.settings, "DOCLING_ENABLED", False)
    monkeypatch.setattr(
        tasks, "figure_directory", lambda _doc_id: str(tmp_path / "figs" / str(_doc_id))
    )

    _run_pipeline_task(tasks, document.id, pdf)

    db_session.refresh(document)
    assert document.status == Document.STATUS_COMPLETED
    revision = (
        db_session.query(DocumentRevision)
        .filter_by(document_id=document.id)
        .one()
    )
    assert revision.pages_total == 2
    assert revision.extra["coverage"]["pages_total"] == 2
    blocks = (
        db_session.query(SourceBlock).filter_by(revision_id=revision.id).all()
    )
    assert len(blocks) > 0
    assert all(b.text_hash for b in blocks if b.original_text)
    figures = (
        db_session.query(DocumentFigure).filter_by(document_id=document.id).all()
    )
    assert len(figures) == 1
    assert str(figures[0].revision_id) == str(revision.id)
