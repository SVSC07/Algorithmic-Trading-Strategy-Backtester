# STUB, owned by Molik, replaced on merge
from fastapi import Depends, Header
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.domain import AuthError, ForbiddenError
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService

def get_current_user(
    authorization: str | None = Header(None),
    db: Session = Depends(get_db),
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise AuthError("Missing or invalid Authorization header")

    token = authorization.split(" ", 1)[1]
    user_repo = UserRepository(db)
    auth_service = AuthService(db, user_repo)
    return auth_service.user_from_token(token)

def require_trader(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in ("TRADER", "ADMIN"):
        raise ForbiddenError("Trader privileges required")
    return current_user

def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "ADMIN":
        raise ForbiddenError("Admin privileges required")
    return current_user
