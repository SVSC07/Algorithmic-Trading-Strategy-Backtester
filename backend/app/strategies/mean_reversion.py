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

class MeanReversionStrategy(Strategy):
    """
    Mean Reversion Strategy.
    Rule 5:
    lookback_period (int, at least 2) and threshold (float, greater than 0).
    With rolling mean m and rolling standard deviation s of closes over lookback_period:
    BUY when close < m - threshold * s.
    SELL when close >= m.
    If volatility s is zero (e.g. flat price series), no signals are produced.
    """

    def __init__(self, lookback_period: int, threshold: float):
        if isinstance(lookback_period, bool) or not isinstance(lookback_period, int):
            raise ValidationError("lookback_period must be an integer")
        if lookback_period < 2:
            raise ValidationError("lookback_period must be at least 2")

        if isinstance(threshold, bool) or not isinstance(threshold, (int, float)):
            raise ValidationError("threshold must be a positive number")
        if threshold <= 0:
            raise ValidationError("threshold must be greater than 0")

        self.lookback_period = lookback_period
        self.threshold = float(threshold)

    def generate_signals(self, price_data: pd.DataFrame) -> list[Signal]:
        if price_data is None or price_data.empty:
            return []

        if len(price_data) < self.lookback_period:
            return []

        closes = price_data["close"].astype(float)
        rolling_mean = closes.rolling(window=self.lookback_period).mean()
        rolling_std = closes.rolling(window=self.lookback_period).std(ddof=1)

        signals: list[Signal] = []

        for i in range(self.lookback_period - 1, len(price_data)):
            m = rolling_mean.iloc[i]
            s = rolling_std.iloc[i]

            if pd.isna(m) or pd.isna(s):
                continue

            # In flat conditions (zero or negligible volatility), no deviation exists
            if s <= 1e-9:
                continue

            close = float(closes.iloc[i])
            bar_date = _to_date(price_data.iloc[i]["date"])

            lower_bound = m - (self.threshold * s)

            if close < lower_bound:
                signals.append(Signal(date=bar_date, action="BUY", price=close))
            elif close >= m:
                signals.append(Signal(date=bar_date, action="SELL", price=close))

        return signals
