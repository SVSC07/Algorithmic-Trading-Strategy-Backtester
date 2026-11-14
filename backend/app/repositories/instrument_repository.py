# STUB, owned by Rishabh, replaced on merge
from datetime import date
from typing import Optional
import pandas as pd
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.instrument import Instrument
from app.models.price_data import PriceData

def _to_date(val) -> date:
    if hasattr(val, "date") and callable(val.date):
        return val.date()
    if isinstance(val, date):
        return val
    return pd.to_datetime(val).date()

class InstrumentRepository:
    def __init__(self, session: Session):
        self.session = session

    def add(self, inst: Instrument) -> Instrument:
        self.session.add(inst)
        self.session.flush()
        return inst

    def update(self, inst: Instrument) -> Instrument:
        self.session.add(inst)
        self.session.flush()
        return inst

    def remove(self, instrument_id: int) -> None:
        inst = self.find_by_id(instrument_id)
        if inst:
            self.session.query(PriceData).filter(PriceData.instrument_id == instrument_id).delete()
            self.session.delete(inst)
            self.session.flush()

    def list_all(self) -> list[Instrument]:
        return self.session.query(Instrument).order_by(Instrument.ticker.asc()).all()

    def find_by_id(self, instrument_id: int) -> Instrument | None:
        return self.session.query(Instrument).filter(Instrument.instrument_id == instrument_id).first()

    def find_by_ticker(self, ticker: str) -> Instrument | None:
        return self.session.query(Instrument).filter(Instrument.ticker == ticker).first()

    def save_price_data(self, instrument_id: int, rows: list[dict]) -> int:
        if not rows:
            return 0

        # Query existing dates for this instrument to avoid duplicates
        existing_dates_q = self.session.query(PriceData.date).filter(PriceData.instrument_id == instrument_id).all()
        existing_dates = {d[0] for d in existing_dates_q}

        inserted = 0
        for r in rows:
            row_date = _to_date(r["date"])
            if row_date in existing_dates:
                continue

            record = PriceData(
                instrument_id=instrument_id,
                date=row_date,
                open=float(r["open"]),
                high=float(r["high"]),
                low=float(r["low"]),
                close=float(r["close"]),
                volume=float(r["volume"]),
            )
            self.session.add(record)
            existing_dates.add(row_date)
            inserted += 1

        self.session.flush()
        return inserted

    def get_price_data(self, instrument_id: int, start: date, end: date) -> pd.DataFrame:
        start_date = _to_date(start)
        end_date = _to_date(end)

        records = (
            self.session.query(PriceData)
            .filter(
                PriceData.instrument_id == instrument_id,
                PriceData.date >= start_date,
                PriceData.date <= end_date,
            )
            .order_by(PriceData.date.asc())
            .all()
        )

        if not records:
            return pd.DataFrame(columns=["date", "open", "high", "low", "close", "volume"])

        data = [
            {
                "date": r.date,
                "open": r.open,
                "high": r.high,
                "low": r.low,
                "close": r.close,
                "volume": r.volume,
            }
            for r in records
        ]
        df = pd.DataFrame(data)
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values(by="date", ascending=True).reset_index(drop=True)
        return df

    def coverage(self, instrument_id: int) -> tuple[Optional[date], Optional[date], int]:
        result = (
            self.session.query(
                func.min(PriceData.date),
                func.max(PriceData.date),
                func.count(PriceData.price_id),
            )
            .filter(PriceData.instrument_id == instrument_id)
            .one_or_none()
        )

        if not result or result[2] == 0:
            return None, None, 0

        return result[0], result[1], int(result[2])
