from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api import deps
from app.core.audit import record_audit
from app.crud import user as crud
from app.schemas.user import UserCreate, UserResponse
from app.models.audit_event import AuditEvent
from app.models.user import User

router = APIRouter()

@router.post("/register", response_model=UserResponse)
def create_user_endpoint(
    user_in: UserCreate,
    db: Session = Depends(deps.get_db)
):
    """
    Create new user.
    """
    existing_email = crud.get_user_by_email(db, email=user_in.email)
    if existing_email:
        raise HTTPException(
            status_code=400,
            detail="A user with this email already exists.",
        )
    existing_username = crud.get_user_by_username(db, username=user_in.username)
    if existing_username:
        raise HTTPException(status_code=400, detail="A user with this username already exists.")
    user = crud.create_user(db, user=user_in)
    record_audit(
        db,
        event_type=AuditEvent.AUTH_REGISTER,
        user_id=user.id,
        entity_type="user",
        entity_id=user.id,
    )
    return user

@router.get("/me", response_model=UserResponse)
def read_user_me(
    current_user: User = Depends(deps.get_current_active_user)
):
    """
    Get current user.
    """
    return current_user
