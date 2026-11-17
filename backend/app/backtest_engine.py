# STUB — owned by Shaurya, replaced on merge
"""
backtest_engine.py
BacktestEngine stub — real implementation owned by Shaurya.
"""
from datetime import date
from typing import Optional

from sqlalchemy.orm import Session

from app.domain import InsufficientDataError, NotFoundError, TradeRecord
from app.models import BacktestRun
from app.repositories.backtest_run_repository import BacktestRunRepository
from app.repositories.instrument_repository import InstrumentRepository
from app.repositories.metrics_repository import MetricsRepository
from app.repositories.strategy_repository import StrategyRepository
from app.services.equity import build_equity_curve
from app.services.metrics_calculator import MetricsCalculator


class BacktestEngine:
    """
    Minimal stub — raises InsufficientDataError when no data exists for the range.
    Real logic (strategy execution, signal generation) is Shaurya's responsibility.
    """

    def __init__(
        self,
        session: Session,
        strategy_repo: StrategyRepository,
        instrument_repo: InstrumentRepository,
        run_repo: BacktestRunRepository,
        metrics_repo: MetricsRepository,
        calculator: MetricsCalculator,
    ) -> None:
        self._session = session
        self._strategy_repo = strategy_repo
        self._instrument_repo = instrument_repo
        self._run_repo = run_repo
        self._metrics_repo = metrics_repo
        self._calculator = calculator

    def run_backtest(
        self,
        user_id: int,
        strategy_id: int,
        instrument_id: int,
        start_date: date,
        end_date: date,
    ) -> int:
        """
        Run a backtest and return the run_id.

        FR-10: raises InsufficientDataError (no row created) if no bars exist in range.
        """
        strategy = self._strategy_repo.find_by_id(strategy_id)
        if strategy is None or strategy.user_id != user_id:
            raise NotFoundError("Strategy not found")

        instrument = self._instrument_repo.find_by_id(instrument_id)
        if instrument is None:
            raise NotFoundError("Instrument not found")

        price_data = self._instrument_repo.get_price_data(instrument_id, start_date, end_date)

        # FR-10: no bars in range → InsufficientDataError, no run row created
        if price_data.empty:
            raise InsufficientDataError("No price data in the specified date range")

        # Determine minimum bar requirement from strategy parameters
        params = strategy.parameters or {}
        min_bars = max(
            params.get("long_window", 0) or 0,
            params.get("lookback_period", 0) or 0,
        ) + 2
        if len(price_data) < min_bars:
            raise InsufficientDataError(
                f"Insufficient price data: need at least {min_bars} bars"
            )

        # FR-10: first / last bar boundary checks (7 calendar-day tolerance)
        import pandas as pd
        first_bar: date = price_data.iloc[0]["date"].date() if hasattr(price_data.iloc[0]["date"], "date") else price_data.iloc[0]["date"]
        last_bar: date = price_data.iloc[-1]["date"].date() if hasattr(price_data.iloc[-1]["date"], "date") else price_data.iloc[-1]["date"]
        if (first_bar - start_date).days > 7:
            raise InsufficientDataError("First bar is more than 7 calendar days after start_date")
        if (end_date - last_bar).days > 7:
            raise InsufficientDataError("Last bar is more than 7 calendar days before end_date")

        # Stub: no actual signal generation — produces zero trades
        trades: list[TradeRecord] = []

        # Persist run
        run = BacktestRun(
            user_id=user_id,
            strategy_id=strategy_id,
            instrument_id=instrument_id,
            start_date=start_date,
            end_date=end_date,
            status="COMPLETED",
        )
        self._run_repo.save(run, trades)

        # Build equity curve and compute metrics
        equity_curve = build_equity_curve(price_data, trades)
        metrics_result = self._calculator.calculate(trades, run, equity_curve)
        self._metrics_repo.save(run.run_id, metrics_result)
        self._session.commit()

        return run.run_id
