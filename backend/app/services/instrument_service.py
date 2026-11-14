# STUB, owned by Rishabh, replaced on merge
import csv
import io
from datetime import datetime
from app.domain import ValidationError, NotFoundError, ConflictError
from app.models.instrument import Instrument
from app.models.backtest_run import BacktestRun

def _format_date(d) -> str | None:
    if d is None:
        return None
    if hasattr(d, "isoformat"):
        return d.isoformat()[:10]
    return str(d)[:10]

class InstrumentService:
    def __init__(self, session, instrument_repo):
        self.session = session
        self.instrument_repo = instrument_repo

    def list_instruments(self) -> list[dict]:
        instruments = self.instrument_repo.list_all()
        result = []
        for inst in instruments:
            cov_start, cov_end, count = self.instrument_repo.coverage(inst.instrument_id)
            result.append({
                "instrument_id": inst.instrument_id,
                "ticker": inst.ticker,
                "name": inst.name,
                "asset_class": inst.asset_class,
                "data_start": _format_date(cov_start),
                "data_end": _format_date(cov_end),
                "bar_count": count,
            })
        return result

    def create_instrument(self, ticker: str, name: str, asset_class: str) -> dict:
        if not ticker or not name or not asset_class:
            raise ValidationError("ticker, name, and asset_class are required")

        existing = self.instrument_repo.find_by_ticker(ticker.strip().upper())
        if existing:
            raise ConflictError(f"Instrument with ticker {ticker.strip().upper()} already exists")

        inst = Instrument(
            ticker=ticker.strip().upper(),
            name=name.strip(),
            asset_class=asset_class.strip(),
        )
        saved = self.instrument_repo.add(inst)
        self.session.commit()
        return {
            "instrument_id": saved.instrument_id,
            "ticker": saved.ticker,
            "name": saved.name,
            "asset_class": saved.asset_class,
            "data_start": None,
            "data_end": None,
            "bar_count": 0,
        }

    def update_instrument(self, instrument_id: int, ticker: str, name: str, asset_class: str) -> dict:
        inst = self.instrument_repo.find_by_id(instrument_id)
        if not inst:
            raise NotFoundError("Instrument not found")

        clean_ticker = ticker.strip().upper()
        if clean_ticker != inst.ticker:
            existing = self.instrument_repo.find_by_ticker(clean_ticker)
            if existing:
                raise ConflictError(f"Instrument with ticker {clean_ticker} already exists")

        inst.ticker = clean_ticker
        inst.name = name.strip()
        inst.asset_class = asset_class.strip()
        saved = self.instrument_repo.update(inst)
        self.session.commit()

        cov_start, cov_end, count = self.instrument_repo.coverage(saved.instrument_id)
        return {
            "instrument_id": saved.instrument_id,
            "ticker": saved.ticker,
            "name": saved.name,
            "asset_class": saved.asset_class,
            "data_start": _format_date(cov_start),
            "data_end": _format_date(cov_end),
            "bar_count": count,
        }

    def delete_instrument(self, instrument_id: int) -> None:
        inst = self.instrument_repo.find_by_id(instrument_id)
        if not inst:
            raise NotFoundError("Instrument not found")

        # Check if referenced by backtest runs
        referenced = self.session.query(BacktestRun).filter(BacktestRun.instrument_id == instrument_id).first()
        if referenced:
            raise ConflictError("Instrument is in use by one or more backtest runs")

        self.instrument_repo.remove(instrument_id)
        self.session.commit()

    def import_prices(self, instrument_id: int, csv_bytes: bytes) -> dict:
        inst = self.instrument_repo.find_by_id(instrument_id)
        if not inst:
            raise NotFoundError("Instrument not found")

        try:
            content = csv_bytes.decode("utf-8")
        except UnicodeDecodeError:
            raise ValidationError("CSV file must be UTF-8 encoded")

        reader = csv.reader(io.StringIO(content))
        header = next(reader, None)
        if not header:
            raise ValidationError("CSV file is empty")

        clean_header = [h.strip().lower() for h in header]
        expected_header = ["date", "open", "high", "low", "close", "volume"]
        if clean_header != expected_header:
            raise ValidationError("CSV header must be exactly date,open,high,low,close,volume")

        valid_rows = []
        errors = []
        row_num = 1  # header is row 1, data starts at row 2

        for row in reader:
            row_num += 1
            if not row or all(c.strip() == "" for c in row):
                continue
            if len(row) < 6:
                errors.append({"row": row_num, "reason": "Fewer than 6 columns in row"})
                continue

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

            valid_rows.append({
                "date": d_val,
                "open": open_val,
                "high": high_val,
                "low": low_val,
                "close": close_val,
                "volume": vol_val,
            })

        imported = 0
        if valid_rows:
            imported = self.instrument_repo.save_price_data(instrument_id, valid_rows)
            self.session.commit()

        return {
            "imported": imported,
            "skipped": len(errors),
            "errors": errors,
        }
