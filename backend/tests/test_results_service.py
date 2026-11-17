"""
tests/test_results_service.py
Tests for ResultsService (Milestone 3).

Uses SQLite in-memory DB and in-memory fakes to avoid needing Postgres.
Tests verify: ownership checks, correct RunDetail/RunSummary shapes,
newest-first ordering, and a run with zero trades.
"""
import os
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest-only-at-least-32bytes")

from app.domain import NotFoundError, TradeRecord, ValidationError
from app.models import Base, BacktestRun, Instrument, Strategy, Trade, Metrics, User
from app.repositories.backtest_run_repository import BacktestRunRepository
from app.repositories.instrument_repository import InstrumentRepository
from app.repositories.metrics_repository import MetricsRepository
from app.repositories.strategy_repository import StrategyRepository
from app.services.results_service import ResultsService


# ---------------------------------------------------------------------------
# DB fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    s = Session()
    yield s
    s.close()
    Base.metadata.drop_all(engine)


# ---------------------------------------------------------------------------
# Helpers to seed test data
# ---------------------------------------------------------------------------

def _seed(session) -> Dict[str, Any]:
    """
    Seed a minimal dataset:
    - 2 users (user_id 1 and 2)
    - 1 strategy (owned by user 1)
    - 1 instrument with 10 price bars
    - 2 backtest runs (run_a newest, run_b older) for user 1
    - 1 run for user 2 (ownership test)
    - trades and metrics for run_a; zero trades for run_b
    Returns a dict of key objects.
    """
    # Users
    u1 = User(name="Alice", email="alice@test.com", password_hash="x", role="TRADER")
    u2 = User(name="Bob", email="bob@test.com", password_hash="x", role="TRADER")
    session.add_all([u1, u2])
    session.flush()

    # Strategy
    strat = Strategy(user_id=u1.user_id, strategy_type="MOVING_AVERAGE_CROSSOVER",
                     parameters={"short_window": 2, "long_window": 5})
    session.add(strat)
    session.flush()

    # Instrument
    inst = Instrument(ticker="TEST", name="Test Corp", asset_class="EQUITY")
    session.add(inst)
    session.flush()

    # Price data: 10 days starting 2023-01-02
    from app.models import PriceData
    for i in range(10):
        d = date(2023, 1, 2 + i)
        session.add(PriceData(
            instrument_id=inst.instrument_id, date=d,
            open=100.0 + i, high=105.0 + i, low=95.0 + i,
            close=100.0 + i, volume=1000.0,
        ))
    session.flush()

    # Run A (user 1, newer) with one trade and metrics
    run_a = BacktestRun(
        user_id=u1.user_id, strategy_id=strat.strategy_id,
        instrument_id=inst.instrument_id,
        start_date=date(2023, 1, 2), end_date=date(2023, 1, 11),
        status="COMPLETED", created_at=datetime(2023, 2, 1),
    )
    session.add(run_a)
    session.flush()
    trade_a = Trade(
        run_id=run_a.run_id, entry_date=date(2023, 1, 3), exit_date=date(2023, 1, 5),
        entry_price=102.0, exit_price=104.0, quantity=10, pnl=20.0,
    )
    session.add(trade_a)
    metrics_a = Metrics(
        run_id=run_a.run_id, sharpe_ratio=1.5, max_drawdown=-0.05,
        win_rate=1.0, cagr=0.1, total_return=0.02,
    )
    session.add(metrics_a)
    session.flush()

    # Run B (user 1, older) with zero trades and metrics
    run_b = BacktestRun(
        user_id=u1.user_id, strategy_id=strat.strategy_id,
        instrument_id=inst.instrument_id,
        start_date=date(2023, 1, 2), end_date=date(2023, 1, 11),
        status="COMPLETED", created_at=datetime(2023, 1, 1),
    )
    session.add(run_b)
    session.flush()
    metrics_b = Metrics(
        run_id=run_b.run_id, sharpe_ratio=0.0, max_drawdown=0.0,
        win_rate=0.0, cagr=0.0, total_return=0.0,
    )
    session.add(metrics_b)
    session.flush()

    # Run C (user 2 — ownership test)
    run_c = BacktestRun(
        user_id=u2.user_id, strategy_id=strat.strategy_id,
        instrument_id=inst.instrument_id,
        start_date=date(2023, 1, 2), end_date=date(2023, 1, 11),
        status="COMPLETED", created_at=datetime(2023, 1, 15),
    )
    session.add(run_c)
    session.flush()
    session.commit()

    return dict(
        u1=u1, u2=u2, strat=strat, inst=inst,
        run_a=run_a, run_b=run_b, run_c=run_c,
        trade_a=trade_a,
    )


