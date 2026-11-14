from typing import Type
from app.domain import ValidationError
from app.strategies.base import Strategy
from app.strategies.moving_average_crossover import MovingAverageCrossoverStrategy
from app.strategies.mean_reversion import MeanReversionStrategy

class StrategyFactory:
    """
    Factory to instantiate strategies based on strategy_type and parameter dict.
    Satisfies NFR-4 and extensible registration.
    """
    _registry: dict[str, Type[Strategy]] = {}

    @classmethod
    def register(cls, strategy_type: str, strategy_cls: Type[Strategy]) -> None:
        if not isinstance(strategy_type, str) or not strategy_type:
            raise ValidationError("strategy_type must be a non-empty string")
        if not issubclass(strategy_cls, Strategy):
            raise ValidationError("strategy_cls must inherit from Strategy")
        cls._registry[strategy_type] = strategy_cls

    @classmethod
    def create(cls, strategy_type: str, parameters: dict) -> Strategy:
        if not isinstance(strategy_type, str):
            raise ValidationError("strategy_type must be a string")
        if strategy_type not in cls._registry:
            raise ValidationError(f"Unknown strategy type: {strategy_type}")
        if not isinstance(parameters, dict):
            raise ValidationError("parameters must be a dictionary")

        target_cls = cls._registry[strategy_type]

        if strategy_type == "MOVING_AVERAGE_CROSSOVER":
            if "short_window" not in parameters or "long_window" not in parameters:
                raise ValidationError("MOVING_AVERAGE_CROSSOVER requires short_window and long_window")
            allowed_keys = {"short_window", "long_window"}
            if set(parameters.keys()) - allowed_keys:
                raise ValidationError("Extra parameters provided for MOVING_AVERAGE_CROSSOVER")
            return target_cls(
                short_window=parameters["short_window"],
                long_window=parameters["long_window"],
            )

        if strategy_type == "MEAN_REVERSION":
            if "lookback_period" not in parameters or "threshold" not in parameters:
                raise ValidationError("MEAN_REVERSION requires lookback_period and threshold")
            allowed_keys = {"lookback_period", "threshold"}
            if set(parameters.keys()) - allowed_keys:
                raise ValidationError("Extra parameters provided for MEAN_REVERSION")
            return target_cls(
                lookback_period=parameters["lookback_period"],
                threshold=parameters["threshold"],
            )

        try:
            return target_cls(**parameters)
        except TypeError as e:
            raise ValidationError(f"Invalid parameters for {strategy_type}: {e}")

# Pre-register built-in strategies
StrategyFactory.register("MOVING_AVERAGE_CROSSOVER", MovingAverageCrossoverStrategy)
StrategyFactory.register("MEAN_REVERSION", MeanReversionStrategy)
