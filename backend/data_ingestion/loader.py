from pathlib import Path
from typing import Dict, Any, Union, Optional, Set
from datetime import date
import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.persistence.database import SessionLocal
from backend.persistence.models import PriceData
from backend.persistence.repositories.price_repo import PriceRepo
from backend.data_ingestion.validator import (
    validate_csv_columns,
    validate_row,
    detect_gaps,
)


def load_prices_from_csv(
    instrument_id: int,
    file_path: Union[str, Path],
    session: Optional[Session] = None,
) -> Dict[str, Any]:
    """Ingest Yahoo Finance price data CSV for a given instrument.

    Input CSV columns: Date, Open, High, Low, Close, Adj Close, Volume.
    Maps to: date, open, high, low, close, volume (Adj Close ignored).

    Returns:
    {
        "rows_loaded": int,
        "rows_rejected": int,
        "gaps_flagged": int,
        "rejected_details": [ {"row": int, "reason": str} ],
        "gap_details": [ {"from": str, "to": str} ]
    }
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Price file not found: {path}")

    # Read CSV
    df = pd.read_csv(path)

    # 1. Validate required columns (will raise ValueError with clear message if missing)
    canonical_map = validate_csv_columns(list(df.columns))

    # Manage session
    close_session_on_finish = False
    if session is None:
        session = SessionLocal()
        close_session_on_finish = True

    try:
        # Load existing dates for this instrument to ensure idempotency and duplicate prevention
        existing_stmt = select(PriceData.date).where(PriceData.instrument_id == instrument_id)
        existing_db_dates: Set[date] = set(session.execute(existing_stmt).scalars().all())

        seen_dates: Set[date] = set()
        valid_records = []
        rejected_details = []

        # Validate rows one by one; CSV line numbers are idx + 2 (1-based, after header)
        for idx, row in df.iterrows():
            row_num = int(idx) + 2
            valid_rec, rejection = validate_row(
                row=row,
                row_num=row_num,
                canonical_map=canonical_map,
                seen_dates=seen_dates,
                existing_db_dates=existing_db_dates,
            )

            if rejection is not None:
                rejected_details.append(rejection)
            elif valid_rec is not None:
                valid_records.append(valid_rec)
                seen_dates.add(valid_rec["date"])

        # Detect gaps on valid records
        gap_details = detect_gaps(valid_records)

        # Bulk insert valid records using PriceRepo
        price_repo = PriceRepo(session=session)
        rows_loaded = price_repo.bulk_insert_prices(
            instrument_id=instrument_id,
            rows=valid_records,
        )

        if close_session_on_finish:
            session.commit()

        return {
            "rows_loaded": rows_loaded,
            "rows_rejected": len(rejected_details),
            "gaps_flagged": len(gap_details),
            "rejected_details": rejected_details,
            "gap_details": gap_details,
        }

    except Exception:
        if close_session_on_finish:
            session.rollback()
        raise
    finally:
        if close_session_on_finish:
            session.close()