@pytest.fixture
def svc_and_data(session):
    data = _seed(session)
    svc = ResultsService(
        session=session,
        run_repo=BacktestRunRepository(session),
        strategy_repo=StrategyRepository(session),
        instrument_repo=InstrumentRepository(session),
        metrics_repo=MetricsRepository(session),
    )
    return svc, data


# ---------------------------------------------------------------------------
# get_run_detail tests
# ---------------------------------------------------------------------------

class TestGetRunDetail:
    _RUNDETAIL_KEYS = {"run", "strategy", "instrument", "metrics", "trades", "equity_curve"}
    _RUN_KEYS = {"run_id", "user_id", "strategy_id", "instrument_id", "start_date",
                 "end_date", "status", "created_at"}
    _METRICS_KEYS = {"sharpe_ratio", "max_drawdown", "win_rate", "cagr", "total_return"}
    _TRADE_KEYS = {"trade_id", "entry_date", "exit_date", "entry_price", "exit_price", "quantity", "pnl"}
    _INSTRUMENT_KEYS = {"instrument_id", "ticker", "name", "asset_class", "data_start", "data_end", "bar_count"}
    _STRATEGY_KEYS = {"strategy_id", "user_id", "strategy_type", "parameters", "created_at"}

    def test_happy_path_shape_matches_contract(self, svc_and_data):
        svc, data = svc_and_data
        detail = svc.get_run_detail(data["u1"].user_id, data["run_a"].run_id)
        # Top-level keys
        assert set(detail.keys()) == self._RUNDETAIL_KEYS
        assert set(detail["run"].keys()) == self._RUN_KEYS
        assert set(detail["metrics"].keys()) == self._METRICS_KEYS
        assert set(detail["instrument"].keys()) == self._INSTRUMENT_KEYS
        assert set(detail["strategy"].keys()) == self._STRATEGY_KEYS

    def test_trade_shape(self, svc_and_data):
        svc, data = svc_and_data
        detail = svc.get_run_detail(data["u1"].user_id, data["run_a"].run_id)
        assert len(detail["trades"]) == 1
        assert set(detail["trades"][0].keys()) == self._TRADE_KEYS

    def test_equity_curve_has_points(self, svc_and_data):
        svc, data = svc_and_data
        detail = svc.get_run_detail(data["u1"].user_id, data["run_a"].run_id)
        assert len(detail["equity_curve"]) > 0
        for pt in detail["equity_curve"]:
            assert "date" in pt and "equity" in pt

    def test_own_run_other_user_raises_not_found(self, svc_and_data):
        """run_c belongs to u2 — u1 must get NotFoundError."""
        svc, data = svc_and_data
        with pytest.raises(NotFoundError):
            svc.get_run_detail(data["u1"].user_id, data["run_c"].run_id)

    def test_nonexistent_run_raises_not_found(self, svc_and_data):
        svc, data = svc_and_data
        with pytest.raises(NotFoundError):
            svc.get_run_detail(data["u1"].user_id, 99999)

    def test_zero_trades_run(self, svc_and_data):
        """run_b has no trades — must not raise, trades == []."""
        svc, data = svc_and_data
        detail = svc.get_run_detail(data["u1"].user_id, data["run_b"].run_id)
        assert detail["trades"] == []

    def test_metrics_values_correct(self, svc_and_data):
        svc, data = svc_and_data
        detail = svc.get_run_detail(data["u1"].user_id, data["run_a"].run_id)
        assert detail["metrics"]["total_return"] == 0.02
        assert detail["metrics"]["win_rate"] == 1.0

    def test_instrument_coverage_fields(self, svc_and_data):
        svc, data = svc_and_data
        detail = svc.get_run_detail(data["u1"].user_id, data["run_a"].run_id)
        inst = detail["instrument"]
        # We seeded 10 price bars
        assert inst["bar_count"] == 10
        assert inst["data_start"] is not None
        assert inst["data_end"] is not None


