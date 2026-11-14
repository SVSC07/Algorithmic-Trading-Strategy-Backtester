# STUB, owned by Rishabh, replaced on merge
from sqlalchemy.orm import Session
from app.domain import MetricsResult
from app.models.metric import Metric

class MetricsRepository:
    def __init__(self, session: Session):
        self.session = session

    def save(self, run_id: int, metrics: MetricsResult) -> Metric:
        metric = Metric(
            run_id=run_id,
            sharpe_ratio=float(metrics.sharpe_ratio),
            max_drawdown=float(metrics.max_drawdown),
            win_rate=float(metrics.win_rate),
            cagr=float(metrics.cagr),
            total_return=float(metrics.total_return),
        )
        self.session.add(metric)
        self.session.flush()
        return metric

    def find_by_run(self, run_id: int) -> Metric | None:
        return self.session.query(Metric).filter(Metric.run_id == run_id).first()
