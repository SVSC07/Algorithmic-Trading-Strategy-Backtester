import pytest
import pandas as pd
from backend.data_ingestion.loader import load_prices_from_csv
from backend.persistence.models import PriceData
from sqlalchemy import select


def test_1_valid_csv_loads_expected_row_count(tmp_path, db_session, sample_instrument):
    """Test 1: Valid CSV loads with the expected row count."""
    csv_file = tmp_path / "valid.csv"
    data = """Date,Open,High,Low,Close,Adj Close,Volume
2023-01-03,150.00,152.00,149.00,151.00,151.00,1000000
2023-01-04,151.00,153.00,150.00,152.50,152.50,1100000
2023-01-05,152.50,154.00,151.50,153.00,153.00,1200000
2023-01-06,153.00,155.00,152.00,154.00,154.00,1300000
2023-01-09,154.00,156.00,153.50,155.50,155.50,1400000
"""
    csv_file.write_text(data)

    result = load_prices_from_csv(
        instrument_id=sample_instrument.id,
        file_path=csv_file,
        session=db_session,
    )

    assert result["rows_loaded"] == 5
    assert result["rows_rejected"] == 0
    assert result["gaps_flagged"] == 0
    assert result["rejected_details"] == []

    # Verify rows in DB
    db_rows = db_session.execute(
        select(PriceData).where(PriceData.instrument_id == sample_instrument.id)
    ).scalars().all()
    assert len(db_rows) == 5


def test_2_malformed_rows_rejected_other_rows_still_load(tmp_path, db_session, sample_instrument):
    """Test 2: Malformed row rejected, other rows still load (do not crash)."""
    csv_file = tmp_path / "malformed.csv"
    # Row 2 (line 2): valid
    # Row 3 (line 3): high < low (140 < 155) -> reject
    # Row 4 (line 4): valid
    # Row 5 (line 5): negative volume -> reject
    # Row 6 (line 6): non-numeric close -> reject
    # Row 7 (line 7): open outside [low, high] (160 > 155) -> reject
    # Row 8 (line 8): valid
    data = """Date,Open,High,Low,Close,Adj Close,Volume
2023-01-03,150.00,152.00,149.00,151.00,151.00,1000000
2023-01-04,151.00,140.00,155.00,145.00,145.00,1100000
2023-01-05,152.50,154.00,151.50,153.00,153.00,1200000
2023-01-06,153.00,155.00,152.00,154.00,154.00,-500
2023-01-09,154.00,156.00,153.50,INVALID,155.50,1400000
2023-01-10,160.00,155.00,150.00,152.00,152.00,1500000
2023-01-11,152.00,154.00,151.00,153.00,153.00,1600000
"""
    csv_file.write_text(data)

    result = load_prices_from_csv(
        instrument_id=sample_instrument.id,
        file_path=csv_file,
        session=db_session,
    )

    assert result["rows_loaded"] == 3
    assert result["rows_rejected"] == 4

    reasons = [item["reason"] for item in result["rejected_details"]]
    assert "high < low" in reasons
    assert "volume < 0" in reasons
    assert "non-numeric price or volume" in reasons
    assert "open outside [low, high]" in reasons

    # Verify line numbers are captured
    lines = [item["row"] for item in result["rejected_details"]]
    assert lines == [3, 5, 6, 7]


def test_3_duplicate_dates_and_idempotency(tmp_path, db_session, sample_instrument):
    """Test 3: Duplicate dates not inserted twice; running the loader twice is idempotent."""
    csv_file = tmp_path / "duplicates.csv"
    data = """Date,Open,High,Low,Close,Adj Close,Volume
2023-01-03,150.00,152.00,149.00,151.00,151.00,1000000
2023-01-04,151.00,153.00,150.00,152.50,152.50,1100000
2023-01-04,151.00,153.00,150.00,152.50,152.50,1100000
2023-01-05,152.50,154.00,151.50,153.00,153.00,1200000
"""
    csv_file.write_text(data)

    # First run: 3 unique dates loaded, 1 in-file duplicate rejected
    run1 = load_prices_from_csv(
        instrument_id=sample_instrument.id,
        file_path=csv_file,
        session=db_session,
    )
    db_session.commit()

    assert run1["rows_loaded"] == 3
    assert run1["rows_rejected"] == 1
    assert run1["rejected_details"][0]["row"] == 4
    assert run1["rejected_details"][0]["reason"] == "duplicate date"

    count_after_run1 = len(
        db_session.execute(
            select(PriceData).where(PriceData.instrument_id == sample_instrument.id)
        ).scalars().all()
    )
    assert count_after_run1 == 3

    # Second run on the same file: all rows rejected as duplicates, row count unchanged
    run2 = load_prices_from_csv(
        instrument_id=sample_instrument.id,
        file_path=csv_file,
        session=db_session,
    )
    db_session.commit()

    assert run2["rows_loaded"] == 0
    assert run2["rows_rejected"] == 4

    count_after_run2 = len(
        db_session.execute(
            select(PriceData).where(PriceData.instrument_id == sample_instrument.id)
        ).scalars().all()
    )
    assert count_after_run2 == 3


def test_4_gap_detection_flagged_no_crash(tmp_path, db_session, sample_instrument):
    """Test 4: Gap in data detected and flagged, no crash.

    Flag missing business days longer than 4 consecutive calendar days.
    """
    csv_file = tmp_path / "gaps.csv"
    # Gap between 2022-03-01 and 2022-03-09 (8 calendar days > 4)
    data = """Date,Open,High,Low,Close,Adj Close,Volume
2022-03-01,100.00,105.00,99.00,104.00,104.00,500000
2022-03-09,104.00,108.00,103.00,107.00,107.00,600000
2022-03-10,107.00,110.00,106.00,109.00,109.00,700000
"""
    csv_file.write_text(data)

    result = load_prices_from_csv(
        instrument_id=sample_instrument.id,
        file_path=csv_file,
        session=db_session,
    )

    assert result["rows_loaded"] == 3
    assert result["rows_rejected"] == 0
    assert result["gaps_flagged"] == 1
    assert result["gap_details"] == [{"from": "2022-03-01", "to": "2022-03-09"}]


def test_5_missing_column_raises_clear_error(tmp_path, db_session, sample_instrument):
    """Test 5: Missing column -> clear error (rejects entire file)."""
    csv_file = tmp_path / "missing_column.csv"
    # Missing 'Volume'
    data = """Date,Open,High,Low,Close,Adj Close
2023-01-03,150.00,152.00,149.00,151.00,151.00
2023-01-04,151.00,153.00,150.00,152.50,152.50
"""
    csv_file.write_text(data)

    with pytest.raises(ValueError) as excinfo:
        load_prices_from_csv(
            instrument_id=sample_instrument.id,
            file_path=csv_file,
            session=db_session,
        )

    assert "missing required column" in str(excinfo.value).lower()
    assert "volume" in str(excinfo.value).lower()
