"""Initial 3NF schema for Algorithmic Trading Strategy Backtester.

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-10-26 19:50:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. User
    op.create_table(
        "user",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False, server_default="trader"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("role IN ('trader', 'admin')", name="check_user_role"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("username"),
    )
    op.create_index("ix_user_email", "user", ["email"], unique=True)
    op.create_index("ix_user_username", "user", ["username"], unique=True)

    # 2. Instrument
    op.create_table(
        "instrument",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("symbol", sa.String(length=20), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("exchange", sa.String(length=50), nullable=False),
        sa.Column("sector", sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("symbol"),
    )
    op.create_index("ix_instrument_symbol", "instrument", ["symbol"], unique=True)

    # 3. PriceData
    op.create_table(
        "price_data",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("instrument_id", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("open", sa.Float(), nullable=False),
        sa.Column("high", sa.Float(), nullable=False),
        sa.Column("low", sa.Float(), nullable=False),
        sa.Column("close", sa.Float(), nullable=False),
        sa.Column("volume", sa.BigInteger(), nullable=False),
        sa.CheckConstraint("open > 0", name="check_price_data_open_positive"),
        sa.CheckConstraint("high > 0", name="check_price_data_high_positive"),
        sa.CheckConstraint("low > 0", name="check_price_data_low_positive"),
        sa.CheckConstraint("close > 0", name="check_price_data_close_positive"),
        sa.CheckConstraint("high >= low", name="check_price_data_high_ge_low"),
        sa.CheckConstraint("volume >= 0", name="check_price_data_volume_non_negative"),
        sa.ForeignKeyConstraint(["instrument_id"], ["instrument.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("instrument_id", "date", name="uq_price_data_instrument_date"),
    )
    op.create_index("ix_price_data_instrument_date", "price_data", ["instrument_id", "date"])

    # 4. Strategy
    op.create_table(
        "strategy",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "type IN ('moving_average_crossover', 'mean_reversion')",
            name="check_strategy_type",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # 5. StrategyParameter
    op.create_table(
        "strategy_parameter",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("strategy_id", sa.Integer(), nullable=False),
        sa.Column("param_name", sa.String(length=100), nullable=False),
        sa.Column("param_value", sa.String(length=255), nullable=False),
        sa.ForeignKeyConstraint(["strategy_id"], ["strategy.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("strategy_id", "param_name", name="uq_strategy_parameter_strategy_param"),
    )

    # 6. BacktestRun
    op.create_table(
        "backtest_run",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("strategy_id", sa.Integer(), nullable=False),
        sa.Column("instrument_id", sa.Integer(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("initial_capital", sa.Float(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="completed"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("end_date > start_date", name="check_backtest_run_date_range"),
        sa.CheckConstraint("initial_capital > 0", name="check_backtest_run_initial_capital_positive"),
        sa.CheckConstraint("status IN ('completed', 'failed')", name="check_backtest_run_status"),
        sa.ForeignKeyConstraint(["instrument_id"], ["instrument.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["strategy_id"], ["strategy.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # 7. Trade
    op.create_table(
        "trade",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("run_id", sa.Integer(), nullable=False),
        sa.Column("entry_date", sa.Date(), nullable=False),
        sa.Column("entry_price", sa.Float(), nullable=False),
        sa.Column("exit_date", sa.Date(), nullable=False),
        sa.Column("exit_price", sa.Float(), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("pnl", sa.Float(), nullable=False),
        sa.CheckConstraint("entry_price > 0", name="check_trade_entry_price_positive"),
        sa.CheckConstraint("exit_price > 0", name="check_trade_exit_price_positive"),
        sa.CheckConstraint("quantity > 0", name="check_trade_quantity_positive"),
        sa.CheckConstraint("exit_date >= entry_date", name="check_trade_exit_ge_entry_date"),
        sa.ForeignKeyConstraint(["run_id"], ["backtest_run.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # 8. PerformanceMetric
    op.create_table(
        "performance_metric",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("run_id", sa.Integer(), nullable=False),
        sa.Column("total_return", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("cagr", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("sharpe_ratio", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("max_drawdown", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("win_rate", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("num_trades", sa.Integer(), nullable=False, server_default="0"),
        sa.CheckConstraint("num_trades >= 0", name="check_metric_num_trades_non_negative"),
        sa.CheckConstraint("win_rate >= 0.0 AND win_rate <= 1.0", name="check_metric_win_rate_range"),
        sa.CheckConstraint("max_drawdown <= 0.0", name="check_metric_max_drawdown_non_positive"),
        sa.ForeignKeyConstraint(["run_id"], ["backtest_run.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("run_id"),
    )


def downgrade() -> None:
    op.drop_table("performance_metric")
    op.drop_table("trade")
    op.drop_table("backtest_run")
    op.drop_table("strategy_parameter")
    op.drop_table("strategy")
    op.drop_index("ix_price_data_instrument_date", table_name="price_data")
    op.drop_table("price_data")
    op.drop_index("ix_instrument_symbol", table_name="instrument")
    op.drop_table("instrument")
    op.drop_index("ix_user_username", table_name="user")
    op.drop_index("ix_user_email", table_name="user")
    op.drop_table("user")
