"""
Unit tests for Instrument Service and CSV Import.
Owned by Rishabh.
"""
import pytest
from app.domain import ValidationError, ConflictError, NotFoundError
from app.models.instrument import Instrument
from app.repositories.instrument_repository import InstrumentRepository
from app.services.instrument_service import InstrumentService

def test_create_and_update_instrument(db_session):
    repo = InstrumentRepository(db_session)
    service = InstrumentService(db_session, repo)

    inst = service.create_instrument(ticker="googl", name="Alphabet Inc.", asset_class="Equity")
    assert inst["ticker"] == "GOOGL"

    # Duplicate ticker conflict
    with pytest.raises(ConflictError):
        service.create_instrument(ticker="GOOGL", name="Alphabet Inc. 2", asset_class="Equity")

    # Update
    updated = service.update_instrument(inst["instrument_id"], ticker="GOOG", name="Alphabet", asset_class="Equity")
    assert updated["ticker"] == "GOOG"

def test_import_prices_valid_and_errors(db_session):
    repo = InstrumentRepository(db_session)
    service = InstrumentService(db_session, repo)

    inst = service.create_instrument(ticker="NFLX", name="Netflix", asset_class="Equity")

    # Header exact match requirement
    bad_header_csv = b"date,open,high,low,close\n2024-01-01,10,11,9,10"
    with pytest.raises(ValidationError):
        service.import_prices(inst["instrument_id"], bad_header_csv)

    # Valid CSV with 1 good row and 1 invalid row
    csv_data = (
        b"date,open,high,low,close,volume\n"
        b"2024-01-01,100.0,105.0,95.0,102.0,50000\n"
        b"bad-date,100.0,105.0,95.0,102.0,50000\n"
        b"2024-01-02,102.0,108.0,101.0,106.0,-10\n"  # negative volume error
    )
    res = service.import_prices(inst["instrument_id"], csv_data)
    assert res["imported"] == 1
    assert res["skipped"] == 2
    assert len(res["errors"]) == 2
