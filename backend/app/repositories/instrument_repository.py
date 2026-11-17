# STUB — owned by Rishabh, replaced on merge
"""
repositories/instrument_repository.py
InstrumentRepository stub.
"""
from datetime import date
from typing import List, Optional, Tuple

import pandas as pd
from sqlalchemy.orm import Session

from app.models import Instrument, PriceData


class InstrumentRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, inst: Instrument) -> Instrument:
        self._session.add(inst)
        self._session.flush()
        return inst

    def update(self, inst: Instrument) -> Instrument:
        self._session.flush()
        return inst

    def remove(self, instrument_id: int) -> None:
        inst = self._session.query(Instrument).filter_by(instrument_id=instrument_id).first()
        if inst:
            self._session.delete(inst)

    def list_all(self) -> List[Instrument]:
        return self._session.query(Instrument).all()

    def find_by_id(self, instrument_id: int) -> Optional[Instrument]:
        return self._session.query(Instrument).filter_by(instrument_id=instrument_id).first()

    def find_by_ticker(self, ticker: str) -> Optional[Instrument]:
        return self._session.query(Instrument).filter(Instrument.ticker == ticker).first()

    def save_price_data(self, instrument_id: int, rows: List[dict]) -> int:
        """Insert rows, skip duplicates; return inserted count."""
        inserted = 0
        for row in rows:
            existing = (
                self._session.query(PriceData)
                .filter_by(instrument_id=instrument_id, date=row["date"])
                .first()
            )
            if existing is None:
                self._session.add(PriceData(instrument_id=instrument_id, **row))
                inserted += 1
        self._session.flush()
        return inserted

    def get_price_data(
        self, instrument_id: int, start: date, end: date
    ) -> pd.DataFrame:
        """Return DataFrame with columns date, open, high, low, close, volume, ascending by date."""
        rows = (
            self._session.query(PriceData)
            .filter(
                PriceData.instrument_id == instrument_id,
                PriceData.date >= start,
                PriceData.date <= end,
            )
            .order_by(PriceData.date)
            .all()
        )
        if not rows:
            return pd.DataFrame(columns=["date", "open", "high", "low", "close", "volume"])
        data = {
            "date": pd.to_datetime([r.date for r in rows]),
            "open": [r.open for r in rows],
            "high": [r.high for r in rows],
            "low": [r.low for r in rows],
            "close": [r.close for r in rows],
            "volume": [r.volume for r in rows],
        }
        return pd.DataFrame(data)

    def coverage(self, instrument_id: int) -> Tuple[Optional[date], Optional[date], int]:
        """Return (first_date, last_date, bar_count)."""
        rows = (
            self._session.query(PriceData)
            .filter_by(instrument_id=instrument_id)
            .order_by(PriceData.date)
            .all()
        )
        if not rows:
            return (None, None, 0)
        return (rows[0].date, rows[-1].date, len(rows))
