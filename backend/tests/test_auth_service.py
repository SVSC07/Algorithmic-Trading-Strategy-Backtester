"""
tests/test_auth_service.py
Tests for AuthService (Milestone 3).

Uses SQLite in-memory DB via SQLAlchemy to avoid needing the real Postgres.
"""
import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest-only-at-least-32bytes")

from app.models import Base
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.domain import AuthError, ConflictError, ValidationError


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    s = Session()
    yield s
    s.close()
    Base.metadata.drop_all(engine)


@pytest.fixture
def svc(session):
    repo = UserRepository(session)
    return AuthService(session, repo)


class TestRegister:
    def test_happy_path(self, svc):
        user = svc.register("Alice", "alice@example.com", "password123")
        assert user.user_id is not None
        assert user.role == "TRADER"
        assert user.email == "alice@example.com"

    def test_password_is_hashed(self, svc):
        user = svc.register("Bob", "bob@example.com", "securepass")
        assert user.password_hash != "securepass"
        assert len(user.password_hash) > 20  # bcrypt hash is long

    def test_short_password_raises_validation_error(self, svc):
        with pytest.raises(ValidationError):
            svc.register("Charlie", "charlie@example.com", "short")

    def test_exactly_8_chars_accepted(self, svc):
        user = svc.register("Dana", "dana@example.com", "12345678")
        assert user is not None

    def test_duplicate_email_raises_conflict(self, svc):
        svc.register("Eve", "eve@example.com", "password123")
        with pytest.raises(ConflictError):
            svc.register("Eve2", "eve@example.com", "password456")

    def test_role_is_always_trader(self, svc):
        user = svc.register("Frank", "frank@example.com", "password123")
        assert user.role == "TRADER"


class TestLogin:
    def test_happy_path(self, svc):
        svc.register("Grace", "grace@example.com", "password123")
        token, user = svc.login("grace@example.com", "password123")
        assert isinstance(token, str)
        assert len(token) > 10
        assert user.email == "grace@example.com"

    def test_wrong_password_raises_auth_error(self, svc):
        svc.register("Henry", "henry@example.com", "password123")
        with pytest.raises(AuthError):
            svc.login("henry@example.com", "wrongpass")

    def test_unknown_email_raises_auth_error(self, svc):
        with pytest.raises(AuthError):
            svc.login("nobody@example.com", "password123")

    def test_unknown_email_same_message_as_wrong_password(self, svc):
        """Non-enumeration: both errors must have the same message."""
        svc.register("Iris", "iris@example.com", "password123")
        try:
            svc.login("nobody@example.com", "password123")
        except AuthError as e:
            msg_unknown = str(e)
        try:
            svc.login("iris@example.com", "wrongpassword")
        except AuthError as e:
            msg_wrong = str(e)
        assert msg_unknown == msg_wrong

    def test_token_decodes_to_correct_user(self, svc):
        from app.core.security import decode_token
        svc.register("Jack", "jack@example.com", "password123")
        token, user = svc.login("jack@example.com", "password123")
        payload = decode_token(token)
        assert payload["user_id"] == user.user_id
        assert payload["role"] == "TRADER"


class TestUserFromToken:
    def test_valid_token_returns_user(self, svc):
        svc.register("Karen", "karen@example.com", "password123")
        token, user = svc.login("karen@example.com", "password123")
        retrieved = svc.user_from_token(token)
        assert retrieved.user_id == user.user_id

    def test_invalid_token_raises_auth_error(self, svc):
        with pytest.raises(AuthError):
            svc.user_from_token("garbage.token.value")

    def test_expired_token_raises_auth_error(self, svc):
        import time
        import jwt as pyjwt
        import os
        secret = os.environ["SECRET_KEY"]
        stale = pyjwt.encode(
            {"user_id": 999, "role": "TRADER", "exp": int(time.time()) - 1},
            secret,
            algorithm="HS256",
        )
        with pytest.raises(AuthError):
            svc.user_from_token(stale)
