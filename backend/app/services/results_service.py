"""
services/results_service.py
ResultsService — get_run_detail, compare_runs, list_runs.

Contracts:
- get_run_detail: NotFoundError if run doesn't exist OR belongs to another user (same error).
- compare_runs: two RunDetails, both owned by user, ValidationError if run_a == run_b.
- list_runs: RunSummary list, newest first, with strategy_type, ticker, total_return.
"""
from datetime import date
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from app.domain import NotFoundError, TradeRecord, ValidationError
from app.repositories.backtest_run_repository import BacktestRunRepository
from app.repositories.instrument_repository import InstrumentRepository
from app.repositories.metrics_repository import MetricsRepository
from app.repositories.strategy_repository import StrategyRepository
from app.services.equity import build_equity_curve


def _fmt_date(d: Any) -> str | None:
    """Convert a date/datetime object to 'YYYY-MM-DD' string, or None."""
    if d is None:
        return None
    if hasattr(d, "strftime"):
        return d.strftime("%Y-%m-%d")
    return str(d)


def _instrument_shape(inst, coverage) -> Dict[str, Any]:
    """Build the Instrument response shape including coverage fields."""
    first, last, count = coverage
    return {
        "instrument_id": inst.instrument_id,
        "ticker": inst.ticker,
        "name": inst.name,
        "asset_class": inst.asset_class,
        "data_start": _fmt_date(first),
        "data_end": _fmt_date(last),
        "bar_count": count,
    }


def _strategy_shape(strategy) -> Dict[str, Any]:
    return {
        "strategy_id": strategy.strategy_id,
        "user_id": strategy.user_id,
        "strategy_type": strategy.strategy_type,
        "parameters": strategy.parameters,
        "created_at": _fmt_date(strategy.created_at),
    }


def _trade_shape(trade) -> Dict[str, Any]:
    return {
        "trade_id": trade.trade_id,
        "entry_date": _fmt_date(trade.entry_date),
        "exit_date": _fmt_date(trade.exit_date),
        "entry_price": trade.entry_price,
        "exit_price": trade.exit_price,
        "quantity": trade.quantity,
        "pnl": trade.pnl,
    }


class ResultsService:
    def __init__(
        self,
        session: Session,
        run_repo: BacktestRunRepository,
        strategy_repo: StrategyRepository,
        instrument_repo: InstrumentRepository,
        metrics_repo: MetricsRepository,
    ) -> None:
        self._session = session
        self._run_repo = run_repo
        self._strategy_repo = strategy_repo
        self._instrument_repo = instrument_repo
        self._metrics_repo = metrics_repo

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_run_detail(self, user_id: int, run_id: int) -> Dict[str, Any]:
        """
        Return the full RunDetail shape.

        Raises NotFoundError if the run doesn't exist or belongs to another user
        (same error for both — no information leakage).
        """
        run = self._run_repo.find_by_id(run_id)
        if run is None or run.user_id != user_id:
            raise NotFoundError(f"Run {run_id} not found")

        strategy = self._strategy_repo.find_by_id(run.strategy_id)
        instrument = self._instrument_repo.find_by_id(run.instrument_id)
        coverage = self._instrument_repo.coverage(run.instrument_id)
        metrics_row = self._metrics_repo.find_by_run(run_id)
        trade_rows = self._run_repo.get_trades(run_id)

        # Rebuild equity curve from stored price data and stored trades
        trade_records = [
            TradeRecord(
                entry_date=t.entry_date,
                exit_date=t.exit_date,
                entry_price=t.entry_price,
                exit_price=t.exit_price,
                quantity=t.quantity,
                pnl=t.pnl,
            )
            for t in trade_rows
        ]

        price_data = self._instrument_repo.get_price_data(
            run.instrument_id, run.start_date, run.end_date
        )
        equity_curve = build_equity_curve(price_data, trade_records)

        metrics_dict: Dict[str, Any] = {
            "sharpe_ratio": None,
            "max_drawdown": None,
            "win_rate": None,
            "cagr": None,
            "total_return": None,
        }
        if metrics_row is not None:
            metrics_dict = {
                "sharpe_ratio": metrics_row.sharpe_ratio,
                "max_drawdown": metrics_row.max_drawdown,
                "win_rate": metrics_row.win_rate,
                "cagr": metrics_row.cagr,
                "total_return": metrics_row.total_return,
            }

        return {
            "run": {
                "run_id": run.run_id,
                "user_id": run.user_id,
                "strategy_id": run.strategy_id,
                "instrument_id": run.instrument_id,
                "start_date": _fmt_date(run.start_date),
                "end_date": _fmt_date(run.end_date),
                "status": run.status,
                "created_at": _fmt_date(run.created_at),
            },
            "strategy": _strategy_shape(strategy) if strategy else None,
            "instrument": _instrument_shape(instrument, coverage) if instrument else None,
            "metrics": metrics_dict,
            "trades": [_trade_shape(t) for t in trade_rows],
            "equity_curve": [
                {"date": _fmt_date(pt.date), "equity": pt.equity}
                for pt in equity_curve
            ],
        }

    def compare_runs(
        self, user_id: int, run_a: int, run_b: int
    ) -> Dict[str, Any]:
        """
        Return {"run_a": RunDetail, "run_b": RunDetail}.

        Raises ValidationError if run_a == run_b.
        Raises NotFoundError if either run doesn't exist or isn't owned by user_id.
        """
        if run_a == run_b:
            raise ValidationError("Cannot compare a run with itself")
        return {
            "run_a": self.get_run_detail(user_id, run_a),
            "run_b": self.get_run_detail(user_id, run_b),
        }

    def list_runs(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Return a list of RunSummary dicts ordered newest first.

        Includes strategy_type, ticker, and total_return.
        """
        runs = self._run_repo.find_by_user(user_id)
        summaries = []
        for run in runs:
            strategy = self._strategy_repo.find_by_id(run.strategy_id)
            instrument = self._instrument_repo.find_by_id(run.instrument_id)
            metrics_row = self._metrics_repo.find_by_run(run.run_id)
            summaries.append(
                {
                    "run_id": run.run_id,
                    "strategy_id": run.strategy_id,
                    "strategy_type": strategy.strategy_type if strategy else None,
                    "instrument_id": run.instrument_id,
                    "ticker": instrument.ticker if instrument else None,
                    "start_date": _fmt_date(run.start_date),
                    "end_date": _fmt_date(run.end_date),
                    "status": run.status,
                    "total_return": metrics_row.total_return if metrics_row else None,
                    "created_at": _fmt_date(run.created_at),
                }
            )
        return summaries
