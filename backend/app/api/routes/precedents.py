from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api import deps
from app.core.precedents import PRECEDENTS, ensure_precedents, precedent_label
from app.models.user import User

router = APIRouter()


@router.get("")
def list_precedents(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """List the shared jurisprudence corpus labels (C5/BL-023)."""
    del db, current_user
    return [
        {
            "key": item["key"],
            "label": precedent_label(item),
            "tribunal": item["tribunal"],
            "tema": item["tema"],
            "fonte": item["fonte"],
        }
        for item in PRECEDENTS
    ]


@router.post("/seed")
def seed_precedents(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_admin_user),
):
    """(Re)seed the shared corpus — admin only.

    Needed after configuring embedding keys so seeds gain real vectors,
    or after curating new precedents.
    """
    del current_user
    return ensure_precedents(db)
