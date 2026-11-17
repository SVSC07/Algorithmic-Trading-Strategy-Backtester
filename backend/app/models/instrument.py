# STUB, owned by Rishabh, replaced on merge
from sqlalchemy import Column, Integer, String
from app.models.base import Base

class Instrument(Base):
    __tablename__ = "instruments"

    instrument_id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    asset_class = Column(String, nullable=False)

    def __getitem__(self, item: str):
        return getattr(self, item)
