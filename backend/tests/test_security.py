"""
tests/test_security.py
Tests for core/security.py and core/errors.py (Milestone 1).

Covers:
- token round trip
- expired token
- tampered signature
- wrong password
- every domain error → correct HTTP status code
- FastAPI RequestValidationError → 400 VALIDATION_ERROR
"""
import os
import time

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest-only")

from app.core.security import (
    create_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.core.errors import register_error_handlers
from app.domain import (
    AuthError,
    ConflictError,
    ForbiddenError,
    InsufficientDataError,
    NotFoundError,
    ValidationError,
)


# ---------------------------------------------------------------------------
# Password helpers
# ---------------------------------------------------------------------------

class TestPasswordHelpers:
    def test_hash_is_deterministic_enough(self):
        h1 = hash_password("hunter2")
        h2 = hash_password("hunter2")
        # bcrypt salts differ, but both verify correctly
        assert h1 != h2
        assert verify_password("hunter2", h1)
        assert verify_password("hunter2", h2)

    def test_verify_correct_password(self):
        hashed = hash_password("correct-horse")
        assert verify_password("correct-horse", hashed) is True

    def test_verify_wrong_password(self):
        hashed = hash_password("correct-horse")
        assert verify_password("wrong-horse", hashed) is False

    def test_empty_password_does_not_verify_against_other_hash(self):
        hashed = hash_password("nonempty")
        assert verify_password("", hashed) is False


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------

class TestTokenHelpers:
    def test_round_trip(self):
        token = create_token(user_id=42, role="TRADER")
        payload = decode_token(token)
        assert payload["user_id"] == 42
        assert payload["role"] == "TRADER"

    def test_round_trip_admin(self):
        token = create_token(user_id=1, role="ADMIN")
        payload = decode_token(token)
        assert payload["role"] == "ADMIN"

    def test_payload_contains_exp(self):
        token = create_token(user_id=7, role="TRADER")
        payload = decode_token(token)
        assert "exp" in payload
        # expiry must be roughly 8 hours in the future (allow ±10 s)
        assert abs(payload["exp"] - (int(time.time()) + 8 * 3600)) < 10

    def test_expired_token_raises_auth_error(self, monkeypatch):
        """Force expiry by signing with exp in the past."""
        import jwt as pyjwt

        secret = os.environ["SECRET_KEY"]
        stale_token = pyjwt.encode(
            {"user_id": 1, "role": "TRADER", "exp": int(time.time()) - 1},
            secret,
            algorithm="HS256",
        )
        with pytest.raises(AuthError, match="expired"):
            decode_token(stale_token)

    def test_tampered_signature_raises_auth_error(self):
        token = create_token(user_id=5, role="TRADER")
        tampered = token[:-4] + "XXXX"
        with pytest.raises(AuthError):
            decode_token(tampered)

    def test_random_string_raises_auth_error(self):
        with pytest.raises(AuthError):
            decode_token("not.a.token")

    def test_wrong_secret_raises_auth_error(self, monkeypatch):
        import jwt as pyjwt

        token_other_secret = pyjwt.encode(
            {"user_id": 9, "role": "TRADER", "exp": int(time.time()) + 3600},
            "wrong-secret",
            algorithm="HS256",
        )
        with pytest.raises(AuthError):
            decode_token(token_other_secret)


# ---------------------------------------------------------------------------
# Error handler mapping tests
# ---------------------------------------------------------------------------

def _make_app_with_route(exc_class):
    """Build a minimal FastAPI app that raises *exc_class* on GET /boom."""
    app = FastAPI()
    register_error_handlers(app)

    @app.get("/boom")
    async def boom():
        raise exc_class("test message")

    return TestClient(app, raise_server_exceptions=False)


class TestErrorHandlers:
    def test_validation_error_gives_400(self):
        client = _make_app_with_route(ValidationError)
        r = client.get("/boom")
        assert r.status_code == 400
        assert r.json()["error"]["code"] == "VALIDATION_ERROR"

    def test_auth_error_gives_401(self):
        client = _make_app_with_route(AuthError)
        r = client.get("/boom")
        assert r.status_code == 401
        assert r.json()["error"]["code"] == "UNAUTHENTICATED"

    def test_forbidden_error_gives_403(self):
        client = _make_app_with_route(ForbiddenError)
        r = client.get("/boom")
        assert r.status_code == 403
        assert r.json()["error"]["code"] == "FORBIDDEN"

    def test_not_found_error_gives_404(self):
        client = _make_app_with_route(NotFoundError)
        r = client.get("/boom")
        assert r.status_code == 404
        assert r.json()["error"]["code"] == "NOT_FOUND"

    def test_conflict_error_gives_409(self):
        client = _make_app_with_route(ConflictError)
        r = client.get("/boom")
        assert r.status_code == 409
        assert r.json()["error"]["code"] == "CONFLICT"

    def test_insufficient_data_gives_422(self):
        client = _make_app_with_route(InsufficientDataError)
        r = client.get("/boom")
        assert r.status_code == 422
        assert r.json()["error"]["code"] == "INSUFFICIENT_DATA"

    def test_unhandled_exception_gives_500_no_leak(self):
        """Generic exceptions must return 500 without exposing internals."""
        app = FastAPI()
        register_error_handlers(app)

        @app.get("/explode")
        async def explode():
            raise RuntimeError("internal secret database password xyz")

        client = TestClient(app, raise_server_exceptions=False)
        r = client.get("/explode")
        assert r.status_code == 500
        body = r.json()
        assert body["error"]["code"] == "INTERNAL_ERROR"
        assert "secret" not in body["error"]["message"]
        assert "xyz" not in body["error"]["message"]

    def test_fastapi_request_validation_remapped_to_400(self):
        """FastAPI's own 422 Unprocessable Entity must be remapped to 400."""
        from pydantic import BaseModel

        app = FastAPI()
        register_error_handlers(app)

        class Body(BaseModel):
            count: int

        @app.post("/items")
        async def items(body: Body):
            return body

        client = TestClient(app, raise_server_exceptions=False)
        # send a string where int is expected
        r = client.post("/items", json={"count": "not-a-number"})
        assert r.status_code == 400
        assert r.json()["error"]["code"] == "VALIDATION_ERROR"

    def test_error_envelope_shape(self):
        """Every error response must have exactly the error envelope keys."""
        client = _make_app_with_route(NotFoundError)
        r = client.get("/boom")
        body = r.json()
        assert set(body.keys()) == {"error"}
        assert set(body["error"].keys()) == {"code", "message"}
