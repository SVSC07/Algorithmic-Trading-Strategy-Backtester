import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.persistence.models import Base, User, Instrument, Strategy


@pytest.fixture
def db_engine():
    """Create a SQLite in-memory engine with PRAGMA foreign_keys enabled."""
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
    engine.dispose()


@pytest.fixture
def db_session(db_engine):
    """Provide a transactional database session for tests."""
    Session = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def sample_user(db_session):
    user = User(
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
    inst = Instrument(
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
    strat = Strategy(
        user_id=sample_user.id,
        name="SMA Crossover Test",
        type="moving_average_crossover",
    )
    db_session.add(strat)
    db_session.commit()
    db_session.refresh(strat)
    return strat
