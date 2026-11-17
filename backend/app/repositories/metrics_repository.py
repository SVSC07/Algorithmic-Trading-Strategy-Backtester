# STUB — owned by Rishabh, replaced on merge
"""
repositories/metrics_repository.py
MetricsRepository stub.
"""
from typing import Optional

from sqlalchemy.orm import Session

from app.domain import MetricsResult
from app.models import Metrics


class MetricsRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, run_id: int, metrics: MetricsResult) -> Metrics:
        m = Metrics(
            run_id=run_id,
            sharpe_ratio=metrics.sharpe_ratio,
            max_drawdown=metrics.max_drawdown,
            win_rate=metrics.win_rate,
            cagr=metrics.cagr,
            total_return=metrics.total_return,
        )
        self._session.add(m)
        self._session.flush()
        return m

    def find_by_run(self, run_id: int) -> Optional[Metrics]:
        return self._session.query(Metrics).filter_by(run_id=run_id).first()
