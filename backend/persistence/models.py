from datetime import datetime, date, timezone
from typing import Any, Dict
from sqlalchemy import (
    Column,
    Integer,
    BigInteger,
    Float,
    String,
    Date,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    Index,
    CheckConstraint,
)
from sqlalchemy.orm import relationship
from backend.persistence.database import Base


def utc_now() -> datetime:
    """Return timezone-aware current UTC datetime."""
    return datetime.now(timezone.utc)


class BaseModelMixin:
    """Helper mixin to support dict access and JSON-ready dict representations."""

    def to_dict(self) -> Dict[str, Any]:
        result = {}
        for col in self.__table__.columns:
            val = getattr(self, col.name)
            if isinstance(val, (datetime, date)):
                result[col.name] = val.isoformat()
            else:
                result[col.name] = val
        return result

    def __getitem__(self, item: str) -> Any:
        return getattr(self, item)


class User(Base, BaseModelMixin):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="trader")
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    __table_args__ = (
        CheckConstraint("role IN ('trader', 'admin')", name="check_user_role"),
    )

    strategies = relationship(
        "Strategy",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    backtest_runs = relationship(
        "BacktestRun",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"


class Instrument(Base, BaseModelMixin):
    __tablename__ = "instrument"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    exchange = Column(String(50), nullable=False)
    sector = Column(String(100), nullable=True)

    prices = relationship(
        "PriceData",
        back_populates="instrument",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    backtest_runs = relationship(
        "BacktestRun",
        back_populates="instrument",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"<Instrument(id={self.id}, symbol='{self.symbol}', exchange='{self.exchange}')>"


class PriceData(Base, BaseModelMixin):
    __tablename__ = "price_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    instrument_id = Column(
        Integer,
        ForeignKey("instrument.id", ondelete="CASCADE"),
        nullable=False,
    )
    date = Column(Date, nullable=False)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(BigInteger, nullable=False)

    __table_args__ = (
        UniqueConstraint("instrument_id", "date", name="uq_price_data_instrument_date"),
        Index("ix_price_data_instrument_date", "instrument_id", "date"),
        CheckConstraint("open > 0", name="check_price_data_open_positive"),
        CheckConstraint("high > 0", name="check_price_data_high_positive"),
        CheckConstraint("low > 0", name="check_price_data_low_positive"),
        CheckConstraint("close > 0", name="check_price_data_close_positive"),
        CheckConstraint("high >= low", name="check_price_data_high_ge_low"),
        CheckConstraint("volume >= 0", name="check_price_data_volume_non_negative"),
    )

    instrument = relationship("Instrument", back_populates="prices")

    def __repr__(self) -> str:
        return f"<PriceData(id={self.id}, instrument_id={self.instrument_id}, date={self.date}, close={self.close})>"


class Strategy(Base, BaseModelMixin):
    __tablename__ = "strategy"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer,
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
    )
    name = Column(String(100), nullable=False)
    type = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    __table_args__ = (
        CheckConstraint(
            "type IN ('moving_average_crossover', 'mean_reversion')",
            name="check_strategy_type",
        ),
    )

    user = relationship("User", back_populates="strategies")
    parameters = relationship(
        "StrategyParameter",
        back_populates="strategy",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    backtest_runs = relationship(
        "BacktestRun",
        back_populates="strategy",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"<Strategy(id={self.id}, name='{self.name}', type='{self.type}')>"


class StrategyParameter(Base, BaseModelMixin):
    __tablename__ = "strategy_parameter"

    id = Column(Integer, primary_key=True, autoincrement=True)
    strategy_id = Column(
        Integer,
        ForeignKey("strategy.id", ondelete="CASCADE"),
        nullable=False,
    )
    param_name = Column(String(100), nullable=False)
    param_value = Column(String(255), nullable=False)

    __table_args__ = (
        UniqueConstraint("strategy_id", "param_name", name="uq_strategy_parameter_strategy_param"),
    )

    strategy = relationship("Strategy", back_populates="parameters")

    def __repr__(self) -> str:
        return f"<StrategyParameter(strategy_id={self.strategy_id}, param_name='{self.param_name}', param_value='{self.param_value}')>"


class BacktestRun(Base, BaseModelMixin):
    __tablename__ = "backtest_run"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer,
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
    )
    strategy_id = Column(
        Integer,
        ForeignKey("strategy.id", ondelete="CASCADE"),
        nullable=False,
    )
    instrument_id = Column(
        Integer,
        ForeignKey("instrument.id", ondelete="CASCADE"),
        nullable=False,
    )
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    initial_capital = Column(Float, nullable=False)
    status = Column(String(20), nullable=False, default="completed")
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    __table_args__ = (
        CheckConstraint("end_date > start_date", name="check_backtest_run_date_range"),
        CheckConstraint("initial_capital > 0", name="check_backtest_run_initial_capital_positive"),
        CheckConstraint("status IN ('completed', 'failed')", name="check_backtest_run_status"),
    )

    user = relationship("User", back_populates="backtest_runs")
    strategy = relationship("Strategy", back_populates="backtest_runs")
    instrument = relationship("Instrument", back_populates="backtest_runs")
    trades = relationship(
        "Trade",
        back_populates="run",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    metric = relationship(
        "PerformanceMetric",
        back_populates="run",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"<BacktestRun(id={self.id}, strategy_id={self.strategy_id}, status='{self.status}')>"


class Trade(Base, BaseModelMixin):
    __tablename__ = "trade"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(
        Integer,
        ForeignKey("backtest_run.id", ondelete="CASCADE"),
        nullable=False,
    )
    entry_date = Column(Date, nullable=False)
    entry_price = Column(Float, nullable=False)
    exit_date = Column(Date, nullable=False)
    exit_price = Column(Float, nullable=False)
    quantity = Column(Float, nullable=False)
    pnl = Column(Float, nullable=False)

    __table_args__ = (
        CheckConstraint("entry_price > 0", name="check_trade_entry_price_positive"),
        CheckConstraint("exit_price > 0", name="check_trade_exit_price_positive"),
        CheckConstraint("quantity > 0", name="check_trade_quantity_positive"),
        CheckConstraint("exit_date >= entry_date", name="check_trade_exit_ge_entry_date"),
    )

    run = relationship("BacktestRun", back_populates="trades")

    def __repr__(self) -> str:
        return f"<Trade(id={self.id}, run_id={self.run_id}, pnl={self.pnl})>"


class PerformanceMetric(Base, BaseModelMixin):
    __tablename__ = "performance_metric"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(
        Integer,
        ForeignKey("backtest_run.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    total_return = Column(Float, nullable=False, default=0.0)
    cagr = Column(Float, nullable=False, default=0.0)
    sharpe_ratio = Column(Float, nullable=False, default=0.0)
    max_drawdown = Column(Float, nullable=False, default=0.0)
    win_rate = Column(Float, nullable=False, default=0.0)
    num_trades = Column(Integer, nullable=False, default=0)

    __table_args__ = (
        CheckConstraint("num_trades >= 0", name="check_metric_num_trades_non_negative"),
        CheckConstraint("win_rate >= 0.0 AND win_rate <= 1.0", name="check_metric_win_rate_range"),
        CheckConstraint("max_drawdown <= 0.0", name="check_metric_max_drawdown_non_positive"),
    )

    run = relationship("BacktestRun", back_populates="metric")

    def __repr__(self) -> str:
        return (
            f"<PerformanceMetric(run_id={self.run_id}, total_return={self.total_return}, "
            f"sharpe_ratio={self.sharpe_ratio}, num_trades={self.num_trades})>"
        )
