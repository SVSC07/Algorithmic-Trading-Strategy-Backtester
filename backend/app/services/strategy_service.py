# STUB — owned by Shaurya, replaced on merge
"""
services/strategy_service.py
StrategyService stub.
"""
from typing import List

from sqlalchemy.orm import Session

from app.domain import ValidationError
from app.models import Strategy
from app.repositories.strategy_repository import StrategyRepository


class StrategyService:
    def __init__(self, session: Session, strategy_repo: StrategyRepository) -> None:
        self._session = session
        self._repo = strategy_repo

    def create_strategy(
        self, user_id: int, strategy_type: str, parameters: dict
    ) -> Strategy:
        """Create and persist a new strategy."""
        _VALID_TYPES = {"MOVING_AVERAGE_CROSSOVER", "MEAN_REVERSION"}
        if strategy_type not in _VALID_TYPES:
            raise ValidationError(f"Unknown strategy_type: {strategy_type}")
        strat = Strategy(user_id=user_id, strategy_type=strategy_type, parameters=parameters)
        self._repo.save(strat)
        self._session.commit()
        return strat

    def list_strategies(self, user_id: int) -> List[Strategy]:
        return self._repo.find_by_user(user_id)
