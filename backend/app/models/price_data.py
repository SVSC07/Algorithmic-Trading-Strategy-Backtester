# STUB, owned by Rishabh, replaced on merge
from sqlalchemy import Column, Integer, Float, Date, ForeignKey, UniqueConstraint, Index
from app.models.base import Base

class PriceData(Base):
    __tablename__ = "app_price_data"

    price_id = Column(Integer, primary_key=True, autoincrement=True)
    instrument_id = Column(Integer, ForeignKey("instruments.instrument_id"), nullable=False)
    date = Column(Date, nullable=False)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)

    __table_args__ = (
        UniqueConstraint("instrument_id", "date", name="uq_instrument_date"),
        Index("ix_price_data_instrument_date", "instrument_id", "date"),
    )
