"""
api/backtests.py
Backtest endpoints:
  POST /api/backtests                   TRADER
  GET  /api/backtests                   TRADER
  GET  /api/backtests/compare?runA=&runB=  TRADER  (MUST be registered BEFORE /{id})
  GET  /api/backtests/{id}              TRADER
"""
from datetime import date

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, model_validator
from sqlalchemy.orm import Session

from app.api.deps import get_session, require_role
from app.services.backtest_engine import BacktestEngine
from app.domain import ValidationError
from app.models import User
from app.repositories.backtest_run_repository import BacktestRunRepository
from app.repositories.instrument_repository import InstrumentRepository
from app.repositories.metrics_repository import MetricsRepository
from app.repositories.strategy_repository import StrategyRepository
from app.services.metrics_calculator import MetricsCalculator
from app.services.results_service import ResultsService

router = APIRouter(prefix="/backtests", tags=["backtests"])

_TRADER = require_role("TRADER", "ADMIN")


class BacktestRequest(BaseModel):
    strategy_id: int
    instrument_id: int
    start_date: date
    end_date: date

    @model_validator(mode="after")
    def validate_dates(self):
        if self.start_date >= self.end_date:
            raise ValueError("start_date must be before end_date")
        return self


def _results_svc(session: Session) -> ResultsService:
    return ResultsService(
        session=session,
        run_repo=BacktestRunRepository(session),
        strategy_repo=StrategyRepository(session),
        instrument_repo=InstrumentRepository(session),
        metrics_repo=MetricsRepository(session),
    )


def _engine(session: Session) -> BacktestEngine:
    return BacktestEngine(
        session=session,
        strategy_repo=StrategyRepository(session),
        instrument_repo=InstrumentRepository(session),
        run_repo=BacktestRunRepository(session),
        metrics_repo=MetricsRepository(session),
        calculator=MetricsCalculator(),
    )


@router.post("", status_code=201)
def run_backtest(
    body: BacktestRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(_TRADER),
):
    """
    POST /api/backtests — TRADER.
    400 if start_date >= end_date. 404 if strategy/instrument not found.
    422 INSUFFICIENT_DATA if FR-10 triggered.
    """
    engine = _engine(session)
    run_id = engine.run_backtest(
        user_id=current_user.user_id,
        strategy_id=body.strategy_id,
        instrument_id=body.instrument_id,
        start_date=body.start_date,
        end_date=body.end_date,
    )
    return {"run_id": run_id, "status": "COMPLETED"}


@router.get("", status_code=200)
def list_backtests(
    session: Session = Depends(get_session),
    current_user: User = Depends(_TRADER),
):
    """GET /api/backtests — TRADER. Returns RunSummary list, newest first."""
    svc = _results_svc(session)
    return svc.list_runs(current_user.user_id)


# IMPORTANT: /compare MUST be registered before /{id} to avoid route collision.
@router.get("/compare", status_code=200)
def compare_backtests(
    runA: int = Query(..., alias="runA"),
    runB: int = Query(..., alias="runB"),
    session: Session = Depends(get_session),
    current_user: User = Depends(_TRADER),
):
    """GET /api/backtests/compare?runA=1&runB=2 — TRADER."""
    svc = _results_svc(session)
    return svc.compare_runs(current_user.user_id, runA, runB)


@router.get("/{run_id}/trades", status_code=200)
def get_backtest_trades(
    run_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(_TRADER),
):
    """GET /api/backtests/{id}/trades — TRADER, own runs only."""
    svc = _results_svc(session)
    detail = svc.get_run_detail(current_user.user_id, run_id)
    return detail.get("trades", [])


@router.get("/{run_id}", status_code=200)
def get_backtest(
    run_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(_TRADER),
):
    """GET /api/backtests/{id} — TRADER, own runs only."""
    svc = _results_svc(session)
    return svc.get_run_detail(current_user.user_id, run_id)
