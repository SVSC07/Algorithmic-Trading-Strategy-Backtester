from datetime import datetime, date
from typing import List, Dict, Any, Tuple, Set
import pandas as pd

REQUIRED_COLUMNS = ["Date", "Open", "High", "Low", "Close", "Volume"]


def validate_csv_columns(columns: List[str]) -> Dict[str, str]:
    """Validate that all required columns are present (case-insensitive check).

    Returns a mapping of canonical column names to the actual CSV column names.
    Raises ValueError if any required column is missing.
    """
    col_map = {col.strip().lower(): col for col in columns}
    canonical_map = {}
    missing = []

    for req in REQUIRED_COLUMNS:
        req_lower = req.lower()
        if req_lower in col_map:
            canonical_map[req_lower] = col_map[req_lower]
        else:
            missing.append(req)

    if missing:
        raise ValueError(
            f"CSV file is missing required column(s): {', '.join(missing)}. "
            f"Found columns: {list(columns)}"
        )

    return canonical_map


def validate_row(
    row: pd.Series,
    row_num: int,
    canonical_map: Dict[str, str],
    seen_dates: Set[date],
    existing_db_dates: Set[date],
) -> Tuple[Dict[str, Any] | None, Dict[str, Any] | None]:
    """Validate an individual CSV row.

    Returns:
        (valid_row_dict, None) if valid.
        (None, {"row": row_num, "reason": reason}) if rejected.
    """
    # 1. Date validation
    date_val = row[canonical_map["date"]]
    if pd.isna(date_val):
        return None, {"row": row_num, "reason": "date unparseable"}

    try:
        if isinstance(date_val, (pd.Timestamp, datetime)):
            parsed_date = date_val.date()
        else:
            parsed_date = datetime.strptime(str(date_val).strip(), "%Y-%m-%d").date()
    except Exception:
        return None, {"row": row_num, "reason": "date unparseable"}

    # 2. Duplicate date checks
    if parsed_date in seen_dates or parsed_date in existing_db_dates:
        return None, {"row": row_num, "reason": "duplicate date"}

    # 3. Numeric checks
    try:
        open_val = float(row[canonical_map["open"]])
        high_val = float(row[canonical_map["high"]])
        low_val = float(row[canonical_map["low"]])
        close_val = float(row[canonical_map["close"]])
        volume_val = int(float(row[canonical_map["volume"]]))
    except (ValueError, TypeError):
        return None, {"row": row_num, "reason": "non-numeric price or volume"}

    if any(pd.isna(v) for v in (open_val, high_val, low_val, close_val, volume_val)):
        return None, {"row": row_num, "reason": "non-numeric price or volume"}

    # 4. Range and constraint checks
    if open_val <= 0 or high_val <= 0 or low_val <= 0 or close_val <= 0:
        return None, {"row": row_num, "reason": "price <= 0"}

    if volume_val < 0:
        return None, {"row": row_num, "reason": "volume < 0"}

    if high_val < low_val:
        return None, {"row": row_num, "reason": "high < low"}

    if open_val < low_val or open_val > high_val:
        return None, {"row": row_num, "reason": "open outside [low, high]"}

    if close_val < low_val or close_val > high_val:
        return None, {"row": row_num, "reason": "close outside [low, high]"}

    valid_record = {
        "date": parsed_date,
        "open": round(open_val, 4),
        "high": round(high_val, 4),
        "low": round(low_val, 4),
        "close": round(close_val, 4),
        "volume": volume_val,
    }
    return valid_record, None


def detect_gaps(valid_records: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """Flag missing business days longer than 4 consecutive calendar days.

    Gaps are flagged, never filled and never crash.
    Returns list of {"from": "YYYY-MM-DD", "to": "YYYY-MM-DD"}.
    """
    if len(valid_records) < 2:
        return []

    # Ensure sorted by date
    sorted_records = sorted(valid_records, key=lambda r: r["date"])
    gap_details = []

    for i in range(len(sorted_records) - 1):
        d_from: date = sorted_records[i]["date"]
        d_to: date = sorted_records[i + 1]["date"]
        diff_calendar_days = (d_to - d_from).days

        if diff_calendar_days > 4:
            gap_details.append(
                {
                    "from": d_from.isoformat(),
                    "to": d_to.isoformat(),
                }
            )

    return gap_details
