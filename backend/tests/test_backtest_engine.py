"""
Unit tests for Backtest Engine orchestration and FR-10 sufficiency.
Owned by Shaurya.
"""
from datetime import date, timedelta
import pandas as pd
import pytest
from app.domain import ValidationError, NotFoundError, InsufficientDataError
from app.services.backtest_engine import BacktestEngine
from tests.fakes import (
    FakeSession,
    FakeStrategyRepository,
    FakeInstrumentRepository,
    FakeBacktestRunRepository,
    FakeMetricsRepository,
    FakeMetricsCalculator,
    FakeStrategy,
    FakeInstrument,
)

@pytest.fixture
def engine_setup():
    session = FakeSession()
    strategy_repo = FakeStrategyRepository()
    instrument_repo = FakeInstrumentRepository()
    run_repo = FakeBacktestRunRepository()
    metrics_repo = FakeMetricsRepository()
    calculator = FakeMetricsCalculator()

    engine = BacktestEngine(
        session=session,
        strategy_repo=strategy_repo,
        instrument_repo=instrument_repo,
        run_repo=run_repo,
        metrics_repo=metrics_repo,
        calculator=calculator,
    )

    return {
        "engine": engine,
        "strategy_repo": strategy_repo,
        "instrument_repo": instrument_repo,
        "run_repo": run_repo,
        "metrics_repo": metrics_repo,
        "session": session,
    }

def populate_prices(instrument_repo, inst_id: int, dates: list[date], closes: list[float]):
    rows = []
    for d, c in zip(dates, closes):
        rows.append({
            "date": d,
            "open": c,
            "high": c + 1.0,
            "low": max(0.5, c - 1.0),
            "close": c,
            "volume": 1000.0,
        })
    instrument_repo.save_price_data(inst_id, rows)

