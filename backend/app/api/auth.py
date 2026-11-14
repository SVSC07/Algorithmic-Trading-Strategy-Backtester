# STUB, owned by Molik, replaced on merge
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    user_repo = UserRepository(db)
    auth_service = AuthService(db, user_repo)
    user = auth_service.register(req.name, req.email, req.password)
    return {
        "user_id": user.user_id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
    }

@router.post("/login", status_code=status.HTTP_200_OK)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user_repo = UserRepository(db)
    auth_service = AuthService(db, user_repo)
    token, user = auth_service.login(req.email, req.password)
    return {
        "token": token,
        "user": {
            "user_id": user.user_id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
        },
    }
