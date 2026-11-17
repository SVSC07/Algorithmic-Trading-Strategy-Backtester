# STUB — owned by Rishabh, replaced on merge
"""
services/instrument_service.py
InstrumentService stub.
"""
import csv
import io
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from app.domain import ConflictError, NotFoundError, ValidationError
from app.models import BacktestRun, Instrument
from app.repositories.instrument_repository import InstrumentRepository


class InstrumentService:
    def __init__(self, session: Session, instrument_repo: InstrumentRepository) -> None:
        self._session = session
        self._repo = instrument_repo

    def list_instruments(self) -> List[Instrument]:
        return self._repo.list_all()

    def create_instrument(self, ticker: str, name: str, asset_class: str) -> Instrument:
        existing = next(
            (i for i in self._repo.list_all() if i.ticker == ticker), None
        )
        if existing:
            raise ConflictError(f"Ticker '{ticker}' already exists")
        inst = Instrument(ticker=ticker, name=name, asset_class=asset_class)
        self._repo.add(inst)
        self._session.commit()
        return inst

    def update_instrument(
        self, instrument_id: int, ticker: str, name: str, asset_class: str
    ) -> Instrument:
        inst = self._repo.find_by_id(instrument_id)
        if inst is None:
            raise NotFoundError(f"Instrument {instrument_id} not found")
        inst.ticker = ticker
        inst.name = name
        inst.asset_class = asset_class
        self._repo.update(inst)
        self._session.commit()
        return inst

    def delete_instrument(self, instrument_id: int) -> None:
        inst = self._repo.find_by_id(instrument_id)
        if inst is None:
            raise NotFoundError(f"Instrument {instrument_id} not found")
        # Check referential integrity
        in_use = (
            self._session.query(BacktestRun)
            .filter_by(instrument_id=instrument_id)
            .first()
        )
        if in_use:
            raise ConflictError(f"Instrument {instrument_id} is referenced by backtest runs")
        self._repo.remove(instrument_id)
        self._session.commit()

    def import_prices(
        self, instrument_id: int, csv_bytes: bytes
    ) -> Dict[str, Any]:
        """
        Parse CSV with header date,open,high,low,close,volume and import rows.
        Returns {"imported": int, "skipped": int, "errors": [{"row": int, "reason": str}]}.
        """
        inst = self._repo.find_by_id(instrument_id)
        if inst is None:
            raise NotFoundError(f"Instrument {instrument_id} not found")

        text = csv_bytes.decode("utf-8", errors="replace")
        reader = csv.DictReader(io.StringIO(text))

        REQUIRED = {"date", "open", "high", "low", "close", "volume"}
        if reader.fieldnames is None or not REQUIRED.issubset(set(reader.fieldnames)):
            raise ValidationError(
                "CSV must have header: date,open,high,low,close,volume"
            )

        rows_to_insert: List[dict] = []
        errors: List[Dict[str, Any]] = []
        from datetime import date as _date

        for row_num, row in enumerate(reader, start=2):  # row 1 = header
            try:
                d = _date.fromisoformat(row["date"].strip())
                r = {
                    "date": d,
                    "open": float(row["open"]),
                    "high": float(row["high"]),
                    "low": float(row["low"]),
                    "close": float(row["close"]),
                    "volume": float(row["volume"]),
                }
                rows_to_insert.append(r)
            except (ValueError, KeyError) as exc:
                errors.append({"row": row_num, "reason": str(exc)})

        inserted = self._repo.save_price_data(instrument_id, rows_to_insert)
        skipped = len(rows_to_insert) - inserted
        self._session.commit()
        return {"imported": inserted, "skipped": skipped, "errors": errors}
