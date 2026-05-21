"""
Mock auth routes.
- POST /auth/login: client sends an email, we return the matching user.
- GET  /auth/me:    returns the user the X-User-Id header is pointing to.

In a real app, login would issue a JWT. Here we just return the user record
and the frontend stores the user id for subsequent requests.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import User
from app.schemas.schemas import UserRead, LoginRequest
from app.core.security import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=UserRead)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if user is None:
        raise HTTPException(status_code=404, detail="No user with that email")
    return user


@router.get("/me", response_model=UserRead)
def me(current_user: User = Depends(get_current_user)):
    return current_user
