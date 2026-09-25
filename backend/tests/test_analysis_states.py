"""V2 T01 — sem sucesso fictício: falha de IA nunca vira COMPLETED."""

import pytest

import app.tasks.document_tasks as tasks
from app.core.ai_engine import (
    LegalAnalyzer,
    OutputInvalidError,
    ProviderUnavailableError,
)
from app.models.analysis import Analysis
from app.models.document import Document


def test_no_provider_raises_and_never_returns_generic_theses(monkeypatch):
    from app.core import ai_engine as engine

    monkeypatch.setattr(engine, "resolve_chat_config", lambda: None)
    analyzer = LegalAnalyzer()
    with pytest.raises(ProviderUnavailableError) as excinfo:
        analyzer.analyze_petition("texto da peticao")
    assert excinfo.value.code == "PROVIDER_UNAVAILABLE"


def test_normalize_never_injects_generic_theses():
    analyzer = LegalAnalyzer()
    out = analyzer._normalize_analysis_payload(
        {"summary": "s", "requests": [], "laws": [], "evidence": "e", "defense_theses": []}
    )
    assert out["kind"] == "analysis"
    assert out["requests"] == []
    assert out["defense_theses"] == []
    for thesis in out["defense_theses"]:
        assert thesis not in LegalAnalyzer.FALLBACK_THESES


def test_invalid_llm_json_raises_output_invalid(monkeypatch):
    import json as _json

    from app.core import ai_engine as engine

    monkeypatch.setattr(
        engine, "resolve_chat_config",
        lambda: {"model": "m", "base_url": None, "api_key": "k"},
    )
    analyzer = LegalAnalyzer.__new__(LegalAnalyzer)
    analyzer.api_key = "k"
    analyzer.model = "m"

    class _Msg:
        content = "nao-json {{{"

    class _Choice:
        message = _Msg()

    class _Comp:
        def create(self, **kwargs):
            return type("R", (), {"choices": [_Choice()]})()

    analyzer.client = type("C", (), {"chat": type("H", (), {"completions": _Comp()})()})()
    with pytest.raises((OutputInvalidError, ProviderUnavailableError)):
        analyzer.analyze_petition("texto")


def _run_task(stored_document, pdf_path):
    target = getattr(tasks.process_pdf_task, "func", None)
    if target is not None:
        class _FakeTask:
            max_retries = 3

            def __init__(self):
                self.request = type("Req", (), {"retries": 0})()

            def retry(self, exc=None, countdown=None):
                raise RuntimeError("retry")

        task = _FakeTask()
        target(task, str(stored_document.id), pdf_path)
        return task
    tasks.process_pdf_task.run(str(stored_document.id), pdf_path)
    return None


def test_pipeline_marks_error_without_analysis_on_provider_failure(
    monkeypatch, db_session, make_user, temp_dir
):
    pdf_path = temp_dir / "falha.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 stub")
    user = make_user()
    document = Document(
        user_id=user.id,
        filename="falha.pdf",
        file_path=str(pdf_path),
        content_type="application/pdf",
        status=Document.STATUS_UPLOADED,
    )
    db_session.add(document)
    db_session.commit()
    db_session.refresh(document)

    monkeypatch.setattr(
        "app.tasks.document_tasks.PDFExtractor.extract_text",
        staticmethod(lambda file_path: "TEXTO"),
    )
    monkeypatch.setattr(tasks.settings, "DOCLING_ENABLED", False)

    def boom(self, text, strategy_prompt=None):
        raise ProviderUnavailableError("sem chave")

    monkeypatch.setattr(
        "app.core.ai_engine.LegalAnalyzer.analyze_petition", boom
    )
    _run_task(document, str(pdf_path))

    db_session.refresh(document)
    assert document.status == Document.STATUS_ERROR
    assert document.error_message.startswith("PROVIDER_UNAVAILABLE:")
    assert (
        db_session.query(Analysis).filter_by(document_id=document.id).count() == 0
    )
