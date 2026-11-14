from datetime import date
import pandas as pd
from app.domain import Signal, ValidationError
from app.strategies.base import Strategy

def _to_date(val) -> date:
    if hasattr(val, "date") and callable(val.date):
        return val.date()
    if isinstance(val, date):
        return val
    return pd.to_datetime(val).date()

class MovingAverageCrossoverStrategy(Strategy):
    """
    Moving Average Crossover Strategy.
    Rule 4:
    short_window and long_window (ints, short < long).
    BUY on the day the short SMA crosses above the long SMA
    (previous bar short <= long, this bar short > long).
    SELL on the opposite cross (previous bar short >= long, this bar short < long).
    No signals before long_window bars exist.
    """

    def __init__(self, short_window: int, long_window: int):
        if isinstance(short_window, bool) or not isinstance(short_window, int):
            raise ValidationError("short_window must be an integer")
        if isinstance(long_window, bool) or not isinstance(long_window, int):
            raise ValidationError("long_window must be an integer")
        if short_window < 1:
            raise ValidationError("short_window must be at least 1")
        if long_window <= short_window:
            raise ValidationError("short_window must be strictly less than long_window")

        self.short_window = short_window
        self.long_window = long_window

    def generate_signals(self, price_data: pd.DataFrame) -> list[Signal]:
        if price_data is None or price_data.empty:
            return []

        if len(price_data) < self.long_window:
            return []

        # Ensure close is float series
        closes = price_data["close"].astype(float)
        short_sma = closes.rolling(window=self.short_window).mean()
        long_sma = closes.rolling(window=self.long_window).mean()

        signals: list[Signal] = []

        # Bars before long_window bars exist cannot produce signals
        for i in range(self.long_window, len(price_data)):
            prev_short = short_sma.iloc[i - 1]
            prev_long = long_sma.iloc[i - 1]
            curr_short = short_sma.iloc[i]
            curr_long = long_sma.iloc[i]

            if pd.isna(prev_short) or pd.isna(prev_long) or pd.isna(curr_short) or pd.isna(curr_long):
                continue

            bar_date = _to_date(price_data.iloc[i]["date"])
            bar_price = float(closes.iloc[i])

            if prev_short <= prev_long and curr_short > curr_long:
                signals.append(Signal(date=bar_date, action="BUY", price=bar_price))
            elif prev_short >= prev_long and curr_short < curr_long:
                signals.append(Signal(date=bar_date, action="SELL", price=bar_price))

        return signals
