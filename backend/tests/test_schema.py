from datetime import date
import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select

from backend.persistence.models import (
    User,
    Instrument,
    PriceData,
    Strategy,
    BacktestRun,
    Trade,
    PerformanceMetric,
)
from backend.persistence.repositories import (
    InstrumentRepo,
    BacktestRepo,
)


def test_6_foreign_key_cascades(db_session, sample_user, sample_strategy, sample_instrument):
    """Test 6: Foreign keys cascade on delete.

    Deleting a BacktestRun deletes its Trades and PerformanceMetric;
    deleting an Instrument deletes its PriceData.
    """
    backtest_repo = BacktestRepo(session=db_session)
    instrument_repo = InstrumentRepo(session=db_session)

    # 1. Test BacktestRun cascade to Trades and PerformanceMetric
    run_id = backtest_repo.save_run(
        user_id=sample_user.id,
        strategy_id=sample_strategy.id,
        instrument_id=sample_instrument.id,
        start_date="2023-01-01",
        end_date="2023-01-31",
        initial_capital=10000.0,
        trades=[
            {
                "entry_date": "2023-01-05",
                "entry_price": 100.0,
                "exit_date": "2023-01-10",
                "exit_price": 110.0,
                "quantity": 10.0,
                "pnl": 100.0,
            }
        ],
        metrics={
            "total_return": 0.10,
            "cagr": 0.10,
            "sharpe_ratio": 1.2,
            "max_drawdown": -0.02,
            "win_rate": 1.0,
            "num_trades": 1,
        },
    )
    db_session.commit()

    # Confirm created
    trades_before = db_session.execute(select(Trade).where(Trade.run_id == run_id)).scalars().all()
    metrics_before = db_session.execute(
        select(PerformanceMetric).where(PerformanceMetric.run_id == run_id)
    ).scalars().all()
    assert len(trades_before) == 1
    assert len(metrics_before) == 1

    # Delete BacktestRun
    backtest_repo.delete_run(run_id)
    db_session.commit()

    # Confirm cascade deleted
    trades_after = db_session.execute(select(Trade).where(Trade.run_id == run_id)).scalars().all()
    metrics_after = db_session.execute(
        select(PerformanceMetric).where(PerformanceMetric.run_id == run_id)
    ).scalars().all()
    runs_after = db_session.execute(select(BacktestRun).where(BacktestRun.id == run_id)).scalars().all()

    assert len(runs_after) == 0
    assert len(trades_after) == 0
    assert len(metrics_after) == 0

    # 2. Test Instrument cascade to PriceData
    p = PriceData(
        instrument_id=sample_instrument.id,
        date=date(2023, 1, 5),
        open=150.0,
        high=155.0,
        low=149.0,
        close=154.0,
        volume=500000,
    )
    db_session.add(p)
    db_session.commit()

    prices_before = db_session.execute(
        select(PriceData).where(PriceData.instrument_id == sample_instrument.id)
    ).scalars().all()
    assert len(prices_before) == 1

    # Delete Instrument
    instrument_repo.delete_instrument(sample_instrument.id)
    db_session.commit()

    prices_after = db_session.execute(
        select(PriceData).where(PriceData.instrument_id == sample_instrument.id)
    ).scalars().all()
    assert len(prices_after) == 0


def test_10_unique_constraints(db_session, sample_user, sample_instrument):
    """Test 10: Unique constraints: duplicate username/symbol raises an error."""
    # 1. Duplicate username
    dup_user = User(
        username=sample_user.username,  # Duplicate!
        email="different_email@example.com",
        password_hash="pwd",
    )
    db_session.add(dup_user)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # 2. Duplicate email
    dup_email_user = User(
        username="unique_user_2",
        email=sample_user.email,  # Duplicate!
        password_hash="pwd",
    )
    db_session.add(dup_email_user)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # 3. Duplicate instrument symbol
    dup_inst = Instrument(
        symbol=sample_instrument.symbol,  # Duplicate!
        name="Apple Fake",
        exchange="NYSE",
    )
    db_session.add(dup_inst)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_schema_check_constraints(db_session, sample_instrument, sample_user, sample_strategy):
    """Verify CHECK constraints enforce 3NF data integrity."""
    # 1. Price > 0 constraint
    invalid_price = PriceData(
        instrument_id=sample_instrument.id,
        date=date(2023, 1, 10),
        open=-10.0,  # Negative open price
        high=100.0,
        low=90.0,
        close=95.0,
        volume=1000,
    )
    db_session.add(invalid_price)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # 2. High >= Low constraint
    invalid_high_low = PriceData(
        instrument_id=sample_instrument.id,
        date=date(2023, 1, 11),
        open=100.0,
        high=80.0,  # high < low!
        low=95.0,
        close=90.0,
        volume=1000,
    )
    db_session.add(invalid_high_low)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # 3. Volume >= 0 constraint
    invalid_vol = PriceData(
        instrument_id=sample_instrument.id,
        date=date(2023, 1, 12),
        open=100.0,
        high=105.0,
        low=95.0,
        close=102.0,
        volume=-100,  # Negative volume!
    )
    db_session.add(invalid_vol)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # 4. BacktestRun end_date > start_date
    invalid_run_dates = BacktestRun(
        user_id=sample_user.id,
        strategy_id=sample_strategy.id,
        instrument_id=sample_instrument.id,
        start_date=date(2023, 1, 31),
        end_date=date(2023, 1, 15),  # end_date before start_date!
        initial_capital=10000.0,
    )
    db_session.add(invalid_run_dates)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()
