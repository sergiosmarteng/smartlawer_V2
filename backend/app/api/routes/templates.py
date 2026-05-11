from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, selectinload

from app.api import deps
from app.core.doc_generator import DocxGenerator
from app.models.analysis import Analysis
from app.models.document import Document
from app.models.user import User

router = APIRouter()

TEMPLATE_DIR = Path(__file__).resolve().parents[3] / "templates"
BASE_TEMPLATE_PATH = TEMPLATE_DIR / "base_template.docx"


def _get_owned_analysis(
    db: Session,
    *,
    identifier: UUID,
    current_user: User,
) -> Analysis | None:
    analysis = (
        db.query(Analysis)
        .options(selectinload(Analysis.document))
        .join(Document, Analysis.document_id == Document.id)
        .filter(Analysis.id == identifier, Document.user_id == current_user.id)
        .first()
    )
    if analysis:
        return analysis

    document = (
        db.query(Document)
        .options(
            selectinload(Document.analysis),
            selectinload(Document.user),
        )
        .filter(Document.id == identifier, Document.user_id == current_user.id)
        .first()
    )
    if not document:
        return None

    return document.analysis


def _build_download_filename(analysis: Analysis) -> str:
    source_name = Path(analysis.document.filename or "defense").stem
    safe_name = source_name.replace(" ", "_")
    return f"{safe_name}_defense_strategy.docx"


def _build_docx_file_response(analysis: Analysis) -> FileResponse:
    analysis_data = {
        "summary": analysis.summary or "",
        "requests": analysis.requests or [],
        "laws": analysis.laws or [],
        "evidence": analysis.evidence or "",
        "defense_theses": analysis.defense_theses or [],
    }

    output_path = DocxGenerator.generate_defense(
        analysis_dict=analysis_data,
        template_path=str(BASE_TEMPLATE_PATH),
    )
    return FileResponse(
        path=output_path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=_build_download_filename(analysis),
    )


@router.get("/{analysis_id}/generate")
def generate_docx_document(
    analysis_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    analysis = _get_owned_analysis(
        db,
        identifier=analysis_id,
        current_user=current_user,
    )
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    try:
        return _build_docx_file_response(analysis)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno de geracao do DOCX: {exc}",
        ) from exc
