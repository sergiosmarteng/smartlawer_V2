import os
import shutil
from pathlib import Path
from typing import List
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, selectinload

from app.api import deps
from app.core.doc_generator import DocxGenerator
from app.models.analysis import Analysis
from app.models.document import Document
from app.models.template import Template
from app.models.user import User
from app.schemas.template import TemplateResponse

router = APIRouter()

TEMPLATE_DIR = Path(__file__).resolve().parents[3] / "templates"
BASE_TEMPLATE_PATH = TEMPLATE_DIR / "base_template.docx"

TEMPLATE_UPLOAD_DIR = os.path.join(
    "/data/uploads"
    if os.environ.get("ENVIRONMENT") != "development_local"
    else "./uploads",
    "templates",
)

os.makedirs(TEMPLATE_UPLOAD_DIR, exist_ok=True)

DOCX_CONTENT_TYPES = frozenset(
    {
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/octet-stream",
    }
)


def _template_response(template: Template) -> TemplateResponse:
    placeholders = list(template.placeholders or [])
    return TemplateResponse(
        id=template.id,
        name=template.name,
        placeholders=placeholders,
        unsupported_placeholders=DocxGenerator.unsupported_placeholders(placeholders),
        created_at=template.created_at,
    )


def _get_owned_template(
    db: Session,
    *,
    template_id: UUID,
    current_user: User,
) -> Template | None:
    return (
        db.query(Template)
        .filter(Template.id == template_id, Template.user_id == current_user.id)
        .first()
    )


@router.post("", response_model=TemplateResponse)
@router.post("/", response_model=TemplateResponse, include_in_schema=False)
async def upload_template(
    file: UploadFile = File(...),
    name: str | None = Form(default=None),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """Upload a user-owned DOCX template (C1/BL-015).

    The file is persisted under the uploads volume, Jinja placeholders are
    discovered at upload time, and incompatible roots are reported (not
    rejected) so the UI can warn before generation. Generation with an
    incompatible template fails with 422 naming the offenders.
    """
    filename = file.filename or ""
    if (
        file.content_type not in DOCX_CONTENT_TYPES
        or not filename.lower().endswith(".docx")
    ):
        raise HTTPException(status_code=400, detail="Only DOCX files are allowed")

    user_dir = Path(TEMPLATE_UPLOAD_DIR) / str(current_user.id)
    user_dir.mkdir(parents=True, exist_ok=True)
    file_path = user_dir / f"{uuid4()}.docx"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        placeholders = DocxGenerator.discover_placeholders(str(file_path))
    except (ValueError, FileNotFoundError) as exc:
        file_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=400, detail=f"Invalid DOCX template: {exc}"
        ) from exc

    template_name = (name or "").strip() or Path(filename).stem or "template"
    template = Template(
        user_id=current_user.id,
        name=template_name[:255],
        file_path=str(file_path),
        placeholders=placeholders,
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return _template_response(template)


@router.get("", response_model=List[TemplateResponse])
@router.get("/", response_model=List[TemplateResponse], include_in_schema=False)
def list_templates(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """List the current user's templates, newest first."""
    templates = (
        db.query(Template)
        .filter(Template.user_id == current_user.id)
        .order_by(Template.created_at.desc())
        .all()
    )
    return [_template_response(template) for template in templates]


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


def _build_docx_file_response(
    analysis: Analysis,
    template_path: str | None = None,
) -> FileResponse:
    analysis_data = {
        "summary": analysis.summary or "",
        "requests": analysis.requests or [],
        "laws": analysis.laws or [],
        "evidence": analysis.evidence or "",
        "defense_theses": analysis.defense_theses or [],
    }

    output_path = DocxGenerator.generate_defense(
        analysis_dict=analysis_data,
        template_path=template_path or str(BASE_TEMPLATE_PATH),
    )
    return FileResponse(
        path=output_path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=_build_download_filename(analysis),
    )


@router.get("/{analysis_id}/generate")
def generate_docx_document(
    analysis_id: UUID,
    template_id: UUID | None = None,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """Generate the defense DOCX, optionally with a user template (C1).

    Identifier rule (BL-014, preserved): ``analysis_id`` accepts an analysis
    id OR its document id. ``template_id`` must be owned by the caller;
    unknown/other-user ids are 404. Templates referencing unsupported
    placeholders fail with 422 naming them — before any opaque render
    failure. Omitted ``template_id`` keeps the legacy base-template path.
    """
    analysis = _get_owned_analysis(
        db,
        identifier=analysis_id,
        current_user=current_user,
    )
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    template_path: str | None = None
    if template_id is not None:
        template = _get_owned_template(
            db,
            template_id=template_id,
            current_user=current_user,
        )
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        unsupported = DocxGenerator.unsupported_placeholders(
            list(template.placeholders or [])
        )
        if unsupported:
            raise HTTPException(
                status_code=422,
                detail={
                    "message": (
                        "Template references placeholders with no analysis data: "
                        + ", ".join(unsupported)
                    ),
                    "unsupported_placeholders": unsupported,
                    "supported_keys": sorted(DocxGenerator.SUPPORTED_CONTEXT_KEYS),
                },
            )
        template_path = template.file_path

    try:
        return _build_docx_file_response(analysis, template_path)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno de geracao do DOCX: {exc}",
        ) from exc