# ---------------------------------------------------------------------------
# compare_runs tests
# ---------------------------------------------------------------------------

class TestCompareRuns:
    def test_happy_path(self, svc_and_data):
        svc, data = svc_and_data
        result = svc.compare_runs(
            data["u1"].user_id, data["run_a"].run_id, data["run_b"].run_id
        )
        assert "run_a" in result and "run_b" in result
        assert result["run_a"]["run"]["run_id"] == data["run_a"].run_id
        assert result["run_b"]["run"]["run_id"] == data["run_b"].run_id

    def test_same_run_raises_validation_error(self, svc_and_data):
        svc, data = svc_and_data
        with pytest.raises(ValidationError):
            svc.compare_runs(data["u1"].user_id, data["run_a"].run_id, data["run_a"].run_id)

    def test_other_users_run_raises_not_found(self, svc_and_data):
        """run_c is owned by u2 — u1 must get NotFoundError."""
        svc, data = svc_and_data
        with pytest.raises(NotFoundError):
            svc.compare_runs(
                data["u1"].user_id, data["run_a"].run_id, data["run_c"].run_id
            )


# ---------------------------------------------------------------------------
# list_runs tests
# ---------------------------------------------------------------------------

class TestListRuns:
    _SUMMARY_KEYS = {
        "run_id", "strategy_id", "strategy_type", "instrument_id",
        "ticker", "start_date", "end_date", "status", "total_return", "created_at",
    }

    def test_returns_only_own_runs(self, svc_and_data):
        svc, data = svc_and_data
        summaries = svc.list_runs(data["u1"].user_id)
        ids = {s["run_id"] for s in summaries}
        assert data["run_a"].run_id in ids
        assert data["run_b"].run_id in ids
        assert data["run_c"].run_id not in ids

    def test_newest_first(self, svc_and_data):
        """run_a created_at=2023-02-01 > run_b created_at=2023-01-01."""
        svc, data = svc_and_data
        summaries = svc.list_runs(data["u1"].user_id)
        assert summaries[0]["run_id"] == data["run_a"].run_id
        assert summaries[1]["run_id"] == data["run_b"].run_id

    def test_summary_shape(self, svc_and_data):
        svc, data = svc_and_data
        summaries = svc.list_runs(data["u1"].user_id)
        for s in summaries:
            assert set(s.keys()) == self._SUMMARY_KEYS

    def test_strategy_type_and_ticker_filled(self, svc_and_data):
        svc, data = svc_and_data
        summaries = svc.list_runs(data["u1"].user_id)
        for s in summaries:
            assert s["strategy_type"] == "MOVING_AVERAGE_CROSSOVER"
            assert s["ticker"] == "TEST"

    def test_total_return_filled_for_completed_runs(self, svc_and_data):
        svc, data = svc_and_data
        summaries = svc.list_runs(data["u1"].user_id)
        run_a_summary = next(s for s in summaries if s["run_id"] == data["run_a"].run_id)
        assert run_a_summary["total_return"] == 0.02

    def test_no_runs_returns_empty_list(self, session):
        """A fresh user with no runs should get []."""
        u = User(name="Zara", email="zara@test.com", password_hash="x", role="TRADER")
        session.add(u)
        session.flush()
        svc = ResultsService(
            session=session,
            run_repo=BacktestRunRepository(session),
            strategy_repo=StrategyRepository(session),
            instrument_repo=InstrumentRepository(session),
            metrics_repo=MetricsRepository(session),
        )
        assert svc.list_runs(u.user_id) == []
