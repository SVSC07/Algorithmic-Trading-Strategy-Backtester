"""
core/security.py
JWT and password utilities.

Tokens: HS256, 8-hour expiry. Payload: {"user_id": int, "role": str, "exp": int}.
SECRET_KEY must be set in the environment; no hardcoded fallback.
"""
import os
import time
from typing import Any

import bcrypt
import jwt

from app.domain import AuthError

_ALGORITHM = "HS256"
_EXPIRY_SECONDS = 8 * 3600  # 8 hours


def _secret() -> str:
    """Read SECRET_KEY from env; raise at call-time if missing."""
    key = os.environ.get("SECRET_KEY")
    if not key:
        raise RuntimeError("SECRET_KEY environment variable is not set")
    return key


def hash_password(plain: str) -> str:
    """Return a bcrypt hash of *plain*."""
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    """Return True when *plain* matches the bcrypt *hashed* value."""
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_token(user_id: int, role: str) -> str:
    """Return a signed JWT containing user_id and role, expiring in 8 hours."""
    payload: dict[str, Any] = {
        "user_id": user_id,
        "role": role,
        "exp": int(time.time()) + _EXPIRY_SECONDS,
    }
    return jwt.encode(payload, _secret(), algorithm=_ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    """
    Decode and verify *token*.

    Raises AuthError on expiry, invalid signature, or malformed token.
    Returns the raw payload dict on success.
    """
    try:
        return jwt.decode(token, _secret(), algorithms=[_ALGORITHM])
    except jwt.ExpiredSignatureError as exc:
        raise AuthError("Token has expired") from exc
    except jwt.InvalidTokenError as exc:
        raise AuthError("Invalid token") from exc
