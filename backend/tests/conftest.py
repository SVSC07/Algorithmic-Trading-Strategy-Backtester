"""
tests/conftest.py
Shared pytest fixtures for all test modules (persistence and API/integration).
"""
import io
import os
import sys
from datetime import date, timedelta
from typing import Generator

# Ensure backend and project root are on sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
root_dir = os.path.abspath(os.path.join(backend_dir, ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

os.environ.setdefault("SECRET_KEY", "integration-test-secret-key-at-least-32-bytes")

# Import app Base and models
from app.main import app
from app.api.deps import get_session
from app.models import Base as AppBase, User as AppUser
from app.core.security import hash_password, create_token

# Import persistence Base and models if present
try:
    from backend.persistence.models import (
        Base as PersistenceBase,
        User as PersistenceUser,
        Instrument as PersistenceInstrument,
        Strategy as PersistenceStrategy,
    )
except ImportError:
    PersistenceBase = None
    PersistenceUser = None
    PersistenceInstrument = None
    PersistenceStrategy = None


def _create_engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    AppBase.metadata.create_all(bind=engine)
    if PersistenceBase is not None:
        PersistenceBase.metadata.create_all(bind=engine)

    return engine


@pytest.fixture(scope="function")
def db_engine():
    """Create a SQLite in-memory engine with all tables created."""
    engine = _create_engine()
    yield engine
    AppBase.metadata.drop_all(bind=engine)
    if PersistenceBase is not None:
        PersistenceBase.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine) -> Generator[Session, None, None]:
    """Provide a transactional database session for tests & set FastAPI get_session override."""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = SessionLocal()

    def _override():
        yield session

    app.dependency_overrides[get_session] = _override
    yield session
    app.dependency_overrides.pop(get_session, None)
    session.close()


@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """TestClient backed by db_session."""
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


@pytest.fixture(scope="function")
def seeded_users(db_session: Session):
    """Seed ADMIN + TRADER users for API integration tests."""
    admin = AppUser(
        name="Admin",
        email="admin@test.com",
        password_hash=hash_password("adminpass1"),
        role="ADMIN",
    )
    trader = AppUser(
        name="Trader",
        email="trader@test.com",
        password_hash=hash_password("traderpass1"),
        role="TRADER",
    )
    db_session.add_all([admin, trader])
    db_session.commit()
    db_session.refresh(admin)
    db_session.refresh(trader)
    admin_token = create_token(admin.user_id, "ADMIN")
    trader_token = create_token(trader.user_id, "TRADER")
    return admin_token, trader_token, admin, trader


# Persistence fixtures
@pytest.fixture
def sample_user(db_session):
    if PersistenceUser is None:
        return None
    user = PersistenceUser(
        username="test_trader",
        email="test_trader@example.com",
        password_hash="hashed_pw_secret",
        role="trader",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def sample_instrument(db_session):
    if PersistenceInstrument is None:
        return None
    inst = PersistenceInstrument(
        symbol="AAPL",
        name="Apple Inc.",
        exchange="NASDAQ",
        sector="Technology",
    )
    db_session.add(inst)
    db_session.commit()
    db_session.refresh(inst)
    return inst


@pytest.fixture
def sample_strategy(db_session, sample_user):
    if PersistenceStrategy is None:
        return None
    strat = PersistenceStrategy(
        user_id=sample_user.id,
        name="SMA Crossover Test",
        type="moving_average_crossover",
    )
    db_session.add(strat)
    db_session.commit()
    db_session.refresh(strat)
    return strat


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def make_price_csv(n_days: int = 60, start_price: float = 100.0) -> bytes:
    """Generate n_days of synthetic weekday-only OHLCV CSV data."""
    rows = ["date,open,high,low,close,volume"]
    d = date(2023, 1, 2)
    price = start_price
    count = 0
    while count < n_days:
        if d.weekday() < 5:
            close = round(price + (count % 5) - 2, 2)
            rows.append(f"{d},{price},{close + 1},{price - 1},{close},1000")
            price = close
            count += 1
        d += timedelta(days=1)
    return "\n".join(rows).encode()
