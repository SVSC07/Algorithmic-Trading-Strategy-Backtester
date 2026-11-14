from datetime import date
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import require_trader
from app.models.user import User
from app.repositories.strategy_repository import StrategyRepository
from app.repositories.instrument_repository import InstrumentRepository
from app.repositories.backtest_run_repository import BacktestRunRepository
from app.repositories.metrics_repository import MetricsRepository
from app.services.metrics_calculator import MetricsCalculator
from app.services.results_service import ResultsService
from app.services.backtest_engine import BacktestEngine

router = APIRouter(prefix="/backtests", tags=["backtests"])

class RunBacktestRequest(BaseModel):
    strategy_id: int
    instrument_id: int
    start_date: date
    end_date: date

@router.post("", status_code=status.HTTP_201_CREATED)
def run_backtest(
    req: RunBacktestRequest,
    current_user: User = Depends(require_trader),
    db: Session = Depends(get_db),
):
    strategy_repo = StrategyRepository(db)
    instrument_repo = InstrumentRepository(db)
    run_repo = BacktestRunRepository(db)
    metrics_repo = MetricsRepository(db)
    calculator = MetricsCalculator()

    engine = BacktestEngine(
        session=db,
        strategy_repo=strategy_repo,
        instrument_repo=instrument_repo,
        run_repo=run_repo,
        metrics_repo=metrics_repo,
        calculator=calculator,
    )

    run_id = engine.run_backtest(
        user_id=current_user.user_id,
        strategy_id=req.strategy_id,
        instrument_id=req.instrument_id,
        start_date=req.start_date,
        end_date=req.end_date,
        raise_on_insufficient_data=True,
    )

    return {
        "run_id": run_id,
        "status": "COMPLETED",
    }

@router.get("", status_code=status.HTTP_200_OK)
def list_backtests(
    current_user: User = Depends(require_trader),
    db: Session = Depends(get_db),
):
    run_repo = BacktestRunRepository(db)
    strategy_repo = StrategyRepository(db)
    instrument_repo = InstrumentRepository(db)
    metrics_repo = MetricsRepository(db)

    results_service = ResultsService(
        session=db,
        run_repo=run_repo,
        strategy_repo=strategy_repo,
        instrument_repo=instrument_repo,
        metrics_repo=metrics_repo,
    )

    return results_service.list_runs(current_user.user_id)

@router.get("/compare", status_code=status.HTTP_200_OK)
def compare_backtests(
    runA: int = Query(..., alias="runA"),
    runB: int = Query(..., alias="runB"),
    current_user: User = Depends(require_trader),
    db: Session = Depends(get_db),
):
    run_repo = BacktestRunRepository(db)
    strategy_repo = StrategyRepository(db)
    instrument_repo = InstrumentRepository(db)
    metrics_repo = MetricsRepository(db)

    results_service = ResultsService(
        session=db,
        run_repo=run_repo,
        strategy_repo=strategy_repo,
        instrument_repo=instrument_repo,
        metrics_repo=metrics_repo,
    )

    return results_service.compare_runs(current_user.user_id, runA, runB)

@router.get("/{run_id}/trades", status_code=status.HTTP_200_OK)
def get_backtest_trades(
    run_id: int,
    current_user: User = Depends(require_trader),
    db: Session = Depends(get_db),
):
    run_repo = BacktestRunRepository(db)
    strategy_repo = StrategyRepository(db)
    instrument_repo = InstrumentRepository(db)
    metrics_repo = MetricsRepository(db)

    results_service = ResultsService(
        session=db,
        run_repo=run_repo,
        strategy_repo=strategy_repo,
        instrument_repo=instrument_repo,
        metrics_repo=metrics_repo,
    )
    detail = results_service.get_run_detail(current_user.user_id, run_id)
    return detail.get("trades", [])

@router.get("/{run_id}", status_code=status.HTTP_200_OK)
def get_backtest_detail(
    run_id: int,
    current_user: User = Depends(require_trader),
    db: Session = Depends(get_db),
):
    run_repo = BacktestRunRepository(db)
    strategy_repo = StrategyRepository(db)
    instrument_repo = InstrumentRepository(db)
    metrics_repo = MetricsRepository(db)

    results_service = ResultsService(
        session=db,
        run_repo=run_repo,
        strategy_repo=strategy_repo,
        instrument_repo=instrument_repo,
        metrics_repo=metrics_repo,
    )

    return results_service.get_run_detail(current_user.user_id, run_id)
