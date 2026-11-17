# STUB — owned by Rishabh, replaced on merge
"""
models/__init__.py
SQLAlchemy ORM models stub.
"""
from sqlalchemy import (
    JSON,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    user_id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    password_hash = Column(String, nullable=False)
    role = Column(String, CheckConstraint("role IN ('TRADER','ADMIN')"), default="TRADER")


class Strategy(Base):
    __tablename__ = "strategies"
    strategy_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    strategy_type = Column(String, nullable=False)
    parameters = Column(JSON, nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class Instrument(Base):
    __tablename__ = "instruments"
    instrument_id = Column(Integer, primary_key=True)
    ticker = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=False)
    asset_class = Column(String, nullable=False)


class PriceData(Base):
    __tablename__ = "price_data"
    price_id = Column(Integer, primary_key=True)
    instrument_id = Column(Integer, ForeignKey("instruments.instrument_id"), nullable=False)
    date = Column(Date, nullable=False)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Float)
    __table_args__ = (UniqueConstraint("instrument_id", "date"),)


class BacktestRun(Base):
    __tablename__ = "backtest_runs"
    run_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    strategy_id = Column(Integer, ForeignKey("strategies.strategy_id"), nullable=False)
    instrument_id = Column(Integer, ForeignKey("instruments.instrument_id"), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    status = Column(
        String,
        CheckConstraint("status IN ('PENDING','COMPLETED','FAILED','INSUFFICIENT_DATA')"),
        default="PENDING",
    )
    created_at = Column(DateTime, server_default=func.now())
    trades = relationship("Trade", back_populates="run", cascade="all, delete-orphan")
    metrics = relationship("Metrics", back_populates="run", uselist=False, cascade="all, delete-orphan")


class Trade(Base):
    __tablename__ = "trades"
    trade_id = Column(Integer, primary_key=True)
    run_id = Column(Integer, ForeignKey("backtest_runs.run_id", ondelete="CASCADE"), nullable=False)
    entry_date = Column(Date)
    exit_date = Column(Date)
    entry_price = Column(Float)
    exit_price = Column(Float)
    quantity = Column(Integer)
    pnl = Column(Float)
    run = relationship("BacktestRun", back_populates="trades")


class Metrics(Base):
    __tablename__ = "metrics"
    metric_id = Column(Integer, primary_key=True)
    run_id = Column(Integer, ForeignKey("backtest_runs.run_id", ondelete="CASCADE"), nullable=False, unique=True)
    sharpe_ratio = Column(Float)
    max_drawdown = Column(Float)
    win_rate = Column(Float)
    cagr = Column(Float)
    total_return = Column(Float)
    run = relationship("BacktestRun", back_populates="metrics")
