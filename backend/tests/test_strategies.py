"""
Unit tests for Trading Strategies (Moving Average Crossover & Mean Reversion).
Owned by Shaurya.
"""
from datetime import date
import pandas as pd
import pytest
from app.domain import ValidationError
from app.strategies.base import Strategy
from app.strategies.moving_average_crossover import MovingAverageCrossoverStrategy
from app.strategies.mean_reversion import MeanReversionStrategy
from app.strategies.factory import StrategyFactory

def make_ohlcv(dates: list[str], closes: list[float]) -> pd.DataFrame:
    df = pd.DataFrame({
        "date": pd.to_datetime(dates),
        "open": closes,
        "high": [c + 1.0 for c in closes],
        "low": [max(0.1, c - 1.0) for c in closes],
        "close": closes,
        "volume": [1000.0] * len(closes),
    })
    return df

class TestMovingAverageCrossover:
    """
    HAND CALCULATION:
    short_window = 2, long_window = 4
    Dates: 2024-01-01 to 2024-01-08 (8 bars)
    Closes: [10.0, 10.0, 10.0, 10.0, 14.0, 14.0, 6.0, 6.0]

    Bar 0 (2024-01-01): close = 10.0
    Bar 1 (2024-01-02): close = 10.0
    Bar 2 (2024-01-03): close = 10.0
    Bar 3 (2024-01-04): close = 10.0
        short_sma = (10+10)/2 = 10.0
        long_sma = (10+10+10+10)/4 = 10.0
        (index 3 is long_window - 1, earliest long SMA)
    Bar 4 (2024-01-05): close = 14.0
        short_sma = (10+14)/2 = 12.0
        long_sma = (10+10+10+14)/4 = 11.0
        prev_short (10.0) <= prev_long (10.0) and curr_short (12.0) > curr_long (11.0)
        -> EXPECTED: BUY signal at date 2024-01-05, price 14.0
    Bar 5 (2024-01-06): close = 14.0
        short_sma = (14+14)/2 = 14.0
        long_sma = (10+10+14+14)/4 = 12.0
        prev_short (12.0) > prev_long (11.0), no cross
    Bar 6 (2024-01-07): close = 6.0
        short_sma = (14+6)/2 = 10.0
        long_sma = (10+14+14+6)/4 = 11.0
        prev_short (14.0) >= prev_long (12.0) and curr_short (10.0) < curr_long (11.0)
        -> EXPECTED: SELL signal at date 2024-01-07, price 6.0
    Bar 7 (2024-01-08): close = 6.0
        short_sma = (6+6)/2 = 6.0
        long_sma = (14+14+6+6)/4 = 10.0
        prev_short (10.0) <= prev_long (11.0), no cross

    TOTAL EXPECTED SIGNALS:
    1. 2024-01-05: BUY @ 14.0
    2. 2024-01-07: SELL @ 6.0
    """
    def test_moving_average_crossover_exact_signals(self):
        dates = [
            "2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04",
            "2024-01-05", "2024-01-06", "2024-01-07", "2024-01-08",
        ]
        closes = [10.0, 10.0, 10.0, 10.0, 14.0, 14.0, 6.0, 6.0]
        df = make_ohlcv(dates, closes)

        strategy = MovingAverageCrossoverStrategy(short_window=2, long_window=4)
        signals = strategy.generate_signals(df)

        assert len(signals) == 2

        # 1. First signal BUY at 2024-01-05 @ 14.0
        assert signals[0].date == date(2024, 1, 5)
        assert signals[0].action == "BUY"
        assert signals[0].price == 14.0

        # 2. Second signal SELL at 2024-01-07 @ 6.0
        assert signals[1].date == date(2024, 1, 7)
        assert signals[1].action == "SELL"
        assert signals[1].price == 6.0

    def test_moving_average_crossover_parameter_validation(self):
        with pytest.raises(ValidationError):
            MovingAverageCrossoverStrategy(short_window=0, long_window=5)
        with pytest.raises(ValidationError):
            MovingAverageCrossoverStrategy(short_window=5, long_window=5)
        with pytest.raises(ValidationError):
            MovingAverageCrossoverStrategy(short_window=10, long_window=5)
        with pytest.raises(ValidationError):
            MovingAverageCrossoverStrategy(short_window=True, long_window=5)  # bool rejected

    def test_flat_price_series_produces_zero_signals(self):
        # Flat series: short SMA == long SMA == 50.0 continuously -> no cross
        dates = [f"2024-01-{i:02d}" for i in range(1, 15)]
        closes = [50.0] * len(dates)
        df = make_ohlcv(dates, closes)

        strat = MovingAverageCrossoverStrategy(short_window=2, long_window=5)
        signals = strat.generate_signals(df)
        assert len(signals) == 0

    def test_data_gap_handled_without_crashing(self):
        # 10 bars spanning irregular days (weekends, holidays, multi-day gaps)
        dates = [
            "2024-01-01", "2024-01-02", "2024-01-08", "2024-01-15",
            "2024-01-20", "2024-02-01", "2024-02-10", "2024-02-15",
        ]
        closes = [10.0, 10.0, 10.0, 10.0, 15.0, 15.0, 5.0, 5.0]
        df = make_ohlcv(dates, closes)

        strat = MovingAverageCrossoverStrategy(short_window=2, long_window=4)
        signals = strat.generate_signals(df)
        assert len(signals) == 2
        assert signals[0].action == "BUY"
        assert signals[1].action == "SELL"

