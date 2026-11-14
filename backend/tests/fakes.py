from datetime import date
from typing import Optional
import pandas as pd
from app.domain import TradeRecord, MetricsResult

class FakeSession:
    """In-memory fake SQLAlchemy session."""
    def __init__(self):
        self.committed = False
        self.rolled_back = False

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def flush(self):
        pass

    def close(self):
        pass

class FakeUser:
    def __init__(self, user_id: int, name: str, email: str, password_hash: str, role: str):
        self.user_id = user_id
        self.name = name
        self.email = email
        self.password_hash = password_hash
        self.role = role

class FakeUserRepository:
    def __init__(self):
        self.users: dict[int, FakeUser] = {}
        self._next_id = 1

    def save(self, user):
        if not getattr(user, "user_id", None):
            user.user_id = self._next_id
            self._next_id += 1
        self.users[user.user_id] = user
        return user

    def find_by_email(self, email: str):
        for user in self.users.values():
            if user.email == email:
                return user
        return None

    def find_by_id(self, user_id: int):
        return self.users.get(user_id)

class FakeStrategy:
    def __init__(self, strategy_id: int, user_id: int, strategy_type: str, parameters: dict, created_at=None):
        self.strategy_id = strategy_id
        self.user_id = user_id
        self.strategy_type = strategy_type
        self.parameters = parameters
        self.created_at = created_at

class FakeStrategyRepository:
    def __init__(self):
        self.strategies: dict[int, FakeStrategy] = {}
        self._next_id = 1

    def save(self, strategy):
        if not getattr(strategy, "strategy_id", None):
            strategy.strategy_id = self._next_id
            self._next_id += 1
        self.strategies[strategy.strategy_id] = strategy
        return strategy

    def find_by_id(self, strategy_id: int):
        return self.strategies.get(strategy_id)

    def find_by_user(self, user_id: int):
        return [s for s in self.strategies.values() if s.user_id == user_id]

class FakeInstrument:
    def __init__(self, instrument_id: int, ticker: str, name: str, asset_class: str):
        self.instrument_id = instrument_id
        self.ticker = ticker
        self.name = name
        self.asset_class = asset_class

class FakeInstrumentRepository:
    def __init__(self):
        self.instruments: dict[int, FakeInstrument] = {}
        self.prices: dict[int, list[dict]] = {}
        self._next_id = 1

    def add(self, inst):
        if not getattr(inst, "instrument_id", None):
            inst.instrument_id = self._next_id
            self._next_id += 1
        self.instruments[inst.instrument_id] = inst
        if inst.instrument_id not in self.prices:
            self.prices[inst.instrument_id] = []
        return inst

    def update(self, inst):
        self.instruments[inst.instrument_id] = inst
        return inst

    def remove(self, instrument_id: int):
        self.instruments.pop(instrument_id, None)
        self.prices.pop(instrument_id, None)

    def list_all(self):
        return list(self.instruments.values())

    def find_by_id(self, instrument_id: int):
        return self.instruments.get(instrument_id)

    def save_price_data(self, instrument_id: int, rows: list[dict]) -> int:
        if instrument_id not in self.prices:
            self.prices[instrument_id] = []
        existing_dates = {r["date"] for r in self.prices[instrument_id]}
        count = 0
        for r in rows:
            if r["date"] not in existing_dates:
                self.prices[instrument_id].append(r)
                existing_dates.add(r["date"])
                count += 1
        return count

    def get_price_data(self, instrument_id: int, start: date, end: date) -> pd.DataFrame:
        rows = self.prices.get(instrument_id, [])
        filtered = [
            r for r in rows
            if start <= (r["date"].date() if hasattr(r["date"], "date") else r["date"]) <= end
        ]
        if not filtered:
            return pd.DataFrame(columns=["date", "open", "high", "low", "close", "volume"])
        df = pd.DataFrame(filtered)
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values(by="date", ascending=True).reset_index(drop=True)
        return df

    def coverage(self, instrument_id: int) -> tuple[Optional[date], Optional[date], int]:
        rows = self.prices.get(instrument_id, [])
        if not rows:
            return None, None, 0
        dates = sorted([r["date"].date() if hasattr(r["date"], "date") else r["date"] for r in rows])
        return dates[0], dates[-1], len(dates)

