"""
api/instruments.py
Instrument endpoints:
  GET  /api/instruments          TRADER, ADMIN
  POST /api/instruments          ADMIN
  PUT  /api/instruments/{id}     ADMIN
  DELETE /api/instruments/{id}   ADMIN
  POST /api/instruments/{id}/prices   ADMIN (multipart)
"""
from fastapi import APIRouter, Depends, File, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_session, require_role
from app.models import User
from app.repositories.instrument_repository import InstrumentRepository
from app.services.instrument_service import InstrumentService

router = APIRouter(prefix="/instruments", tags=["instruments"])

_TRADER_OR_ADMIN = require_role("TRADER", "ADMIN")
_ADMIN = require_role("ADMIN")


class InstrumentRequest(BaseModel):
    ticker: str
    name: str
    asset_class: str


def _instrument_shape(inst, coverage=None) -> dict:
    if coverage is None:
        first = last = None
        count = 0
    else:
        first, last, count = coverage
    from app.services.results_service import _fmt_date
    return {
        "instrument_id": inst.instrument_id,
        "ticker": inst.ticker,
        "name": inst.name,
        "asset_class": inst.asset_class,
        "data_start": _fmt_date(first),
        "data_end": _fmt_date(last),
        "bar_count": count,
    }


def _svc(session: Session) -> InstrumentService:
    return InstrumentService(session, InstrumentRepository(session))


@router.get("", status_code=200)
def list_instruments(
    session: Session = Depends(get_session),
    _user: User = Depends(_TRADER_OR_ADMIN),
):
    """GET /api/instruments — TRADER, ADMIN."""
    svc = _svc(session)
    repo = InstrumentRepository(session)
    instruments = svc.list_instruments()
    return [_instrument_shape(i, repo.coverage(i.instrument_id)) for i in instruments]


@router.post("", status_code=201)
def create_instrument(
    body: InstrumentRequest,
    session: Session = Depends(get_session),
    _user: User = Depends(_ADMIN),
):
    """POST /api/instruments — ADMIN. 409 on duplicate ticker."""
    svc = _svc(session)
    repo = InstrumentRepository(session)
    inst = svc.create_instrument(body.ticker, body.name, body.asset_class)
    return _instrument_shape(inst, repo.coverage(inst.instrument_id))


@router.put("/{instrument_id}", status_code=200)
def update_instrument(
    instrument_id: int,
    body: InstrumentRequest,
    session: Session = Depends(get_session),
    _user: User = Depends(_ADMIN),
):
    """PUT /api/instruments/{id} — ADMIN."""
    svc = _svc(session)
    repo = InstrumentRepository(session)
    inst = svc.update_instrument(instrument_id, body.ticker, body.name, body.asset_class)
    return _instrument_shape(inst, repo.coverage(inst.instrument_id))


@router.delete("/{instrument_id}", status_code=204)
def delete_instrument(
    instrument_id: int,
    session: Session = Depends(get_session),
    _user: User = Depends(_ADMIN),
):
    """DELETE /api/instruments/{id} — ADMIN. 409 if any run references it."""
    svc = _svc(session)
    svc.delete_instrument(instrument_id)
    return None


@router.post("/{instrument_id}/prices", status_code=200)
async def import_prices(
    instrument_id: int,
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
    _user: User = Depends(_ADMIN),
):
    """POST /api/instruments/{id}/prices — ADMIN. Multipart field 'file', CSV."""
    csv_bytes = await file.read()
    svc = _svc(session)
    return svc.import_prices(instrument_id, csv_bytes)
