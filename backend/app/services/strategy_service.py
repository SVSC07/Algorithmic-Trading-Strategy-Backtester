"""
services/strategy_service.py
StrategyService.
"""
from typing import List
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.domain import ValidationError
from app.models import Strategy
from app.repositories.strategy_repository import StrategyRepository
from app.strategies.factory import StrategyFactory


class StrategyService:
    def __init__(self, session: Session, strategy_repo: StrategyRepository) -> None:
        self._session = session
        self._repo = strategy_repo

    def create_strategy(
        self, user_id: int, strategy_type: str, parameters: dict
    ) -> Strategy:
        """Create and persist a new strategy with parameter validation."""
        # Validate through StrategyFactory; raises ValidationError if invalid
        StrategyFactory.create(strategy_type, parameters)

        try:
            strat = Strategy(
                user_id=user_id,
                strategy_type=strategy_type,
                parameters=parameters,
            )
        except Exception:
            strat = Strategy(
                strategy_id=None,
                user_id=user_id,
                strategy_type=strategy_type,
                parameters=parameters,
            )

        saved = self._repo.save(strat)
        self._session.commit()
        return saved or strat

    def list_strategies(self, user_id: int) -> List[Strategy]:
        return self._repo.find_by_user(user_id)
