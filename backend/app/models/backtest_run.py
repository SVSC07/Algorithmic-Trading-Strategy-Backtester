# STUB, owned by Rishabh, replaced on merge
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, Date, DateTime, String, ForeignKey, CheckConstraint
from app.models.base import Base

class BacktestRun(Base):
    __tablename__ = "backtest_runs"

    run_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    strategy_id = Column(Integer, ForeignKey("strategies.strategy_id"), nullable=False)
    instrument_id = Column(Integer, ForeignKey("instruments.instrument_id"), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    status = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        CheckConstraint(
            "status IN ('PENDING', 'COMPLETED', 'FAILED', 'INSUFFICIENT_DATA')",
            name="check_run_status",
        ),
    )
