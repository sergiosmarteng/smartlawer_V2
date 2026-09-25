"""Figuras da petição: pipeline + API (Goal figuras a/b/c/d)."""

import io

from app.models.analysis import Analysis
from app.models.document import Document


def _run_pipeline_task(tasks, document_id: str, pdf_path: str) -> None:
    # Compatível com os dois ambientes: stub de celery do conftest
    # (expõe ``.func``) e celery real (task bound, chama ``.run``).
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


def _make_pdf_with_image(path, with_image: bool) -> str:
    import fitz
    from PIL import Image

    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Petição inicial — fatos e pedidos.")
    if with_image:
        img = Image.new("RGB", (80, 60), color=(200, 30, 30))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        page.insert_image(
            fitz.Rect(72, 150, 252, 270), stream=buf.getvalue()
        )
    doc.save(path)
    doc.close()
    return path


def test_extract_figures_finds_one_image(tmp_path, monkeypatch):
    from app.core import docling_extractor as extractor

    pdf = _make_pdf_with_image(str(tmp_path / "com_imagem.pdf"), True)
    # Força fallback fitz (determinístico, sem modelo Docling).
    monkeypatch.setattr(extractor, "_extract_figures_docling", lambda *_a: [])
    out = tmp_path / "figs"
    figuras = extractor.extract_figures(pdf, str(out))
    assert len(figuras) == 1
    fig = figuras[0]
    assert fig["page_number"] == 1
    assert fig["content_type"] == "image/png"
    assert fig["file_path"] and fig["file_path"].endswith(".png")
    import os

    assert os.path.isfile(fig["file_path"])


def test_extract_figures_empty_for_text_only(tmp_path, monkeypatch):
    from app.core import docling_extractor as extractor

    pdf = _make_pdf_with_image(str(tmp_path / "sem_imagem.pdf"), False)
    monkeypatch.setattr(extractor, "_extract_figures_docling", lambda *_a: [])
    figuras = extractor.extract_figures(pdf, str(tmp_path / "figs"))
    assert figuras == []


def test_pipeline_persists_figures_and_analysis_exposes_array(
    monkeypatch, client, db_session, make_user, auth_headers_for, tmp_path
):
    import app.tasks.document_tasks as tasks

    user = make_user()
    pdf = _make_pdf_with_image(str(tmp_path / "peticao.pdf"), True)

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

    # Pipeline determinístico: texto + IA stubados, figuras via fitz real.
    monkeypatch.setattr(
        tasks.PDFExtractor, "extract_text", staticmethod(lambda file_path: "TEXTO DA PETICAO")
    )

    def fake_analyze(self, text, strategy_prompt=None):
        return {
            "summary": "resumo",
            "requests": ["pedido 1"],
            "laws": ["Art. 1"],
            "evidence": "prova",
            "defense_theses": ["tese 1"],
        }

    monkeypatch.setattr(
        "app.core.ai_engine.LegalAnalyzer.analyze_petition", fake_analyze
    )
    monkeypatch.setattr(tasks.settings, "DOCLING_ENABLED", False)
    monkeypatch.setattr(
        tasks, "figure_directory", lambda _doc_id: str(tmp_path / "figs" / str(_doc_id))
    )

    _run_pipeline_task(tasks, document.id, pdf)

    analysis = (
        db_session.query(Analysis).filter_by(document_id=document.id).one()
    )
    resp = client.get(
        f"/api/v1/analysis/{analysis.id}", headers=auth_headers_for(user)
    )
    assert resp.status_code == 200
    payload = resp.json()
    figuras = payload.get("figuras") or payload.get("figuras".lower()) or []
    # Tolerant camel/snake: backend envia downloadUrl + download_url.
    assert isinstance(payload["figuras"], list)
    assert len(payload["figuras"]) == 1
    fig = payload["figuras"][0]
    assert fig["pageNumber"] == 1 or fig.get("page_number") == 1
    assert fig["downloadUrl"] or fig.get("download_url")

    download_path = fig["downloadUrl"] or fig["download_url"]
    assert download_path.startswith("/documents/")
    dl = client.get(
        f"/api/v1{download_path}", headers=auth_headers_for(user)
    )
    assert dl.status_code == 200
    assert "image" in dl.headers["content-type"]
    assert len(dl.content) > 100


def test_analysis_without_figures_returns_empty_array(
    monkeypatch, client, db_session, make_user, auth_headers_for, tmp_path
):
    import app.tasks.document_tasks as tasks

    user = make_user()
    pdf = _make_pdf_with_image(str(tmp_path / "sem.pdf"), False)

    document = Document(
        user_id=user.id,
        filename="sem.pdf",
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
        return {"summary": "resumo"}

    monkeypatch.setattr(
        "app.core.ai_engine.LegalAnalyzer.analyze_petition", fake_analyze
    )
    monkeypatch.setattr(tasks.settings, "DOCLING_ENABLED", False)
    monkeypatch.setattr(
        tasks, "figure_directory", lambda _doc_id: str(tmp_path / "figs2" / str(_doc_id))
    )

    _run_pipeline_task(tasks, document.id, pdf)

    analysis = (
        db_session.query(Analysis).filter_by(document_id=document.id).one()
    )
    resp = client.get(
        f"/api/v1/analysis/{analysis.id}", headers=auth_headers_for(user)
    )
    assert resp.status_code == 200
    # Backend retorna [] (nunca null) — a UI traduz para "documento sem figuras".
    assert resp.json()["figuras"] == []
