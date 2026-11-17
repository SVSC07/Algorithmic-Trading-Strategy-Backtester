from datetime import date, datetime
from typing import Optional, List, Dict, Any, Union
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.persistence.models import PriceData
from backend.persistence.repositories.base import BaseRepo, repo_method


def normalize_date(d: Union[date, str]) -> date:
    if isinstance(d, str):
        return datetime.strptime(d.strip(), "%Y-%m-%d").date()
    return d


class PriceRepo(BaseRepo):
    @repo_method
    def get_prices(
        self,
        instrument_id: int,
        start_date: Union[date, str],
        end_date: Union[date, str],
        session: Optional[Session] = None,
    ) -> List[Dict[str, Any]]:
        """Fetch historical price rows between start_date and end_date (inclusive), sorted ASC by date.

        Each dict: {date, open, high, low, close, volume}
        """
        start = normalize_date(start_date)
        end = normalize_date(end_date)

        with self.get_db(session) as s:
            stmt = (
                select(PriceData)
                .where(
                    PriceData.instrument_id == instrument_id,
                    PriceData.date >= start,
                    PriceData.date <= end,
                )
                .order_by(PriceData.date.asc())
            )
            records = s.execute(stmt).scalars().all()
            return [
                {
                    "date": r.date,
                    "open": float(r.open),
                    "high": float(r.high),
                    "low": float(r.low),
                    "close": float(r.close),
                    "volume": int(r.volume),
                }
                for r in records
            ]

    @repo_method
    def bulk_insert_prices(
        self,
        instrument_id: int,
        rows: List[Dict[str, Any]],
        session: Optional[Session] = None,
    ) -> int:
        """Insert price records in bulk. Returns count of inserted rows."""
        if not rows:
            return 0

        with self.get_db(session) as s:
            entities = []
            for r in rows:
                p_date = normalize_date(r["date"])
                entities.append(
                    PriceData(
                        instrument_id=instrument_id,
                        date=p_date,
                        open=float(r["open"]),
                        high=float(r["high"]),
                        low=float(r["low"]),
                        close=float(r["close"]),
                        volume=int(r["volume"]),
                    )
                )
            s.add_all(entities)
            s.flush()
            return len(entities)
