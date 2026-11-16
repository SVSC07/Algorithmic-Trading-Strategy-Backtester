from datetime import date, datetime
from typing import Optional, List, Dict, Any, Union
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from backend.persistence.models import BacktestRun, Trade, PerformanceMetric
from backend.persistence.repositories.base import BaseRepo, repo_method


def normalize_date(d: Union[date, str]) -> date:
    if isinstance(d, str):
        return datetime.strptime(d.strip(), "%Y-%m-%d").date()
    return d


def format_run_dict(run: BacktestRun) -> Dict[str, Any]:
    metric = run.metric
    return {
        "id": run.id,
        "user_id": run.user_id,
        "strategy_id": run.strategy_id,
        "instrument_id": run.instrument_id,
        "start_date": run.start_date,
        "end_date": run.end_date,
        "initial_capital": float(run.initial_capital),
        "status": run.status,
        "created_at": run.created_at,
        "trades": [
            {
                "id": t.id,
                "run_id": t.run_id,
                "entry_date": t.entry_date,
                "entry_price": float(t.entry_price),
                "exit_date": t.exit_date,
                "exit_price": float(t.exit_price),
                "quantity": float(t.quantity),
                "pnl": float(t.pnl),
            }
            for t in run.trades
        ],
        "metrics": {
            "total_return": float(metric.total_return) if metric else 0.0,
            "cagr": float(metric.cagr) if metric else 0.0,
            "sharpe_ratio": float(metric.sharpe_ratio) if metric else 0.0,
            "max_drawdown": float(metric.max_drawdown) if metric else 0.0,
            "win_rate": float(metric.win_rate) if metric else 0.0,
            "num_trades": int(metric.num_trades) if metric else 0,
        },
    }


class BacktestRepo(BaseRepo):
    @repo_method
    def save_run(
        self,
        user_id: int,
        strategy_id: int,
        instrument_id: int,
        start_date: Union[date, str],
        end_date: Union[date, str],
        initial_capital: float,
        trades: List[Dict[str, Any]],
        metrics: Dict[str, Any],
        status: str = "completed",
        session: Optional[Session] = None,
    ) -> int:
        """Save run + trades + metrics in ONE atomic transaction (all or nothing).

        Rolls back fully if any step (including metrics insert) fails.
        Returns the created run_id.
        """
        start = normalize_date(start_date)
        end = normalize_date(end_date)

        with self.get_db(session) as s:
            try:
                # 1. BacktestRun record
                run = BacktestRun(
                    user_id=user_id,
                    strategy_id=strategy_id,
                    instrument_id=instrument_id,
                    start_date=start,
                    end_date=end,
                    initial_capital=float(initial_capital),
                    status=status,
                )
                s.add(run)
                s.flush()  # Populates run.id

                # 2. Trade records
                for t in trades:
                    trade_row = Trade(
                        run_id=run.id,
                        entry_date=normalize_date(t["entry_date"]),
                        entry_price=float(t["entry_price"]),
                        exit_date=normalize_date(t["exit_date"]),
                        exit_price=float(t["exit_price"]),
                        quantity=float(t["quantity"]),
                        pnl=float(t["pnl"]),
                    )
                    s.add(trade_row)

                # 3. PerformanceMetric record
                num_trades = metrics.get("num_trades", len(trades))
                metric_row = PerformanceMetric(
                    run_id=run.id,
                    total_return=float(metrics.get("total_return", 0.0)),
                    cagr=float(metrics.get("cagr", 0.0)),
                    sharpe_ratio=float(metrics.get("sharpe_ratio", 0.0)),
                    max_drawdown=float(metrics.get("max_drawdown", 0.0)),
                    win_rate=float(metrics.get("win_rate", 0.0)),
                    num_trades=int(num_trades),
                )
                s.add(metric_row)

                s.flush()
                return run.id

            except Exception:
                s.rollback()
                raise

    @repo_method
    def get_run(
        self,
        run_id: int,
        session: Optional[Session] = None,
    ) -> Optional[Dict[str, Any]]:
        """Fetch backtest run by ID with trades and metrics, matching the API result object."""
        with self.get_db(session) as s:
            stmt = (
                select(BacktestRun)
                .options(
                    selectinload(BacktestRun.trades),
                    selectinload(BacktestRun.metric),
                )
                .where(BacktestRun.id == run_id)
            )
            run = s.execute(stmt).scalar_one_or_none()
            if not run:
                return None
            return format_run_dict(run)

    @repo_method
    def list_runs(
        self,
        user_id: int,
        session: Optional[Session] = None,
    ) -> List[Dict[str, Any]]:
        """List all backtest runs for a user with their trades and metrics."""
        with self.get_db(session) as s:
            stmt = (
                select(BacktestRun)
                .options(
                    selectinload(BacktestRun.trades),
                    selectinload(BacktestRun.metric),
                )
                .where(BacktestRun.user_id == user_id)
                .order_by(BacktestRun.id.desc())
            )
            runs = s.execute(stmt).scalars().all()
            return [format_run_dict(r) for r in runs]

    @repo_method
    def delete_run(
        self,
        run_id: int,
        session: Optional[Session] = None,
    ) -> None:
        """Delete backtest run by ID (cascades to trades and metrics)."""
        with self.get_db(session) as s:
            run = s.get(BacktestRun, run_id)
            if run:
                s.delete(run)
                s.flush()
