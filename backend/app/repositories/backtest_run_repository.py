# STUB — owned by Rishabh, replaced on merge
"""
repositories/backtest_run_repository.py
BacktestRunRepository stub.
"""
from typing import List, Optional

from sqlalchemy.orm import Session

from app.domain import TradeRecord
from app.models import BacktestRun, Trade


class BacktestRunRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, run: BacktestRun, trades: List[TradeRecord]) -> BacktestRun:
        """Persist the run and its trades; flush but do not commit."""
        self._session.add(run)
        self._session.flush()
        for t in trades:
            self._session.add(
                Trade(
                    run_id=run.run_id,
                    entry_date=t.entry_date,
                    exit_date=t.exit_date,
                    entry_price=t.entry_price,
                    exit_price=t.exit_price,
                    quantity=t.quantity,
                    pnl=t.pnl,
                )
            )
        self._session.flush()
        return run

    def find_by_id(self, run_id: int) -> Optional[BacktestRun]:
        return self._session.query(BacktestRun).filter_by(run_id=run_id).first()

    def find_by_user(self, user_id: int) -> List[BacktestRun]:
        return (
            self._session.query(BacktestRun)
            .filter_by(user_id=user_id)
            .order_by(BacktestRun.created_at.desc())
            .all()
        )

    def get_trades(self, run_id: int) -> List[Trade]:
        return self._session.query(Trade).filter_by(run_id=run_id).all()
