from datetime import date
import pytest
from sqlalchemy import select
from backend.persistence.models import BacktestRun, Trade, PerformanceMetric, User, Instrument
from backend.persistence.repositories import (
    UserRepo,
    InstrumentRepo,
    PriceRepo,
    StrategyRepo,
    BacktestRepo,
)


def test_7_save_run_then_get_run_round_trip(db_session, sample_user, sample_strategy, sample_instrument):
    """Test 7: save_run then get_run returns identical data (round trip)."""
    backtest_repo = BacktestRepo(session=db_session)

    trades_payload = [
        {
            "entry_date": "2023-01-05",
            "entry_price": 150.0,
            "exit_date": "2023-01-10",
            "exit_price": 160.0,
            "quantity": 100.0,
            "pnl": 1000.0,
        },
        {
            "entry_date": "2023-01-12",
            "entry_price": 162.0,
            "exit_date": "2023-01-18",
            "exit_price": 158.0,
            "quantity": 50.0,
            "pnl": -200.0,
        },
    ]

    metrics_payload = {
        "total_return": 0.08,
        "cagr": 0.12,
        "sharpe_ratio": 1.45,
        "max_drawdown": -0.05,
        "win_rate": 0.50,
        "num_trades": 2,
    }

    run_id = backtest_repo.save_run(
        user_id=sample_user.id,
        strategy_id=sample_strategy.id,
        instrument_id=sample_instrument.id,
        start_date="2023-01-01",
        end_date="2023-01-31",
        initial_capital=10000.0,
        trades=trades_payload,
        metrics=metrics_payload,
        status="completed",
    )
    db_session.commit()

    assert isinstance(run_id, int)

    # Fetch run
    run_dict = backtest_repo.get_run(run_id)
    assert run_dict is not None
    assert run_dict["id"] == run_id
    assert run_dict["user_id"] == sample_user.id
    assert run_dict["strategy_id"] == sample_strategy.id
    assert run_dict["instrument_id"] == sample_instrument.id
    assert run_dict["start_date"] == date(2023, 1, 1)
    assert run_dict["end_date"] == date(2023, 1, 31)
    assert run_dict["initial_capital"] == 10000.0
    assert run_dict["status"] == "completed"

    # Verify trades
    assert len(run_dict["trades"]) == 2
    t0 = run_dict["trades"][0]
    assert t0["entry_date"] == date(2023, 1, 5)
    assert t0["entry_price"] == 150.0
    assert t0["exit_date"] == date(2023, 1, 10)
    assert t0["exit_price"] == 160.0
    assert t0["quantity"] == 100.0
    assert t0["pnl"] == 1000.0

    # Verify metrics (stored as decimals, max_drawdown is negative)
    metrics = run_dict["metrics"]
    assert metrics["total_return"] == 0.08
    assert metrics["cagr"] == 0.12
    assert metrics["sharpe_ratio"] == 1.45
    assert metrics["max_drawdown"] == -0.05
    assert metrics["win_rate"] == 0.50
    assert metrics["num_trades"] == 2


def test_7b_no_trades_metrics_contract(db_session, sample_user, sample_strategy, sample_instrument):
    """Never return None for metrics: no trades => num_trades=0, win_rate=0, sharpe_ratio=0."""
    backtest_repo = BacktestRepo(session=db_session)

    run_id = backtest_repo.save_run(
        user_id=sample_user.id,
        strategy_id=sample_strategy.id,
        instrument_id=sample_instrument.id,
        start_date="2023-01-01",
        end_date="2023-01-31",
        initial_capital=10000.0,
        trades=[],
        metrics={},  # Empty metrics
    )
    db_session.commit()

    run_dict = backtest_repo.get_run(run_id)
    assert run_dict["metrics"]["num_trades"] == 0
    assert run_dict["metrics"]["win_rate"] == 0.0
    assert run_dict["metrics"]["sharpe_ratio"] == 0.0
    assert run_dict["metrics"]["total_return"] == 0.0
    assert run_dict["metrics"]["cagr"] == 0.0
    assert run_dict["metrics"]["max_drawdown"] == 0.0