class TestMeanReversion:
    """
    HAND CALCULATION:
    lookback_period = 3, threshold = 1.0
    Dates: 2024-01-01 to 2024-01-05 (5 bars)
    Closes: [10.0, 10.0, 10.0, 4.0, 8.0]

    Bar 0 (2024-01-01): 10.0
    Bar 1 (2024-01-02): 10.0
    Bar 2 (2024-01-03): 10.0
        Window [10, 10, 10]: mean = 10.0, std = 0.0 (flat over window -> no signal)
    Bar 3 (2024-01-04): 4.0
        Window [10, 10, 4]:
        mean m = (10 + 10 + 4) / 3 = 8.0
        std s = sqrt([ (10-8)^2 + (10-8)^2 + (4-8)^2 ] / 2) = sqrt(24/2) = sqrt(12) = 3.4641
        lower_bound = m - threshold * s = 8.0 - 1.0 * 3.4641 = 4.5359
        close = 4.0 < 4.5359
        -> EXPECTED: BUY signal at date 2024-01-04, price 4.0
    Bar 4 (2024-01-05): 8.0
        Window [10, 4, 8]:
        mean m = (10 + 4 + 8) / 3 = 7.3333
        close = 8.0 >= 7.3333
        -> EXPECTED: SELL signal at date 2024-01-05, price 8.0

    TOTAL EXPECTED SIGNALS:
    1. 2024-01-04: BUY @ 4.0
    2. 2024-01-05: SELL @ 8.0
    """
    def test_mean_reversion_exact_signals(self):
        dates = ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05"]
        closes = [10.0, 10.0, 10.0, 4.0, 8.0]
        df = make_ohlcv(dates, closes)

        strategy = MeanReversionStrategy(lookback_period=3, threshold=1.0)
        signals = strategy.generate_signals(df)

        assert len(signals) == 2

        # 1. BUY signal
        assert signals[0].date == date(2024, 1, 4)
        assert signals[0].action == "BUY"
        assert signals[0].price == 4.0

        # 2. SELL signal
        assert signals[1].date == date(2024, 1, 5)
        assert signals[1].action == "SELL"
        assert signals[1].price == 8.0

    def test_mean_reversion_flat_series_produces_zero_signals(self):
        dates = [f"2024-01-{i:02d}" for i in range(1, 10)]
        closes = [100.0] * len(dates)
        df = make_ohlcv(dates, closes)

        strat = MeanReversionStrategy(lookback_period=3, threshold=1.5)
        signals = strat.generate_signals(df)
        assert len(signals) == 0

    def test_mean_reversion_parameter_validation(self):
        with pytest.raises(ValidationError):
            MeanReversionStrategy(lookback_period=1, threshold=1.0)
        with pytest.raises(ValidationError):
            MeanReversionStrategy(lookback_period=3, threshold=0.0)
        with pytest.raises(ValidationError):
            MeanReversionStrategy(lookback_period=3, threshold=-0.5)
        with pytest.raises(ValidationError):
            MeanReversionStrategy(lookback_period=True, threshold=1.0)

class TestStrategyFactory:
    def test_factory_creates_moving_average_crossover(self):
        strat = StrategyFactory.create(
            "MOVING_AVERAGE_CROSSOVER",
            {"short_window": 5, "long_window": 20},
        )
        assert isinstance(strat, Strategy)
        assert isinstance(strat, MovingAverageCrossoverStrategy)
        assert strat.short_window == 5
        assert strat.long_window == 20

    def test_factory_creates_mean_reversion(self):
        strat = StrategyFactory.create(
            "MEAN_REVERSION",
            {"lookback_period": 10, "threshold": 2.0},
        )
        assert isinstance(strat, Strategy)
        assert isinstance(strat, MeanReversionStrategy)
        assert strat.lookback_period == 10
        assert strat.threshold == 2.0

    def test_factory_rejects_unknown_strategy(self):
        with pytest.raises(ValidationError):
            StrategyFactory.create("UNKNOWN_STRATEGY", {})

    def test_factory_rejects_invalid_parameters(self):
        with pytest.raises(ValidationError):
            StrategyFactory.create("MOVING_AVERAGE_CROSSOVER", {"short_window": 20, "long_window": 5})
        with pytest.raises(ValidationError):
            StrategyFactory.create("MEAN_REVERSION", {"lookback_period": 1, "threshold": 1.0})
        with pytest.raises(ValidationError):
            StrategyFactory.create("MOVING_AVERAGE_CROSSOVER", {"short_window": 5})  # missing long_window
