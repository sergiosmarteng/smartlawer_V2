"""Onda 2B integração final — regressões cruzadas sem duplicação (§9.6)."""

from app.crud import run as run_crud
from app.models.analysis_run import AnalysisRun
from app.models.document import Document
from app.models.document_revision import DocumentRevision


def _document(db_session, make_user, name="p2b.pdf"):
    user = make_user()
    document = Document(
        user_id=user.id, filename=name, file_path=f"/tmp/{name}",
        content_type="application/pdf", status="uploaded",
    )
    db_session.add(document)
    db_session.commit()
    db_session.refresh(document)
    return user, document


def _run(db_session, user, document, areas, fixture):
    rev = DocumentRevision(
        document_id=document.id, user_id=user.id,
        sha256="sha-2b", pages_total=4,
    )
    db_session.add(rev)
    db_session.commit()
    db_session.refresh(rev)
    run = AnalysisRun(
        user_id=user.id, document_id=document.id,
        status=AnalysisRun.RUNNING,
        snapshot={
            "areas": areas,
            "document_ids": [str(document.id)],
            "revision_ids": [str(rev.id)],
            "fixture": fixture,
        },
    )
    db_session.add(run)
    db_session.commit()
    db_session.refresh(run)
    return run


def _enable(*flags):
    from app.core.config import settings

    return [(settings, flag) for flag in flags]


def test_contracts_tax_share_single_objects(db_session, make_user, monkeypatch):
    from app.core.config import settings
    from app.core.pipeline.orchestrator import run_universal_pipeline

    for flag in ("DOSSIER_MODULE_CONTRACTS", "DOSSIER_MODULE_TAX"):
        monkeypatch.setattr(settings, flag, True)
    user, document = _document(db_session, make_user)
    run = _run(db_session, user, document, ["contracts", "tax"], {
        "claims": [{"id": "claim-1", "title": "Multa contratual e tributária",
                    "source_refs": ["src-1"]}],
        "facts": [
            {"id": "f1", "statement": "Cláusula penal do contrato",
             "asserted_by": "parte-A", "epistemic_status": "documented",
             "source_refs": ["src-1"]},
            {"id": "f2", "statement": "Auto de infração do ente",
             "asserted_by": "parte-A", "epistemic_status": "documented",
             "source_refs": ["src-2"]},
        ],
        "evidence": [{"id": "ev1", "presence_status": "examined"}],
        "legal_references": [],
        "visuals": [],
        "sources": [{"id": "src-1", "page_number": 1},
                    {"id": "src-2", "page_number": 2}],
        "coverage": {"pages_total": 4, "pages_extracted": 4},
    })
    artifact = run_universal_pipeline(db_session, run_id=run.id)
    assert artifact is not None
    content = artifact.content
    assert set(content["module_results"]) == {"contracts", "tax"}
    assert [c["id"] for c in content["claims"]] == ["claim-1"]
    assert [f["id"] for f in content["facts"]] == ["f1", "f2"]


def test_corporate_real_estate_share_single_objects(db_session, make_user, monkeypatch):
    from app.core.config import settings
    from app.core.pipeline.orchestrator import run_universal_pipeline

    for flag in ("DOSSIER_MODULE_CORPORATE", "DOSSIER_MODULE_REAL_ESTATE"):
        monkeypatch.setattr(settings, flag, True)
    user, document = _document(db_session, make_user, name="p2b2.pdf")
    run = _run(db_session, user, document, ["corporate", "real_estate"], {
        "claims": [{"id": "claim-1", "title": "Imóvel em recuperação",
                    "source_refs": ["src-1"]}],
        "facts": [
            {"id": "f1", "statement": "Quotas societárias do imóvel",
             "asserted_by": "parte-A", "epistemic_status": "documented",
             "source_refs": ["src-1"]},
        ],
        "evidence": [{"id": "ev1", "presence_status": "examined"}],
        "legal_references": [],
        "visuals": [],
        "sources": [{"id": "src-1", "page_number": 1}],
        "coverage": {"pages_total": 4, "pages_extracted": 4},
    })
    artifact = run_universal_pipeline(db_session, run_id=run.id)
    assert artifact is not None
    content = artifact.content
    assert set(content["module_results"]) == {"corporate", "real_estate"}
    assert [c["id"] for c in content["claims"]] == ["claim-1"]
    values = [c.get("amount") for c in content["claims"]]
    assert len(values) == len(set(map(str, values)))


def test_flags_off_and_research_failure_preserve_documentary(db_session, make_user):
    from app.core.pipeline.orchestrator import run_universal_pipeline

    user, document = _document(db_session, make_user, name="p2b3.pdf")
    run = _run(db_session, user, document, ["tax", "administrative"], {
        "claims": [{"id": "claim-1", "title": "Anulação", "source_refs": ["src-1"]}],
        "facts": [{"id": "f1", "statement": "Auto de infração",
                   "epistemic_status": "documented", "source_refs": ["src-1"]}],
        "evidence": [],
        "legal_references": [],
        "visuals": [],
        "sources": [{"id": "src-1", "page_number": 1}],
        "coverage": {"pages_total": 4, "pages_extracted": 4},
    })
    artifact = run_universal_pipeline(db_session, run_id=run.id)
    assert artifact is not None
    assert artifact.content["module_results"] == {}
    assert [c["id"] for c in artifact.content["claims"]] == ["claim-1"]

    from app.core.legal_research import research_issues

    batch = research_issues(
        [{"id": "q1", "question": "Alíquota municipal"}],
        sources=[{"id": "muni", "available": False, "organ": "Município"}],
        reference_date="2026-10-04",
    )
    assert batch["partial"] is True
    assert batch["pending_actions"]
