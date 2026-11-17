"""
api/deps.py
Shared FastAPI dependencies: get_session, get_current_user, require_role.
"""
from typing import Callable

from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.security import decode_token
from app.domain import AuthError, ForbiddenError
from app.models import User
from app.repositories.user_repository import UserRepository


def get_session() -> Session:  # type: ignore[return]
    """Yield one SQLAlchemy session per request; always close it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    authorization: str | None = Header(default=None),
    session: Session = Depends(get_session),
) -> User:
    """
    Extract the bearer token from the Authorization header and return the User.

    Raises AuthError when the header is missing, malformed, or the token is invalid.
    """
    if authorization is None or not authorization.startswith("Bearer "):
        raise AuthError("Authorization header missing or malformed")
    token = authorization.removeprefix("Bearer ").strip()
    payload = decode_token(token)
    user_id = payload.get("user_id")
    repo = UserRepository(session)
    user = repo.find_by_id(user_id)
    if user is None:
        raise AuthError("User not found")
    return user


def require_role(*roles: str) -> Callable:
    """Return a dependency that raises ForbiddenError if the user's role is not in *roles*."""

    def _check(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise ForbiddenError(
                f"This action requires one of: {', '.join(roles)}"
            )
        return current_user

    return _check
