# STUB — owned by Rishabh, replaced on merge
"""
repositories/strategy_repository.py
StrategyRepository stub.
"""
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models import Strategy


class StrategyRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, strategy: Strategy) -> Strategy:
        self._session.add(strategy)
        self._session.flush()
        return strategy

    def find_by_id(self, strategy_id: int) -> Optional[Strategy]:
        return self._session.query(Strategy).filter_by(strategy_id=strategy_id).first()

    def find_by_user(self, user_id: int) -> List[Strategy]:
        return self._session.query(Strategy).filter_by(user_id=user_id).all()
