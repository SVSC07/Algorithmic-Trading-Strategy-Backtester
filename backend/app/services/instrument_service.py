"""
services/instrument_service.py
InstrumentService managing instruments and price ingestion.
"""
import csv
import io
from datetime import datetime, date as _date
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
        if not ticker or not name or not asset_class:
            raise ValidationError("ticker, name, and asset_class are required")

        clean_ticker = ticker.strip().upper()
        existing = next(
            (i for i in self._repo.list_all() if i.ticker.upper() == clean_ticker), None
        )
        if existing:
            raise ConflictError(f"Instrument with ticker '{clean_ticker}' already exists")

        inst = Instrument(ticker=clean_ticker, name=name.strip(), asset_class=asset_class.strip())
        self._repo.add(inst)
        self._session.commit()
        return inst

    def update_instrument(
        self, instrument_id: int, ticker: str, name: str, asset_class: str
    ) -> Instrument:
        inst = self._repo.find_by_id(instrument_id)
        if inst is None:
            raise NotFoundError(f"Instrument {instrument_id} not found")

        clean_ticker = ticker.strip().upper()
        if clean_ticker != inst.ticker.upper():
            existing = next(
                (i for i in self._repo.list_all() if i.ticker.upper() == clean_ticker and i.instrument_id != instrument_id), None
            )
            if existing:
                raise ConflictError(f"Instrument with ticker '{clean_ticker}' already exists")

        inst.ticker = clean_ticker
        inst.name = name.strip()
        inst.asset_class = asset_class.strip()
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

        try:
            content = csv_bytes.decode("utf-8")
        except UnicodeDecodeError:
            raise ValidationError("CSV file must be UTF-8 encoded")

        reader = csv.reader(io.StringIO(content))
        header = next(reader, None)
        if not header:
            raise ValidationError("CSV file is empty")

        clean_header = [h.strip().lower() for h in header]
        expected_standard = ["date", "open", "high", "low", "close", "volume"]
        expected_yahoo = ["date", "open", "high", "low", "close", "adj close", "volume"]
        is_yahoo = clean_header == expected_yahoo
        if clean_header != expected_standard and not is_yahoo:
            raise ValidationError("CSV header must be date,open,high,low,close,volume (or include adj close)")

        rows_to_insert: List[dict] = []
        errors: List[Dict[str, Any]] = []

        for row_num, row in enumerate(reader, start=2):
            if not row or all(c.strip() == "" for c in row):
                continue
            min_cols = 7 if is_yahoo else 6
            if len(row) < min_cols:
                errors.append({"row": row_num, "reason": f"Fewer than {min_cols} columns in row"})
                continue

            if is_yahoo:
                date_str, o_str, h_str, l_str, c_str, _, v_str = [cell.strip() for cell in row[:7]]
            else:
                date_str, o_str, h_str, l_str, c_str, v_str = [cell.strip() for cell in row[:6]]

            try:
                d_val = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                errors.append({"row": row_num, "reason": f"Invalid date format: {date_str}, expected YYYY-MM-DD"})
                continue

            try:
                open_val = float(o_str)
                high_val = float(h_str)
                low_val = float(l_str)
                close_val = float(c_str)
                vol_val = float(v_str)
            except ValueError:
                errors.append({"row": row_num, "reason": "Non-numeric price or volume value"})
                continue

            if open_val <= 0 or high_val <= 0 or low_val <= 0 or close_val <= 0 or vol_val < 0:
                errors.append({"row": row_num, "reason": "Prices must be positive and volume non-negative"})
                continue

            rows_to_insert.append({
                "date": d_val,
                "open": open_val,
                "high": high_val,
                "low": low_val,
                "close": close_val,
                "volume": vol_val,
            })

        inserted = self._repo.save_price_data(instrument_id, rows_to_insert)
        self._session.commit()
        skipped = len(errors) + (len(rows_to_insert) - inserted)
        return {"imported": inserted, "skipped": skipped, "errors": errors}
