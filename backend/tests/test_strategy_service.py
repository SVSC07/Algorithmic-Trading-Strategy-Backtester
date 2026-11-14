"""
Unit tests for Strategy Service.
Owned by Shaurya.
"""
import pytest
from app.domain import ValidationError
from app.services.strategy_service import StrategyService
from tests.fakes import FakeSession, FakeStrategyRepository

def test_create_strategy_success():
    session = FakeSession()
    repo = FakeStrategyRepository()
    service = StrategyService(session, repo)

    strat = service.create_strategy(
        user_id=1,
        strategy_type="MOVING_AVERAGE_CROSSOVER",
        parameters={"short_window": 10, "long_window": 30},
    )

    assert strat.strategy_id is not None
    assert strat.user_id == 1
    assert strat.strategy_type == "MOVING_AVERAGE_CROSSOVER"
    assert session.committed is True

def test_create_strategy_invalid_parameters():
    session = FakeSession()
    repo = FakeStrategyRepository()
    service = StrategyService(session, repo)

    with pytest.raises(ValidationError):
        service.create_strategy(
            user_id=1,
            strategy_type="MOVING_AVERAGE_CROSSOVER",
            parameters={"short_window": 50, "long_window": 10},  # short > long
        )

def test_list_strategies_by_user():
    session = FakeSession()
    repo = FakeStrategyRepository()
    service = StrategyService(session, repo)

    service.create_strategy(user_id=1, strategy_type="MEAN_REVERSION", parameters={"lookback_period": 5, "threshold": 1.5})
    service.create_strategy(user_id=2, strategy_type="MEAN_REVERSION", parameters={"lookback_period": 5, "threshold": 1.5})
    service.create_strategy(user_id=1, strategy_type="MOVING_AVERAGE_CROSSOVER", parameters={"short_window": 5, "long_window": 15})

    user1_strats = service.list_strategies(user_id=1)
    assert len(user1_strats) == 2
    assert all(s.user_id == 1 for s in user1_strats)
