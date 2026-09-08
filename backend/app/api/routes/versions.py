from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api import deps
from app.api.routes.templates import _get_owned_analysis
from app.models.generated_document import GeneratedDocument
from app.models.user import User
from app.schemas.workflow import GeneratedVersionResponse

router = APIRouter()

DOCX_MEDIA_TYPE = (
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
)


def _version_payload(
    analysis_id: UUID, row: GeneratedDocument
) -> GeneratedVersionResponse:
    return GeneratedVersionResponse(
        version=row.version,
        template_id=row.template_id,
        created_at=row.created_at,
        download_url=f"/analysis/{analysis_id}/versions/{row.version}",
    )


@router.get(
    "/analysis/{analysis_id}/versions",
    response_model=list[GeneratedVersionResponse],
)
def list_generated_versions(
    analysis_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """List persisted DOCX generations for an analysis, newest first (C2)."""
    analysis = _get_owned_analysis(
        db, identifier=analysis_id, current_user=current_user
    )
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    rows = (
        db.query(GeneratedDocument)
        .filter(
            GeneratedDocument.analysis_id == analysis.id,
            GeneratedDocument.user_id == current_user.id,
        )
        .order_by(GeneratedDocument.version.desc())
        .all()
    )
    return [_version_payload(analysis.id, row) for row in rows]


@router.get("/analysis/{analysis_id}/versions/{version}")
def download_generated_version(
    analysis_id: UUID,
    version: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """Recover a previous DOCX generation (C2 DoD)."""
    analysis = _get_owned_analysis(
        db, identifier=analysis_id, current_user=current_user
    )
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    row = (
        db.query(GeneratedDocument)
        .filter(
            GeneratedDocument.analysis_id == analysis.id,
            GeneratedDocument.version == version,
            GeneratedDocument.user_id == current_user.id,
        )
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Version not found")
    if not Path(row.file_path).exists():
        raise HTTPException(
            status_code=404, detail="Version file is no longer available"
        )

    source_name = Path(analysis.document.filename or "defense").stem.replace(" ", "_")
    return FileResponse(
        path=row.file_path,
        media_type=DOCX_MEDIA_TYPE,
        filename=f"{source_name}_v{row.version}.docx",
    )
