# STUB, owned by Rishabh, replaced on merge
from sqlalchemy.orm import Session
from app.domain import TradeRecord
from app.models.backtest_run import BacktestRun
from app.models.trade import Trade

class BacktestRunRepository:
    def __init__(self, session: Session):
        self.session = session

    def save(self, run: BacktestRun, trades: list[TradeRecord]) -> BacktestRun:
        self.session.add(run)
        self.session.flush()

        for t in trades:
            trade_row = Trade(
                run_id=run.run_id,
                entry_date=t.entry_date,
                exit_date=t.exit_date,
                entry_price=t.entry_price,
                exit_price=t.exit_price,
                quantity=t.quantity,
                pnl=t.pnl,
            )
            self.session.add(trade_row)

        self.session.flush()
        return run

    def find_by_id(self, run_id: int) -> BacktestRun | None:
        return self.session.query(BacktestRun).filter(BacktestRun.run_id == run_id).first()

    def find_by_user(self, user_id: int) -> list[BacktestRun]:
        return (
            self.session.query(BacktestRun)
            .filter(BacktestRun.user_id == user_id)
            .order_by(BacktestRun.run_id.desc())
            .all()
        )

    def get_trades(self, run_id: int) -> list[Trade]:
        return (
            self.session.query(Trade)
            .filter(Trade.run_id == run_id)
            .order_by(Trade.entry_date.asc(), Trade.trade_id.asc())
            .all()
        )