class FakeBacktestRun:
    def __init__(self, run_id: int, user_id: int, strategy_id: int, instrument_id: int, start_date: date, end_date: date, status: str, created_at=None):
        self.run_id = run_id
        self.user_id = user_id
        self.strategy_id = strategy_id
        self.instrument_id = instrument_id
        self.start_date = start_date
        self.end_date = end_date
        self.status = status
        self.created_at = created_at

class FakeTrade:
    def __init__(self, trade_id: int, run_id: int, entry_date: date, exit_date: date, entry_price: float, exit_price: float, quantity: int, pnl: float):
        self.trade_id = trade_id
        self.run_id = run_id
        self.entry_date = entry_date
        self.exit_date = exit_date
        self.entry_price = entry_price
        self.exit_price = exit_price
        self.quantity = quantity
        self.pnl = pnl

class FakeBacktestRunRepository:
    def __init__(self):
        self.runs: dict[int, FakeBacktestRun] = {}
        self.trades: dict[int, list[FakeTrade]] = {}
        self._next_run_id = 1
        self._next_trade_id = 1

    def save(self, run, trades: list[TradeRecord]):
        if not getattr(run, "run_id", None):
            run.run_id = self._next_run_id
            self._next_run_id += 1
        self.runs[run.run_id] = run
        self.trades[run.run_id] = []
        for t in trades:
            trade_obj = FakeTrade(
                trade_id=self._next_trade_id,
                run_id=run.run_id,
                entry_date=t.entry_date,
                exit_date=t.exit_date,
                entry_price=t.entry_price,
                exit_price=t.exit_price,
                quantity=t.quantity,
                pnl=t.pnl,
            )
            self._next_trade_id += 1
            self.trades[run.run_id].append(trade_obj)
        return run

    def find_by_id(self, run_id: int):
        return self.runs.get(run_id)

    def find_by_user(self, user_id: int):
        return sorted([r for r in self.runs.values() if r.user_id == user_id], key=lambda x: x.run_id, reverse=True)

    def get_trades(self, run_id: int) -> list[FakeTrade]:
        return self.trades.get(run_id, [])

class FakeMetric:
    def __init__(self, metric_id: int, run_id: int, sharpe_ratio: float, max_drawdown: float, win_rate: float, cagr: float, total_return: float):
        self.metric_id = metric_id
        self.run_id = run_id
        self.sharpe_ratio = sharpe_ratio
        self.max_drawdown = max_drawdown
        self.win_rate = win_rate
        self.cagr = cagr
        self.total_return = total_return

class FakeMetricsRepository:
    def __init__(self):
        self.metrics: dict[int, FakeMetric] = {}
        self._next_id = 1

    def save(self, run_id: int, metrics: MetricsResult):
        obj = FakeMetric(
            metric_id=self._next_id,
            run_id=run_id,
            sharpe_ratio=metrics.sharpe_ratio,
            max_drawdown=metrics.max_drawdown,
            win_rate=metrics.win_rate,
            cagr=metrics.cagr,
            total_return=metrics.total_return,
        )
        self._next_id += 1
        self.metrics[run_id] = obj
        return obj

    def find_by_run(self, run_id: int):
        return self.metrics.get(run_id)

class FakeMetricsCalculator:
    def calculate(self, trades: list[TradeRecord], run, equity_curve) -> MetricsResult:
        return MetricsResult(
            sharpe_ratio=1.5,
            max_drawdown=-0.05,
            win_rate=0.6,
            cagr=0.12,
            total_return=0.10,
        )
