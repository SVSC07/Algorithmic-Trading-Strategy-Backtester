# STUB, owned by Molik, replaced on merge
from fastapi import APIRouter, Depends, UploadFile, File, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import require_trader, require_admin
from app.models.user import User
from app.repositories.instrument_repository import InstrumentRepository
from app.services.instrument_service import InstrumentService

router = APIRouter(prefix="/instruments", tags=["instruments"])

class InstrumentPayload(BaseModel):
    ticker: str
    name: str
    asset_class: str

@router.get("", status_code=status.HTTP_200_OK)
def list_instruments(
    current_user: User = Depends(require_trader),
    db: Session = Depends(get_db),
):
    repo = InstrumentRepository(db)
    service = InstrumentService(db, repo)
    return service.list_instruments()

@router.post("", status_code=status.HTTP_201_CREATED)
def create_instrument(
    req: InstrumentPayload,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    repo = InstrumentRepository(db)
    service = InstrumentService(db, repo)
    return service.create_instrument(req.ticker, req.name, req.asset_class)

@router.put("/{instrument_id}", status_code=status.HTTP_200_OK)
def update_instrument(
    instrument_id: int,
    req: InstrumentPayload,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    repo = InstrumentRepository(db)
    service = InstrumentService(db, repo)
    return service.update_instrument(instrument_id, req.ticker, req.name, req.asset_class)

@router.delete("/{instrument_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_instrument(
    instrument_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    repo = InstrumentRepository(db)
    service = InstrumentService(db, repo)
    service.delete_instrument(instrument_id)
    return None

@router.post("/{instrument_id}/prices", status_code=status.HTTP_200_OK)
async def upload_prices(
    instrument_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    repo = InstrumentRepository(db)
    service = InstrumentService(db, repo)
    csv_bytes = await file.read()
    return service.import_prices(instrument_id, csv_bytes)
