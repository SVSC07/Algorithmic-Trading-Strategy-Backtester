"""
api/strategies.py
Strategy endpoints: POST /api/strategies, GET /api/strategies.
TRADER role required.
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from app.api.deps import get_session, require_role
from app.models import User
from app.repositories.strategy_repository import StrategyRepository
from app.services.strategy_service import StrategyService

router = APIRouter(prefix="/strategies", tags=["strategies"])

_TRADER = require_role("TRADER", "ADMIN")


class StrategyRequest(BaseModel):
    strategy_type: str
    parameters: dict

    @field_validator("strategy_type")
    @classmethod
    def strategy_type_non_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("strategy_type must not be empty")
        return v


def _strategy_shape(s) -> dict:
    from app.services.results_service import _fmt_date
    return {
        "strategy_id": s.strategy_id,
        "user_id": s.user_id,
        "strategy_type": s.strategy_type,
        "parameters": s.parameters,
        "created_at": _fmt_date(s.created_at),
    }


@router.post("", status_code=201)
def create_strategy(
    body: StrategyRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(_TRADER),
):
    """POST /api/strategies — TRADER. Create a new strategy."""
    svc = StrategyService(session, StrategyRepository(session))
    strategy = svc.create_strategy(current_user.user_id, body.strategy_type, body.parameters)
    return _strategy_shape(strategy)


@router.get("", status_code=200)
def list_strategies(
    session: Session = Depends(get_session),
    current_user: User = Depends(_TRADER),
):
    """GET /api/strategies — TRADER. List own strategies."""
    svc = StrategyService(session, StrategyRepository(session))
    strategies = svc.list_strategies(current_user.user_id)
    return [_strategy_shape(s) for s in strategies]
