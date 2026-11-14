from abc import ABC, abstractmethod
import pandas as pd
from app.domain import Signal

class Strategy(ABC):
    """Abstract base class for all algorithmic trading strategies."""

    @abstractmethod
    def generate_signals(self, price_data: pd.DataFrame) -> list[Signal]:
        """
        Generate trading signals based on OHLCV price data.
        
        :param price_data: pandas DataFrame with columns:
                           date (datetime64[ns] or date), open, high, low, close, volume
                           sorted ascending by date.
        :return: list of Signal(date, action, price)
        """
        pass
