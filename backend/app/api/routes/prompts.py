from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.core.audit import record_audit
from app.crud.prompt import set_default_profile
from app.models.audit_event import AuditEvent
from app.models.prompt_profile import PromptProfile
from app.models.user import User
from app.schemas.prompt import PromptProfileCreate, PromptProfileResponse

router = APIRouter()


@router.post("", response_model=PromptProfileResponse)
@router.post("/", response_model=PromptProfileResponse, include_in_schema=False)
def create_prompt_profile(
    payload: PromptProfileCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """Create a prompt profile (C3/BL-020)."""
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Profile name is required")
    profile = PromptProfile(
        user_id=current_user.id,
        name=name[:255],
        strategy_prompt=(payload.strategy_prompt or "").strip(),
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    if payload.is_default:
        profile = set_default_profile(db, profile=profile)
    record_audit(
        db,
        event_type=AuditEvent.PROMPT_CREATED,
        user_id=current_user.id,
        entity_type="prompt_profile",
        entity_id=profile.id,
        meta={"name": profile.name},
    )
    return profile


@router.get("", response_model=List[PromptProfileResponse])
@router.get("/", response_model=List[PromptProfileResponse], include_in_schema=False)
def list_prompt_profiles(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """List the current user's prompt profiles, default first."""
    return (
        db.query(PromptProfile)
        .filter(PromptProfile.user_id == current_user.id)
        .order_by(PromptProfile.is_default.desc(), PromptProfile.created_at.desc())
        .all()
    )


@router.patch("/{profile_id}/default", response_model=PromptProfileResponse)
def set_default_prompt_profile(
    profile_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """Make a profile the default AI run profile."""
    profile = (
        db.query(PromptProfile)
        .filter(
            PromptProfile.id == profile_id,
            PromptProfile.user_id == current_user.id,
        )
        .first()
    )
    if not profile:
        raise HTTPException(status_code=404, detail="Prompt profile not found")
    profile = set_default_profile(db, profile=profile)
    record_audit(
        db,
        event_type=AuditEvent.PROMPT_DEFAULT,
        user_id=current_user.id,
        entity_type="prompt_profile",
        entity_id=profile.id,
    )
    return profile


@router.delete("/{profile_id}", status_code=204)
def delete_prompt_profile(
    profile_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """Delete an owned prompt profile."""
    profile = (
        db.query(PromptProfile)
        .filter(
            PromptProfile.id == profile_id,
            PromptProfile.user_id == current_user.id,
        )
        .first()
    )
    if not profile:
        raise HTTPException(status_code=404, detail="Prompt profile not found")
    profile_name = profile.name
    db.delete(profile)
    db.commit()
    record_audit(
        db,
        event_type=AuditEvent.PROMPT_DELETED,
        user_id=current_user.id,
        entity_type="prompt_profile",
        entity_id=profile_id,
        meta={"name": profile_name},
    )
    return None
