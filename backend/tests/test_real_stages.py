"""W-2 — estágios reais sobre blocos da revisão (sem fixture)."""

import dataclasses

from app.crud import run as run_crud
from app.models.analysis_run import AnalysisRun
from app.models.document import Document
from app.models.document_revision import DocumentRevision


def _seed(db_session, make_user):
    user = make_user()
    document = Document(
        user_id=user.id, filename="real.pdf", file_path="/tmp/real.pdf",
        content_type="application/pdf", status="uploaded",
    )
    db_session.add(document)
    db_session.commit()
    db_session.refresh(document)
    rev = DocumentRevision(
        document_id=document.id, user_id=user.id,
        sha256="sha-real", pages_total=2,
    )
    db_session.add(rev)
    db_session.commit()
    db_session.refresh(rev)
    from app.crud.extraction import replace_source_blocks

    replace_source_blocks(db_session, revision=rev, pages=[
        {"page_number": 1, "method": "pymupdf", "blocks": [
            {"id": "b1", "type": "text", "reading_order": 0,
             "original_text": "A parte A requer guarda compartilhada.",
             "normalized_text": "A parte A requer guarda compartilhada.",
             "quality_flags": []},
        ]},
        {"page_number": 2, "method": "pymupdf", "blocks": [
            {"id": "b2", "type": "text", "reading_order": 1,
             "original_text": "Contestação com pedido de alimentos.",
             "normalized_text": "Contestação com pedido de alimentos.",
             "quality_flags": []},
        ]},
    ])
    run = run_crud.create_run(db_session, user_id=user.id, document_id=document.id)
    return user, document, rev, run


class _StructProvider:
    def __init__(self, payloads=None, fail_on=()):
        self._payloads = payloads or {}
        self.fail_on = set(fail_on)
        self.prompts = []

    def complete_json(self, prompt):
        self.prompts.append(prompt)
        for marker in self.fail_on:
            if marker in prompt:
                raise RuntimeError("provedor caiu")
        for key, payload in self._payloads.items():
            if key in prompt:
                return dict(payload)
        return {"claims": [], "facts": [], "evidence": [], "legal_references": []}


class _AnalysisProvider:
    def analyze(self, payload):
        assert payload["represented_side"] in ("claimant", "respondent", "neutral")
        return {
            "procedural_issues": [],
            "theses": [{
                "id": "t1", "represented_side": "neutral", "issue": "Guarda",
                "conclusion": "Compartilhada", "factual_premises": ["f1"],
                "legal_premises": [], "supporting_refs": ["b1"], "adverse_refs": [],
            }],
            "risks": [], "actions": [], "questions": [], "limitations": [],
        }


def _payload_b1():
    return {
        "claims": [{"id": "c1", "title": "Guarda", "source_refs": ["b1"]}],
        "facts": [{"id": "f1", "statement": "Guarda requerida",
                   "asserted_by": "parte-A", "source_refs": ["b1"]}],
        "evidence": [],
        "legal_references": [],
    }


def test_real_blocks_produce_reconciled_sources_and_coverage(db_session, make_user):
    from app.core.pipeline.orchestrator import execute_real_stages

    _, _, _, run = _seed(db_session, make_user)
    out = execute_real_stages(
        db_session, run=run,
        struct_provider=_StructProvider(payloads={"guarda compartilhada": _payload_b1()}),
        analysis_provider=_AnalysisProvider(),
    )
    assert out["empty"] is False
    assert [c["id"] for c in out["reconciled"]["claims"]] == ["c1"]
    assert [f["id"] for f in out["reconciled"]["facts"]] == ["f1"]
    by_id = {s["id"]: s for s in out["sources"]}
    assert by_id["b1"]["page_number"] == 1
    assert out["coverage"]["pages_total"] == 2
    assert out["failed_batches"] == []
    assert out["analysis"]["theses"][0]["id"] == "t1"
    assert out["classification"].primary_area in (
        "family", "civil_procedure", "general")


def test_batch_markers_reach_provider_prompt(db_session, make_user):
    from app.core.pipeline.orchestrator import execute_real_stages

    _, _, _, run = _seed(db_session, make_user)
    provider = _StructProvider()
    execute_real_stages(
        db_session, run=run,
        struct_provider=provider, analysis_provider=_AnalysisProvider())
    assert provider.prompts
    assert any("[bloco b1" in p for p in provider.prompts)


def test_failed_batch_is_explicit_and_others_survive(db_session, make_user):
    from app.core.pipeline.orchestrator import execute_real_stages

    _, _, _, run = _seed(db_session, make_user)
    out = execute_real_stages(
        db_session, run=run,
        struct_provider=_StructProvider(
            payloads={"guarda compartilhada": _payload_b1()},
            fail_on=("Contestação",),
        ),
        analysis_provider=_AnalysisProvider(),
        max_batch_tokens=10,
    )
    assert len(out["failed_batches"]) == 1
    assert [c["id"] for c in out["reconciled"]["claims"]] == ["c1"]
    assert out["empty"] is False


def test_no_blocks_returns_empty_for_honest_failed(db_session, make_user):
    from app.core.pipeline.orchestrator import execute_real_stages

    user = make_user()
    document = Document(
        user_id=user.id, filename="vazio.pdf", file_path="/tmp/vazio.pdf",
        content_type="application/pdf", status="uploaded",
    )
    db_session.add(document)
    db_session.commit()
    db_session.refresh(document)
    rev = DocumentRevision(
        document_id=document.id, user_id=user.id,
        sha256="sha-vazio", pages_total=0,
    )
    db_session.add(rev)
    db_session.commit()
    db_session.refresh(rev)
    run = run_crud.create_run(db_session, user_id=user.id, document_id=document.id)
    out = execute_real_stages(
        db_session, run=run,
        struct_provider=_StructProvider(), analysis_provider=_AnalysisProvider())
    assert out["empty"] is True
    assert "sem blocos" in out["reason"].lower() or "bloco" in out["reason"].lower()
