"""
api/auth.py
Auth endpoints: POST /api/auth/register, POST /api/auth/login.
Both are public (no token required).
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.api.deps import get_session
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str  # min length checked in service (raises ValidationError → 400)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/register", status_code=201)
def register(body: RegisterRequest, session: Session = Depends(get_session)):
    """
    POST /api/auth/register — public.
    Creates a TRADER user. 409 if email exists. 400 if password < 8 chars.
    """
    svc = AuthService(session, UserRepository(session))
    user = svc.register(body.name, body.email, body.password)
    return {
        "user_id": user.user_id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
    }


@router.post("/login", status_code=200)
def login(body: LoginRequest, session: Session = Depends(get_session)):
    """
    POST /api/auth/login — public.
    Returns JWT token and user details. 401 on bad credentials.
    """
    svc = AuthService(session, UserRepository(session))
    token, user = svc.login(body.email, body.password)
    return {
        "token": token,
        "user": {
            "user_id": user.user_id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
        },
    }
