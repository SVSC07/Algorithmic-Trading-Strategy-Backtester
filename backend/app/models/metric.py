# STUB, owned by Rishabh, replaced on merge
from sqlalchemy import Column, Integer, Float, ForeignKey
from app.models.base import Base

class Metric(Base):
    __tablename__ = "metrics"

    metric_id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(Integer, ForeignKey("backtest_runs.run_id", ondelete="CASCADE"), unique=True, nullable=False)
    sharpe_ratio = Column(Float, nullable=False)
    max_drawdown = Column(Float, nullable=False)
    win_rate = Column(Float, nullable=False)
    cagr = Column(Float, nullable=False)
    total_return = Column(Float, nullable=False)
