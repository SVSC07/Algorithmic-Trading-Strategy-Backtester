"""
services/auth_service.py
AuthService — register, login, user_from_token.

RULES:
- register: always TRADER, password hashed, ConflictError on duplicate email,
  ValidationError if password < 8 chars.
- login: AuthError on unknown email or wrong password (same message, no enumeration).
- user_from_token: delegates token verification to core/security.py.
"""
from typing import Tuple

from sqlalchemy.orm import Session

from app.core.security import (
    create_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.domain import AuthError, ConflictError, NotFoundError, ValidationError
from app.models import User
from app.repositories.user_repository import UserRepository


class AuthService:
    def __init__(self, session: Session, user_repo: UserRepository) -> None:
        self._session = session
        self._repo = user_repo

    def register(self, name: str, email: str, password: str) -> User:
        """
        Create a new TRADER user.

        Raises ValidationError if password is shorter than 8 characters.
        Raises ConflictError if email is already registered.
        """
        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters")
        if self._repo.find_by_email(email) is not None:
            raise ConflictError(f"Email '{email}' is already registered")
        user = User(
            name=name,
            email=email,
            password_hash=hash_password(password),
            role="TRADER",
        )
        self._repo.save(user)
        self._session.commit()
        return user

    def login(self, email: str, password: str) -> Tuple[str, User]:
        """
        Authenticate a user.

        Returns (jwt_token, user) on success.
        Raises AuthError on unknown email or wrong password (same message for both
        so accounts cannot be enumerated).
        """
        _BAD_CREDS = "Invalid email or password"
        user = self._repo.find_by_email(email)
        if user is None:
            raise AuthError(_BAD_CREDS)
        if not verify_password(password, user.password_hash):
            raise AuthError(_BAD_CREDS)
        token = create_token(user_id=user.user_id, role=user.role)
        return token, user

    def user_from_token(self, token: str) -> User:
        """
        Decode *token* and return the corresponding User.

        Raises AuthError if the token is invalid or the user no longer exists.
        """
        payload = decode_token(token)  # raises AuthError on bad token
        user_id = payload.get("user_id")
        user = self._repo.find_by_id(user_id)
        if user is None:
            raise AuthError("User not found")
        return user
