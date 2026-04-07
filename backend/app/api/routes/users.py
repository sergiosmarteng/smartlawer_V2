from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api import deps
from app.crud import user as crud
from app.schemas.user import UserCreate, UserResponse
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
    user = crud.get_user_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this username already exists in the system.",
        )
    return crud.create_user(db, user=user_in)

@router.get("/me", response_model=UserResponse)
def read_user_me(
    current_user: User = Depends(deps.get_current_active_user)
):
    """
    Get current user.
    """
    return current_user
