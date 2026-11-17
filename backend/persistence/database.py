import os
from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

# Dev default to SQLite, configurable via DATABASE_URL (works with PostgreSQL as well)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///trading_backtester.db")

connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
)

# Enable SQLite foreign keys (PRAGMA foreign_keys=ON)
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    # Check if driver is sqlite
    if "sqlite" in str(type(dbapi_connection)).lower():
        cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_session() -> Generator[Session, None, None]:
    """Provide a transactional database session for FastAPI dependencies or context handling."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