class TestBacktestEngine:
    def test_insufficient_data_no_bars_raises_and_no_run_row(self, engine_setup):
        """
        FR-10: Instrument has no bars in range -> raise InsufficientDataError, no run row created.
        """
        engine = engine_setup["engine"]
        s_repo = engine_setup["strategy_repo"]
        i_repo = engine_setup["instrument_repo"]
        r_repo = engine_setup["run_repo"]

        strat = s_repo.save(FakeStrategy(1, 100, "MOVING_AVERAGE_CROSSOVER", {"short_window": 2, "long_window": 5}))
        inst = i_repo.add(FakeInstrument(1, "AAPL", "Apple", "Equity"))

        with pytest.raises(InsufficientDataError):
            engine.run_backtest(
                user_id=100,
                strategy_id=strat.strategy_id,
                instrument_id=inst.instrument_id,
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 20),
                raise_on_insufficient_data=True,
            )

        # Confirm no run row created
        assert len(r_repo.runs) == 0

    def test_insufficient_data_status_mode_sets_insufficient_data_zero_trades(self, engine_setup):
        """
        FR-10 (Non-raising mode): Correctly setting status to INSUFFICIENT_DATA with 0 trades.
        """
        engine = engine_setup["engine"]
        s_repo = engine_setup["strategy_repo"]
        i_repo = engine_setup["instrument_repo"]
        r_repo = engine_setup["run_repo"]

        strat = s_repo.save(FakeStrategy(1, 100, "MOVING_AVERAGE_CROSSOVER", {"short_window": 2, "long_window": 5}))
        inst = i_repo.add(FakeInstrument(1, "AAPL", "Apple", "Equity"))

        # Empty data
        run_id = engine.run_backtest(
            user_id=100,
            strategy_id=strat.strategy_id,
            instrument_id=inst.instrument_id,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 20),
            raise_on_insufficient_data=False,
        )

        assert run_id in r_repo.runs
        run = r_repo.find_by_id(run_id)
        assert run.status == "INSUFFICIENT_DATA"
        # 0 trades created
        assert len(r_repo.get_trades(run_id)) == 0

    def test_insufficient_data_fewer_than_min_bars(self, engine_setup):
        """
        FR-10: bars in range are fewer than (long_window or lookback_period) + 2.
        For long_window=5, min_bars = 7. If only 5 bars exist, raise InsufficientDataError.
        """
        engine = engine_setup["engine"]
        s_repo = engine_setup["strategy_repo"]
        i_repo = engine_setup["instrument_repo"]

        strat = s_repo.save(FakeStrategy(1, 100, "MOVING_AVERAGE_CROSSOVER", {"short_window": 2, "long_window": 5}))
        inst = i_repo.add(FakeInstrument(1, "AAPL", "Apple", "Equity"))

        # Only 5 bars (requires at least 7)
        dates = [date(2024, 1, 1) + timedelta(days=i) for i in range(5)]
        populate_prices(i_repo, inst.instrument_id, dates, [100.0] * 5)

        with pytest.raises(InsufficientDataError):
            engine.run_backtest(
                user_id=100,
                strategy_id=strat.strategy_id,
                instrument_id=inst.instrument_id,
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 6),
                raise_on_insufficient_data=True,
            )

    def test_insufficient_data_date_boundary_gaps(self, engine_setup):
        """
        FR-10:
        First bar > 7 calendar days after start_date, OR
        Last bar > 7 calendar days before end_date.
        """
        engine = engine_setup["engine"]
        s_repo = engine_setup["strategy_repo"]
        i_repo = engine_setup["instrument_repo"]

        strat = s_repo.save(FakeStrategy(1, 100, "MOVING_AVERAGE_CROSSOVER", {"short_window": 2, "long_window": 3}))
        inst = i_repo.add(FakeInstrument(1, "AAPL", "Apple", "Equity"))

        # First bar on 2024-01-15 (more than 7 days after 2024-01-01)
        dates = [date(2024, 1, 15) + timedelta(days=i) for i in range(10)]
        populate_prices(i_repo, inst.instrument_id, dates, [100.0] * 10)

        with pytest.raises(InsufficientDataError):
            engine.run_backtest(
                user_id=100,
                strategy_id=strat.strategy_id,
                instrument_id=inst.instrument_id,
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 26),
            )

    def test_successful_moving_average_crossover_run_and_trades(self, engine_setup):
        """
        Full orchestration test:
        short_window=2, long_window=4
        Price series has 8 bars.
        Buy occurs on 2024-01-05 @ 14.0.
        Sell occurs on 2024-01-07 @ 6.0.
        initial_capital = 100,000.0
        quantity = floor(100,000 / 14.0) = 7142
        pnl = (6.0 - 14.0) * 7142 = -8.0 * 7142 = -57,136.0
        Final cash = 100,000 - 57,136 = 42,864.0
        """
        engine = engine_setup["engine"]
        s_repo = engine_setup["strategy_repo"]
        i_repo = engine_setup["instrument_repo"]
        r_repo = engine_setup["run_repo"]

        strat = s_repo.save(FakeStrategy(1, 100, "MOVING_AVERAGE_CROSSOVER", {"short_window": 2, "long_window": 4}))
        inst = i_repo.add(FakeInstrument(1, "AAPL", "Apple", "Equity"))

        dates = [date(2024, 1, 1) + timedelta(days=i) for i in range(8)]
        closes = [10.0, 10.0, 10.0, 10.0, 14.0, 14.0, 6.0, 6.0]
        populate_prices(i_repo, inst.instrument_id, dates, closes)

        run_id = engine.run_backtest(
            user_id=100,
            strategy_id=strat.strategy_id,
            instrument_id=inst.instrument_id,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 8),
        )

        run = r_repo.find_by_id(run_id)
        assert run.status == "COMPLETED"

        trades = r_repo.get_trades(run_id)
        assert len(trades) == 1
        t = trades[0]
        assert t.entry_date == date(2024, 1, 5)
        assert t.exit_date == date(2024, 1, 7)
        assert t.entry_price == 14.0
        assert t.exit_price == 6.0
        assert t.quantity == 7142
        assert t.pnl == pytest.approx(-57136.0)

    def test_open_position_closed_on_last_bar(self, engine_setup):
        """
        Rule 1: A position still open on the last bar is closed at that bar's close.
        Buy occurs on 2024-01-05 @ 14.0, never sells before end.
        Last bar is 2024-01-08 @ 20.0.
        Position must be closed at 2024-01-08 @ 20.0.
        """
        engine = engine_setup["engine"]
        s_repo = engine_setup["strategy_repo"]
        i_repo = engine_setup["instrument_repo"]
        r_repo = engine_setup["run_repo"]

        strat = s_repo.save(FakeStrategy(1, 100, "MOVING_AVERAGE_CROSSOVER", {"short_window": 2, "long_window": 4}))
        inst = i_repo.add(FakeInstrument(1, "AAPL", "Apple", "Equity"))

        dates = [date(2024, 1, 1) + timedelta(days=i) for i in range(8)]
        # Closes stay elevated so no SELL cross triggers
        closes = [10.0, 10.0, 10.0, 10.0, 14.0, 15.0, 16.0, 20.0]
        populate_prices(i_repo, inst.instrument_id, dates, closes)

        run_id = engine.run_backtest(
            user_id=100,
            strategy_id=strat.strategy_id,
            instrument_id=inst.instrument_id,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 8),
        )

        trades = r_repo.get_trades(run_id)
        assert len(trades) == 1
        t = trades[0]
        assert t.entry_date == date(2024, 1, 5)
        assert t.exit_date == date(2024, 1, 8)  # Closed on last bar!
        assert t.entry_price == 14.0
        assert t.exit_price == 20.0
        assert t.quantity == 7142
        assert t.pnl == pytest.approx((20.0 - 14.0) * 7142)

    def test_validation_start_date_ge_end_date(self, engine_setup):
        engine = engine_setup["engine"]
        with pytest.raises(ValidationError):
            engine.run_backtest(
                user_id=1,
                strategy_id=1,
                instrument_id=1,
                start_date=date(2024, 1, 10),
                end_date=date(2024, 1, 10),
            )

    def test_unowned_strategy_raises_not_found(self, engine_setup):
        engine = engine_setup["engine"]
        s_repo = engine_setup["strategy_repo"]
        i_repo = engine_setup["instrument_repo"]

        strat = s_repo.save(FakeStrategy(1, 999, "MEAN_REVERSION", {"lookback_period": 3, "threshold": 1.0}))
        inst = i_repo.add(FakeInstrument(1, "AAPL", "Apple", "Equity"))

        with pytest.raises(NotFoundError):
            engine.run_backtest(
                user_id=100,  # user_id 100 != 999
                strategy_id=strat.strategy_id,
                instrument_id=inst.instrument_id,
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 10),
            )
