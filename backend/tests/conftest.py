from datetime import date
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.models.base import Base
from app.models.user import User
from app.core.database import get_db
from app.core.security import hash_password, create_token
from app.main import app

@pytest.fixture(scope="function")
def db_engine():
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

    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session(db_engine):
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture(scope="function")
def client(db_engine):
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)

    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def seed_users(db_session):
    admin = User(
        name="Admin",
        email="admin@test.com",
        password_hash=hash_password("adminpassword123"),
        role="ADMIN",
    )
    trader = User(
        name="Trader",
        email="trader@test.com",
        password_hash=hash_password("traderpassword123"),
        role="TRADER",
    )
    db_session.add(admin)
    db_session.add(trader)
    db_session.commit()

    admin_token = create_token(admin.user_id, admin.role)
    trader_token = create_token(trader.user_id, trader.role)

    return {
        "admin": admin,
        "trader": trader,
        "admin_token": admin_token,
        "trader_token": trader_token,
    }
