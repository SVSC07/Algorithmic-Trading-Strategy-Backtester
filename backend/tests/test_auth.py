"""
Unit tests for Auth Service & Security.
Owned by Molik.
"""
import pytest
from app.domain import ValidationError, AuthError, ConflictError
from app.core.security import hash_password, verify_password, create_token, decode_token
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService

def test_password_hashing():
    pwd = "supersecret123"
    hashed = hash_password(pwd)
    assert hashed != pwd
    assert verify_password(pwd, hashed) is True
    assert verify_password("wrongpassword", hashed) is False

def test_token_creation_and_decoding():
    token = create_token(user_id=42, role="TRADER")
    payload = decode_token(token)
    assert payload["user_id"] == 42
    assert payload["role"] == "TRADER"

def test_auth_service_register_and_login(db_session):
    repo = UserRepository(db_session)
    service = AuthService(db_session, repo)

    # Short password error (< 8)
    with pytest.raises(ValidationError):
        service.register(name="User", email="u@test.com", password="abc")

    # Register
    user = service.register(name="User One", email="u1@test.com", password="password123")
    assert user.user_id is not None
    assert user.role == "TRADER"

    # Duplicate email conflict
    with pytest.raises(ConflictError):
        service.register(name="User Two", email="u1@test.com", password="password123")

    # Login success
    token, logged_in = service.login(email="u1@test.com", password="password123")
    assert logged_in.user_id == user.user_id
    assert token is not None

    # Login bad credentials
    with pytest.raises(AuthError):
        service.login(email="u1@test.com", password="wrongpassword")
