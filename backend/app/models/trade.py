# STUB, owned by Rishabh, replaced on merge
from sqlalchemy import Column, Integer, Float, Date, ForeignKey
from app.models.base import Base

class Trade(Base):
    __tablename__ = "trades"

    trade_id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(Integer, ForeignKey("backtest_runs.run_id", ondelete="CASCADE"), nullable=False)
    entry_date = Column(Date, nullable=False)
    exit_date = Column(Date, nullable=False)
    entry_price = Column(Float, nullable=False)
    exit_price = Column(Float, nullable=False)
    quantity = Column(Integer, nullable=False)
    pnl = Column(Float, nullable=False)
