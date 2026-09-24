from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.api import deps
from app.core.config import settings
from app.core import security
from app.core.audit import record_audit
from app.crud.user import get_user_by_email, get_user_by_username
from app.models.audit_event import AuditEvent
from app.schemas.user import Token

router = APIRouter()

@router.post("/login/access-token", response_model=Token)
def login_access_token(
    db: Session = Depends(deps.get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Token:
    """
    OAuth2 compatible token login, get an access token for future requests.
    Supports login via email or username.
    """
    user = get_user_by_email(db, email=form_data.username) or get_user_by_username(db, username=form_data.username)
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password"
        )
    elif not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Subject of the token uses the database ID 
    access_token = security.create_access_token(
        subject=user.id, expires_delta=access_token_expires
    )

    record_audit(
        db,
        event_type=AuditEvent.AUTH_LOGIN,
        user_id=user.id,
        entity_type="user",
        entity_id=user.id,
    )

    return Token(
        access_token=access_token,
        token_type="bearer"
    )
