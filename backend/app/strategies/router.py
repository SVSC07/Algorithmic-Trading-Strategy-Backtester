from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import require_trader
from app.models.user import User
from app.repositories.strategy_repository import StrategyRepository
from app.services.strategy_service import StrategyService

router = APIRouter(prefix="/strategies", tags=["strategies"])

class CreateStrategyRequest(BaseModel):
    strategy_type: str
    parameters: dict

def _format_strategy(s) -> dict:
    created = getattr(s, "created_at", None)
    iso_created = created.isoformat() if hasattr(created, "isoformat") else str(created)
    return {
        "strategy_id": s.strategy_id,
        "user_id": s.user_id,
        "strategy_type": s.strategy_type,
        "parameters": s.parameters,
        "created_at": iso_created,
    }

@router.post("", status_code=status.HTTP_201_CREATED)
def create_strategy(
    req: CreateStrategyRequest,
    current_user: User = Depends(require_trader),
    db: Session = Depends(get_db),
):
    strategy_repo = StrategyRepository(db)
    service = StrategyService(db, strategy_repo)
    strategy = service.create_strategy(current_user.user_id, req.strategy_type, req.parameters)
    return _format_strategy(strategy)

@router.get("", status_code=status.HTTP_200_OK)
def list_strategies(
    current_user: User = Depends(require_trader),
    db: Session = Depends(get_db),
):
    strategy_repo = StrategyRepository(db)
    service = StrategyService(db, strategy_repo)
    strategies = service.list_strategies(current_user.user_id)
    return [_format_strategy(s) for s in strategies]
