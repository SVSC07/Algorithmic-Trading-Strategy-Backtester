from typing import Optional, List, Dict, Any
from sqlalchemy import select, func, delete
from sqlalchemy.orm import Session

from backend.persistence.models import Instrument, PriceData
from backend.persistence.repositories.base import BaseRepo, repo_method


class InstrumentRepo(BaseRepo):
    @repo_method
    def list_instruments(
        self,
        session: Optional[Session] = None,
    ) -> List[Dict[str, Any]]:
        """List all instruments, including data_start and data_end bounds from price data."""
        with self.get_db(session) as s:
            stmt = (
                select(
                    Instrument.id,
                    Instrument.symbol,
                    Instrument.name,
                    Instrument.exchange,
                    Instrument.sector,
                    func.min(PriceData.date).label("data_start"),
                    func.max(PriceData.date).label("data_end"),
                )
                .outerjoin(PriceData, Instrument.id == PriceData.instrument_id)
                .group_by(
                    Instrument.id,
                    Instrument.symbol,
                    Instrument.name,
                    Instrument.exchange,
                    Instrument.sector,
                )
                .order_by(Instrument.symbol.asc())
            )
            rows = s.execute(stmt).all()
            return [
                {
                    "id": r.id,
                    "symbol": r.symbol,
                    "name": r.name,
                    "exchange": r.exchange,
                    "sector": r.sector,
                    "data_start": r.data_start,
                    "data_end": r.data_end,
                }
                for r in rows
            ]

    @repo_method
    def get_instrument(
        self,
        id: int,
        session: Optional[Session] = None,
    ) -> Optional[Instrument]:
        """Fetch instrument by primary key ID or return None."""
        with self.get_db(session) as s:
            stmt = select(Instrument).where(Instrument.id == id)
            return s.execute(stmt).scalar_one_or_none()

    @repo_method
    def create_instrument(
        self,
        symbol: str,
        name: str,
        exchange: str,
        sector: Optional[str] = None,
        session: Optional[Session] = None,
    ) -> Instrument:
        """Create a new financial instrument."""
        with self.get_db(session) as s:
            instrument = Instrument(
                symbol=symbol.strip().upper(),
                name=name.strip(),
                exchange=exchange.strip().upper(),
                sector=sector.strip() if sector else None,
            )
            s.add(instrument)
            s.flush()
            s.refresh(instrument)
            return instrument

    @repo_method
    def delete_instrument(
        self,
        id: int,
        session: Optional[Session] = None,
    ) -> None:
        """Delete an instrument by ID (cascades to PriceData and BacktestRun)."""
        with self.get_db(session) as s:
            inst = s.get(Instrument, id)
            if inst:
                s.delete(inst)
                s.flush()
