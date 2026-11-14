# STUB, owned by Molik, replaced on merge
from app.domain import NotFoundError, TradeRecord
from app.services.equity import build_equity_curve

def _format_date(d) -> str | None:
    if d is None:
        return None
    if hasattr(d, "isoformat"):
        return d.isoformat()[:10]
    return str(d)[:10]

def _format_datetime(dt) -> str | None:
    if dt is None:
        return None
    if hasattr(dt, "isoformat"):
        return dt.isoformat()
    return str(dt)

class ResultsService:
    def __init__(self, session, run_repo, strategy_repo, instrument_repo, metrics_repo):
        self.session = session
        self.run_repo = run_repo
        self.strategy_repo = strategy_repo
        self.instrument_repo = instrument_repo
        self.metrics_repo = metrics_repo

    def list_runs(self, user_id: int) -> list[dict]:
        runs = self.run_repo.find_by_user(user_id)
        results = []
        for r in runs:
            strat = self.strategy_repo.find_by_id(r.strategy_id)
            inst = self.instrument_repo.find_by_id(r.instrument_id)
            metric = self.metrics_repo.find_by_run(r.run_id) if self.metrics_repo else None

            results.append({
                "run_id": r.run_id,
                "strategy_id": r.strategy_id,
                "strategy_type": strat.strategy_type if strat else "UNKNOWN",
                "instrument_id": r.instrument_id,
                "ticker": inst.ticker if inst else "UNKNOWN",
                "start_date": _format_date(r.start_date),
                "end_date": _format_date(r.end_date),
                "status": r.status,
                "total_return": float(metric.total_return) if metric else 0.0,
                "created_at": _format_datetime(r.created_at),
            })
        return results

    def get_run_detail(self, user_id: int, run_id: int) -> dict:
        run = self.run_repo.find_by_id(run_id)
        if not run or run.user_id != user_id:
            raise NotFoundError("Backtest run not found")

        strategy = self.strategy_repo.find_by_id(run.strategy_id)
        instrument = self.instrument_repo.find_by_id(run.instrument_id)
        metric = self.metrics_repo.find_by_run(run.run_id) if self.metrics_repo else None
        trades = self.run_repo.get_trades(run_id)

        # Coverage for instrument
        cov_start, cov_end, bar_count = self.instrument_repo.coverage(run.instrument_id)

        # Build equity curve
        trade_records = [
            TradeRecord(
                entry_date=t.entry_date,
                exit_date=t.exit_date,
                entry_price=t.entry_price,
                exit_price=t.exit_price,
                quantity=t.quantity,
                pnl=t.pnl,
            )
            for t in trades
        ]
        price_data = self.instrument_repo.get_price_data(run.instrument_id, run.start_date, run.end_date)
        curve = build_equity_curve(price_data, trade_records, initial_capital=100000.0)

        return {
            "run": {
                "run_id": run.run_id,
                "user_id": run.user_id,
                "strategy_id": run.strategy_id,
                "instrument_id": run.instrument_id,
                "start_date": _format_date(run.start_date),
                "end_date": _format_date(run.end_date),
                "status": run.status,
                "created_at": _format_datetime(run.created_at),
            },
            "strategy": {
                "strategy_id": strategy.strategy_id,
                "user_id": strategy.user_id,
                "strategy_type": strategy.strategy_type,
                "parameters": strategy.parameters,
                "created_at": _format_datetime(strategy.created_at),
            } if strategy else {},
            "instrument": {
                "instrument_id": instrument.instrument_id,
                "ticker": instrument.ticker,
                "name": instrument.name,
                "asset_class": instrument.asset_class,
                "data_start": _format_date(cov_start),
                "data_end": _format_date(cov_end),
                "bar_count": bar_count,
            } if instrument else {},
            "metrics": {
                "sharpe_ratio": float(metric.sharpe_ratio) if metric else 0.0,
                "max_drawdown": float(metric.max_drawdown) if metric else 0.0,
                "win_rate": float(metric.win_rate) if metric else 0.0,
                "cagr": float(metric.cagr) if metric else 0.0,
                "total_return": float(metric.total_return) if metric else 0.0,
            },
            "trades": [
                {
                    "trade_id": t.trade_id,
                    "entry_date": _format_date(t.entry_date),
                    "exit_date": _format_date(t.exit_date),
                    "entry_price": float(t.entry_price),
                    "exit_price": float(t.exit_price),
                    "quantity": int(t.quantity),
                    "pnl": float(t.pnl),
                }
                for t in trades
            ],
            "equity_curve": [
                {
                    "date": _format_date(pt.date),
                    "equity": float(pt.equity),
                }
                for pt in curve
            ],
        }

    def compare_runs(self, user_id: int, run_a: int, run_b: int) -> dict:
        detail_a = self.get_run_detail(user_id, run_a)
        detail_b = self.get_run_detail(user_id, run_b)
        return {
            "run_a": detail_a,
            "run_b": detail_b,
        }
