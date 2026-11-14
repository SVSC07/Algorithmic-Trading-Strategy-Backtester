"""
Unit tests for Metrics Calculator according to Trading Rule 6.
Owned by Molik.
"""
from datetime import date
import pytest
from app.domain import TradeRecord, EquityPoint
from app.services.metrics_calculator import MetricsCalculator

class DummyRun:
    def __init__(self, start_date: date, end_date: date):
        self.start_date = start_date
        self.end_date = end_date

def test_metrics_calculator_hand_calculated():
    """
    HAND CALCULATION:
    Equities (4 points):
      Day 0: 100,000.0
      Day 1: 105,000.0 (return = +5%)
      Day 2: 95,000.0  (return = -9.5238%)
      Day 3: 110,000.0 (return = +15.7895%)

    initial = 100,000.0
    final = 110,000.0
    total_return = 110,000 / 100,000 - 1 = +0.10 (10.0%)

    calendar_days = 365 (e.g. 2023-01-01 to 2024-01-01)
    cagr = (1.10) ^ (365.25 / 365) - 1.0 = approx 0.10007

    running_peaks:
      Day 0: peak 100k -> dd = 0.0
      Day 1: peak 105k -> dd = 0.0
      Day 2: peak 105k -> dd = 95k / 105k - 1 = -0.095238 (-9.52%)
      Day 3: peak 110k -> dd = 0.0
    max_drawdown = -0.095238

    Trades (2 trades):
      Trade 1: pnl = +5000.0 (>0)
      Trade 2: pnl = -2000.0 (<=0)
      win_rate = 1 / 2 = 0.50
    """
    curve = [
        EquityPoint(date=date(2023, 1, 1), equity=100000.0),
        EquityPoint(date=date(2023, 5, 1), equity=105000.0),
        EquityPoint(date=date(2023, 9, 1), equity=95000.0),
        EquityPoint(date=date(2024, 1, 1), equity=110000.0),
    ]

    trades = [
        TradeRecord(date(2023, 1, 2), date(2023, 5, 1), 100.0, 105.0, 1000, 5000.0),
        TradeRecord(date(2023, 5, 2), date(2023, 9, 1), 105.0, 95.0, 200, -2000.0),
    ]

    run = DummyRun(start_date=date(2023, 1, 1), end_date=date(2024, 1, 1))

    m = MetricsCalculator.calculate(trades, run, curve)

    assert m.total_return == pytest.approx(0.10, rel=1e-3)
    assert m.max_drawdown == pytest.approx(-0.095238, rel=1e-3)
    assert m.win_rate == 0.50
    assert m.cagr == pytest.approx(0.10, rel=1e-2)
    assert isinstance(m.sharpe_ratio, float)

def test_metrics_flat_equity_produces_zero_drawdown():
    curve = [
        EquityPoint(date=date(2024, 1, 1), equity=100000.0),
        EquityPoint(date=date(2024, 1, 2), equity=100000.0),
        EquityPoint(date=date(2024, 1, 3), equity=100000.0),
    ]
    run = DummyRun(date(2024, 1, 1), date(2024, 1, 3))
    m = MetricsCalculator.calculate([], run, curve)

    assert m.max_drawdown == 0.0
    assert m.total_return == 0.0
    assert m.win_rate == 0.0
