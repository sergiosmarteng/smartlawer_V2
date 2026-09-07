"""Tests for A2: feature-flagged Docling ingestion (Onda A - RAG)."""

import pytest

import app.tasks.document_tasks as tasks
from app.core import docling_extractor
from app.core.docling_extractor import extract_markdown
from app.models.analysis import Analysis
from app.models.document import Document


@pytest.fixture()
def pdf_path(temp_dir):
    path = temp_dir / "peticao.pdf"
    path.write_bytes(b"%PDF-1.4 stub")
    return str(path)


@pytest.fixture()
def stored_document(db_session, make_user, pdf_path):
    user = make_user()
    document = Document(
        user_id=user.id,
        filename="peticao.pdf",
        file_path=pdf_path,
        content_type="application/pdf",
        status=Document.STATUS_UPLOADED,
    )
    db_session.add(document)
    db_session.commit()
    db_session.refresh(document)
    return document


@pytest.fixture()
def stub_pipeline(monkeypatch, pdf_path):
    """Stub PDF extraction + AI; capture what the analyzer receives."""
    calls = {}

    def fake_extract(file_path):
        calls["extract_path"] = file_path
        return "TEXTO BRUTO DA PETICAO"

    def fake_analyze(self, text):
        calls["analysis_input"] = text
        return {
            "summary": "resumo",
            "requests": ["pedido 1"],
            "laws": ["Art. 1"],
            "evidence": "prova",
            "defense_theses": ["tese 1"],
        }

    monkeypatch.setattr(
        "app.tasks.document_tasks.PDFExtractor.extract_text",
        staticmethod(fake_extract),
    )
    monkeypatch.setattr(
        "app.core.ai_engine.LegalAnalyzer.analyze_petition", fake_analyze
    )
    return calls


class _FakeTask:
    max_retries = 3

    def __init__(self):
        self.request = type("Req", (), {"retries": 0})()
        self.retry_called = False

    def retry(self, exc=None, countdown=None):
        del exc, countdown
        self.retry_called = True
        raise RuntimeError("retry")


def _run_task(stored_document, pdf_path):
    task = _FakeTask()
    tasks.process_pdf_task.func(task, str(stored_document.id), pdf_path)
    return task


# --- Adapter unit tests -----------------------------------------------------


def test_adapter_returns_none_when_converter_missing(monkeypatch, pdf_path):
    def boom():
        raise ImportError("No module named 'docling'")

    monkeypatch.setattr(docling_extractor, "_get_converter", boom)
    docling_extractor.reset_converter_cache()
    assert extract_markdown(pdf_path) is None


def test_adapter_returns_none_on_empty_output(monkeypatch, pdf_path):
    class EmptyDoc:
        def export_to_markdown(self):
            return "   "

    class FakeResult:
        document = EmptyDoc()

    class FakeConverter:
        def convert(self, _path):
            return FakeResult()

    monkeypatch.setattr(docling_extractor, "_get_converter", lambda: FakeConverter())
    docling_extractor.reset_converter_cache()
    assert extract_markdown(pdf_path) is None


def test_adapter_returns_markdown_on_success(monkeypatch, pdf_path):
    class Doc:
        def export_to_markdown(self):
            return "# Peticao\n\n## Dos Fatos"

    class FakeResult:
        document = Doc()

    class FakeConverter:
        def convert(self, _path):
            return FakeResult()

    monkeypatch.setattr(docling_extractor, "_get_converter", lambda: FakeConverter())
    docling_extractor.reset_converter_cache()
    assert extract_markdown(pdf_path) == "# Peticao\n\n## Dos Fatos"


# --- Wiring tests (flag on/off/failure) -------------------------------------


def test_flag_off_never_calls_docling(
    monkeypatch, db_session, stub_pipeline, stored_document, pdf_path
):
    monkeypatch.setattr(tasks.settings, "DOCLING_ENABLED", False)

    def forbidden(_path):
        raise AssertionError("Docling must not run when flag is off")

    monkeypatch.setattr(tasks, "docling_extract_markdown", forbidden)
    _run_task(stored_document, pdf_path)

    assert stub_pipeline["analysis_input"] == "TEXTO BRUTO DA PETICAO"
    db_session.refresh(stored_document)
    assert stored_document.status == Document.STATUS_COMPLETED
    assert stored_document.raw_text == "TEXTO BRUTO DA PETICAO"
    assert stored_document.structured_markdown is None


def test_flag_on_success_uses_markdown(
    monkeypatch, db_session, stub_pipeline, stored_document, pdf_path
):
    monkeypatch.setattr(tasks.settings, "DOCLING_ENABLED", True)
    monkeypatch.setattr(
        tasks, "docling_extract_markdown", lambda _p: "# Peticao\n\n## Dos Fatos"
    )
    _run_task(stored_document, pdf_path)

    assert stub_pipeline["analysis_input"] == "# Peticao\n\n## Dos Fatos"
    db_session.refresh(stored_document)
    assert stored_document.status == Document.STATUS_COMPLETED
    assert stored_document.raw_text == "TEXTO BRUTO DA PETICAO"
    assert stored_document.structured_markdown == "# Peticao\n\n## Dos Fatos"
    analysis = (
        db_session.query(Analysis)
        .filter_by(document_id=stored_document.id)
        .one()
    )
    assert analysis.summary == "resumo"


def test_flag_on_failure_falls_back_to_raw(
    monkeypatch, db_session, stub_pipeline, stored_document, pdf_path
):
    monkeypatch.setattr(tasks.settings, "DOCLING_ENABLED", True)

    def boom(_path):
        raise RuntimeError("docling exploded")

    monkeypatch.setattr(tasks, "docling_extract_markdown", boom)
    _run_task(stored_document, pdf_path)

    assert stub_pipeline["analysis_input"] == "TEXTO BRUTO DA PETICAO"
    db_session.refresh(stored_document)
    assert stored_document.status == Document.STATUS_COMPLETED
    assert stored_document.structured_markdown is None
