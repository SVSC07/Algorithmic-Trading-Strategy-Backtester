"""
tests/test_contract.py
Contract tests (Milestone 5) — verify every endpoint from the API contract is
registered in app.openapi(), /compare appears before /{id}, and status 422 is
only ever produced as INSUFFICIENT_DATA.
"""
import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ.setdefault("SECRET_KEY", "integration-test-secret-key-at-least-32-bytes")

from app.main import app
from app.models import Base
from app.api.deps import get_session


@pytest.fixture(scope="module")
def openapi_schema():
    """Retrieve the OpenAPI schema once for the whole module."""
    client = TestClient(app, raise_server_exceptions=False)
    r = client.get("/openapi.json")
    assert r.status_code == 200
    return r.json()


class TestRoutesExist:
    """Every path+method from the contract must exist in the OpenAPI schema."""

    _REQUIRED = [
        ("post",   "/api/auth/register"),
        ("post",   "/api/auth/login"),
        ("post",   "/api/strategies"),
        ("get",    "/api/strategies"),
        ("get",    "/api/instruments"),
        ("post",   "/api/instruments"),
        ("put",    "/api/instruments/{instrument_id}"),
        ("delete", "/api/instruments/{instrument_id}"),
        ("post",   "/api/instruments/{instrument_id}/prices"),
        ("post",   "/api/backtests"),
        ("get",    "/api/backtests"),
        ("get",    "/api/backtests/compare"),
        ("get",    "/api/backtests/{run_id}"),
        ("get",    "/health"),
    ]

    def test_all_contract_paths_exist(self, openapi_schema):
        paths = openapi_schema.get("paths", {})
        for method, path in self._REQUIRED:
            assert path in paths, f"Missing path: {path}"
            assert method in paths[path], (
                f"Missing method {method.upper()} on {path}"
            )

    def test_compare_registered_before_id(self, openapi_schema):
        """
        /api/backtests/compare must be declared before /api/backtests/{run_id}
        in the router so FastAPI routes /compare correctly.
        """
        paths = list(openapi_schema.get("paths", {}).keys())
        backtest_paths = [p for p in paths if p.startswith("/api/backtests")]
        compare_idx = next(
            (i for i, p in enumerate(backtest_paths) if p == "/api/backtests/compare"),
            None,
        )
        id_idx = next(
            (i for i, p in enumerate(backtest_paths) if "{" in p and "compare" not in p),
            None,
        )
        assert compare_idx is not None, "/api/backtests/compare not found"
        assert id_idx is not None, "/api/backtests/{run_id} not found"
        assert compare_idx < id_idx, (
            "/compare must appear before /{run_id} in the route table"
        )

    def test_422_only_means_insufficient_data(self):
        """
        Test that the application never returns a raw FastAPI 422; every 422
        it emits must have code INSUFFICIENT_DATA.
        """
        engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
        session = SessionLocal()

        def _override():
            yield session

        app.dependency_overrides[get_session] = _override
        client = TestClient(app, raise_server_exceptions=False)

        # Sending bad JSON should give 400, not 422
        r = client.post("/api/auth/register", json={"name": "X"})
        assert r.status_code == 400
        assert r.json()["error"]["code"] == "VALIDATION_ERROR"

        # Sending non-JSON should also give 400
        r = client.post(
            "/api/auth/register",
            content=b"not json",
            headers={"Content-Type": "application/json"},
        )
        assert r.status_code in (400, 422)
        if r.status_code == 422:
            # Must be INSUFFICIENT_DATA if we ever get 422
            assert r.json()["error"]["code"] == "INSUFFICIENT_DATA"

        app.dependency_overrides.pop(get_session, None)
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


def _make_test_client_with_db():
    """Helper: build an in-memory SQLite-backed TestClient."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session = SessionLocal()

    def _override():
        yield session

    app.dependency_overrides[get_session] = _override
    return TestClient(app, raise_server_exceptions=False), session, engine


class TestStatusCodes:
    def test_register_201(self):
        client, session, engine = _make_test_client_with_db()
        try:
            r = client.post("/api/auth/register", json={
                "name": "T", "email": "t@t.com", "password": "password123",
            })
            assert r.status_code == 201
        finally:
            app.dependency_overrides.pop(get_session, None)
            session.close()
            Base.metadata.drop_all(engine)
            engine.dispose()

    def test_login_200(self):
        from app.models import User
        from app.core.security import hash_password

        client, session, engine = _make_test_client_with_db()
        try:
            session.add(User(
                name="L", email="l@l.com",
                password_hash=hash_password("loginpass1"), role="TRADER",
            ))
            session.commit()
            r = client.post("/api/auth/login", json={
                "email": "l@l.com", "password": "loginpass1",
            })
            assert r.status_code == 200
        finally:
            app.dependency_overrides.pop(get_session, None)
            session.close()
            Base.metadata.drop_all(engine)
            engine.dispose()
