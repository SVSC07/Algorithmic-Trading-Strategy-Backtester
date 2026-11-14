# STUB, owned by Rishabh, replaced on merge
from sqlalchemy.orm import Session
from app.models.strategy import Strategy

class StrategyRepository:
    def __init__(self, session: Session):
        self.session = session

    def save(self, strategy: Strategy) -> Strategy:
        self.session.add(strategy)
        self.session.flush()
        return strategy

    def find_by_id(self, strategy_id: int) -> Strategy | None:
        return self.session.query(Strategy).filter(Strategy.strategy_id == strategy_id).first()

    def find_by_user(self, user_id: int) -> list[Strategy]:
        return self.session.query(Strategy).filter(Strategy.user_id == user_id).order_by(Strategy.strategy_id.desc()).all()
