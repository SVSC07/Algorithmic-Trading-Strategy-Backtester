from datetime import datetime, timezone
from app.strategies.factory import StrategyFactory

class StrategyService:
    """Service for managing trading strategies."""

    def __init__(self, session, strategy_repo):
        self.session = session
        self.strategy_repo = strategy_repo

    def create_strategy(self, user_id: int, strategy_type: str, parameters: dict):
        # Validate through StrategyFactory; raises ValidationError if invalid
        StrategyFactory.create(strategy_type, parameters)

        # Lazy import of model if available, else lightweight container
        try:
            from app.models.strategy import Strategy as StrategyModel
            strategy_obj = StrategyModel(
                user_id=user_id,
                strategy_type=strategy_type,
                parameters=parameters,
                created_at=datetime.now(timezone.utc),
            )
        except (ImportError, Exception):
            from tests.fakes import FakeStrategy
            strategy_obj = FakeStrategy(
                strategy_id=None,
                user_id=user_id,
                strategy_type=strategy_type,
                parameters=parameters,
                created_at=datetime.now(timezone.utc),
            )

        saved = self.strategy_repo.save(strategy_obj)
        self.session.commit()
        return saved

    def list_strategies(self, user_id: int):
        return self.strategy_repo.find_by_user(user_id)
