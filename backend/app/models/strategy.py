# STUB, owned by Rishabh, replaced on merge
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from app.models.base import Base

class Strategy(Base):
    __tablename__ = "strategies"

    strategy_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    strategy_type = Column(String, nullable=False)
    parameters = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
