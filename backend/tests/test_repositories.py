"""
Unit tests for Repositories.
Owned by Rishabh.
"""
from datetime import date
from app.domain import TradeRecord, MetricsResult
from app.models.user import User
from app.models.strategy import Strategy
from app.models.instrument import Instrument
from app.models.backtest_run import BacktestRun
from app.repositories.user_repository import UserRepository
from app.repositories.strategy_repository import StrategyRepository
from app.repositories.instrument_repository import InstrumentRepository
from app.repositories.backtest_run_repository import BacktestRunRepository
from app.repositories.metrics_repository import MetricsRepository

def test_user_repository(db_session):
    repo = UserRepository(db_session)
    u = User(name="Alice", email="alice@test.com", password_hash="hashed", role="TRADER")
    saved = repo.save(u)
    db_session.commit()

    assert saved.user_id is not None
    assert repo.find_by_email("alice@test.com") is not None
    assert repo.find_by_id(saved.user_id) is not None

def test_instrument_repository_coverage_and_prices(db_session):
    repo = InstrumentRepository(db_session)
    inst = Instrument(ticker="NVDA", name="Nvidia", asset_class="Equity")
    saved = repo.add(inst)
    db_session.commit()

    rows = [
        {"date": date(2024, 1, 1), "open": 100, "high": 105, "low": 95, "close": 102, "volume": 1000},
        {"date": date(2024, 1, 2), "open": 102, "high": 108, "low": 101, "close": 107, "volume": 1500},
        {"date": date(2024, 1, 3), "open": 107, "high": 110, "low": 106, "close": 109, "volume": 1200},
    ]
    inserted = repo.save_price_data(saved.instrument_id, rows)
    db_session.commit()
    assert inserted == 3

    # Coverage
    start_d, end_d, count = repo.coverage(saved.instrument_id)
    assert start_d == date(2024, 1, 1)
    assert end_d == date(2024, 1, 3)
    assert count == 3

    # Get price data
    df = repo.get_price_data(saved.instrument_id, date(2024, 1, 1), date(2024, 1, 2))
    assert len(df) == 2
    assert list(df.columns) == ["date", "open", "high", "low", "close", "volume"]

def test_backtest_run_and_metrics_repository(db_session):
    u_repo = UserRepository(db_session)
    u = u_repo.save(User(name="Bob", email="bob@test.com", password_hash="h", role="TRADER"))
    s_repo = StrategyRepository(db_session)
    s = s_repo.save(Strategy(user_id=u.user_id, strategy_type="MEAN_REVERSION", parameters={}))
    i_repo = InstrumentRepository(db_session)
    inst = i_repo.add(Instrument(ticker="AMZN", name="Amazon", asset_class="Equity"))
    db_session.commit()

    run_repo = BacktestRunRepository(db_session)
    run = BacktestRun(
        user_id=u.user_id,
        strategy_id=s.strategy_id,
        instrument_id=inst.instrument_id,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 10),
        status="COMPLETED",
    )
    trade = TradeRecord(
        entry_date=date(2024, 1, 2),
        exit_date=date(2024, 1, 5),
        entry_price=150.0,
        exit_price=160.0,
        quantity=10,
        pnl=100.0,
    )
    saved_run = run_repo.save(run, [trade])
    db_session.commit()

    assert saved_run.run_id is not None
    trades = run_repo.get_trades(saved_run.run_id)
    assert len(trades) == 1
    assert trades[0].pnl == 100.0

    metrics_repo = MetricsRepository(db_session)
    metrics_result = MetricsResult(
        sharpe_ratio=1.2,
        max_drawdown=-0.08,
        win_rate=1.0,
        cagr=0.15,
        total_return=0.10,
    )
    saved_m = metrics_repo.save(saved_run.run_id, metrics_result)
    db_session.commit()

    assert saved_m.metric_id is not None
    found_m = metrics_repo.find_by_run(saved_run.run_id)
    assert found_m.sharpe_ratio == 1.2
