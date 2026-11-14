"""
Unit tests for SQLAlchemy Models and DB Constraints.
Owned by Rishabh.
"""
from datetime import date
import pytest
from sqlalchemy.exc import IntegrityError
from app.models.user import User
from app.models.strategy import Strategy
from app.models.instrument import Instrument
from app.models.price_data import PriceData
from app.models.backtest_run import BacktestRun
from app.models.trade import Trade
from app.models.metric import Metric

def test_user_model_role_constraint(db_session):
    # Valid roles
    u1 = User(name="T1", email="t1@test.com", password_hash="hash", role="TRADER")
    u2 = User(name="A1", email="a1@test.com", password_hash="hash", role="ADMIN")
    db_session.add(u1)
    db_session.add(u2)
    db_session.commit()

    # Invalid role
    u3 = User(name="Bad", email="bad@test.com", password_hash="hash", role="SUPERUSER")
    db_session.add(u3)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

def test_price_data_unique_constraint(db_session):
    inst = Instrument(ticker="AAPL", name="Apple", asset_class="Equity")
    db_session.add(inst)
    db_session.commit()

    p1 = PriceData(instrument_id=inst.instrument_id, date=date(2024, 1, 1), open=10, high=11, low=9, close=10, volume=100)
    db_session.add(p1)
    db_session.commit()

    # Duplicate instrument_id + date
    p2 = PriceData(instrument_id=inst.instrument_id, date=date(2024, 1, 1), open=10, high=11, low=9, close=10, volume=200)
    db_session.add(p2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

def test_trade_cascade_delete(db_session):
    u = User(name="T", email="t@t.com", password_hash="h", role="TRADER")
    db_session.add(u)
    db_session.commit()

    s = Strategy(user_id=u.user_id, strategy_type="MEAN_REVERSION", parameters={})
    inst = Instrument(ticker="TSLA", name="Tesla", asset_class="Equity")
    db_session.add(s)
    db_session.add(inst)
    db_session.commit()

    run = BacktestRun(
        user_id=u.user_id,
        strategy_id=s.strategy_id,
        instrument_id=inst.instrument_id,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 10),
        status="COMPLETED",
    )
    db_session.add(run)
    db_session.commit()

    trade = Trade(
        run_id=run.run_id,
        entry_date=date(2024, 1, 2),
        exit_date=date(2024, 1, 5),
        entry_price=100.0,
        exit_price=110.0,
        quantity=50,
        pnl=500.0,
    )
    db_session.add(trade)
    db_session.commit()

    trade_id = trade.trade_id
    # Delete run should cascade delete trade
    db_session.delete(run)
    db_session.commit()

    assert db_session.query(Trade).filter(Trade.trade_id == trade_id).first() is None