def test_8_save_run_rollback_on_metrics_failure(db_session, sample_user, sample_strategy, sample_instrument):
    """Test 8: save_run rolls back fully if the metrics insert fails."""
    backtest_repo = BacktestRepo(session=db_session)

    # max_drawdown > 0 violates check_metric_max_drawdown_non_positive CHECK constraint (max_drawdown <= 0.0)
    invalid_metrics = {
        "total_return": 0.15,
        "max_drawdown": 0.25,  # VIOLATION: max_drawdown must be negative or zero
        "win_rate": 0.6,
    }

    trades = [
        {
            "entry_date": "2023-01-05",
            "entry_price": 100.0,
            "exit_date": "2023-01-08",
            "exit_price": 105.0,
            "quantity": 10.0,
            "pnl": 50.0,
        }
    ]

    with pytest.raises(Exception):
        backtest_repo.save_run(
            user_id=sample_user.id,
            strategy_id=sample_strategy.id,
            instrument_id=sample_instrument.id,
            start_date="2023-01-01",
            end_date="2023-01-31",
            initial_capital=5000.0,
            trades=trades,
            metrics=invalid_metrics,
        )

    # Ensure transaction was completely rolled back: no BacktestRun and no Trades exist
    runs_in_db = db_session.execute(select(BacktestRun)).scalars().all()
    trades_in_db = db_session.execute(select(Trade)).scalars().all()
    metrics_in_db = db_session.execute(select(PerformanceMetric)).scalars().all()

    assert len(runs_in_db) == 0
    assert len(trades_in_db) == 0
    assert len(metrics_in_db) == 0


def test_9_get_prices_filtered_and_ordered_asc(db_session, sample_instrument):
    """Test 9: get_prices returns only rows in the date range, ordered ascending."""
    price_repo = PriceRepo(session=db_session)

    # Insert unordered dates
    price_repo.bulk_insert_prices(
        instrument_id=sample_instrument.id,
        rows=[
            {"date": "2023-01-20", "open": 100, "high": 105, "low": 99, "close": 104, "volume": 1000},
            {"date": "2023-01-05", "open": 90, "high": 95, "low": 89, "close": 94, "volume": 1000},
            {"date": "2023-01-15", "open": 95, "high": 98, "low": 94, "close": 97, "volume": 1000},
            {"date": "2023-01-10", "open": 92, "high": 96, "low": 91, "close": 95, "volume": 1000},
            {"date": "2023-01-02", "open": 88, "high": 91, "low": 87, "close": 89, "volume": 1000},
        ],
    )
    db_session.commit()

    # Query range 2023-01-05 to 2023-01-15
    results = price_repo.get_prices(
        instrument_id=sample_instrument.id,
        start_date="2023-01-05",
        end_date="2023-01-15",
    )

    assert len(results) == 3
    dates = [r["date"] for r in results]
    assert dates == [date(2023, 1, 5), date(2023, 1, 10), date(2023, 1, 15)]

    # Check dict structure
    assert "open" in results[0]
    assert "high" in results[0]
    assert "low" in results[0]
    assert "close" in results[0]
    assert "volume" in results[0]


def test_instrument_repo_bounds_and_strategy_repo(db_session, sample_user, sample_instrument):
    """Test InstrumentRepo.list_instruments data_start/data_end and StrategyRepo CRUD."""
    instrument_repo = InstrumentRepo(session=db_session)
    price_repo = PriceRepo(session=db_session)

    # Empty prices -> data_start and data_end are None
    inst_list = instrument_repo.list_instruments()
    assert len(inst_list) == 1
    assert inst_list[0]["symbol"] == "AAPL"
    assert inst_list[0]["data_start"] is None
    assert inst_list[0]["data_end"] is None

    # Add prices
    price_repo.bulk_insert_prices(
        instrument_id=sample_instrument.id,
        rows=[
            {"date": "2023-01-10", "open": 100, "high": 105, "low": 99, "close": 104, "volume": 1000},
            {"date": "2023-01-20", "open": 105, "high": 110, "low": 104, "close": 108, "volume": 1000},
        ],
    )
    db_session.commit()

    inst_list = instrument_repo.list_instruments()
    assert inst_list[0]["data_start"] == date(2023, 1, 10)
    assert inst_list[0]["data_end"] == date(2023, 1, 20)

    # StrategyRepo CRUD
    strategy_repo = StrategyRepo(session=db_session)
    strat = strategy_repo.create_strategy(
        user_id=sample_user.id,
        name="Mean Reversion Test",
        type="mean_reversion",
        parameters={"window": 14, "k": 1.5},
    )
    assert strat["name"] == "Mean Reversion Test"
    assert strat["parameters"]["window"] == 14
    assert strat["parameters"]["k"] == 1.5

    # Update strategy
    updated = strategy_repo.update_strategy(
        id=strat["id"],
        name="Mean Reversion Updated",
        parameters={"window": 20},
    )
    assert updated["name"] == "Mean Reversion Updated"
    assert updated["parameters"] == {"window": 20}
