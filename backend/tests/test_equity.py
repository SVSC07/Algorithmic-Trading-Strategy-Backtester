"""
Unit tests for Equity Curve Calculation.
Owned by Shaurya.
"""
from datetime import date
import pandas as pd
from app.domain import TradeRecord
from app.services.equity import build_equity_curve

def test_build_equity_curve_hand_calculated():
    """
    HAND CALCULATION:
    Initial capital: 100,000.0
    Price Series (4 days):
      2024-01-01: close = 100.0 (Flat -> equity = 100,000.0)
      2024-01-02: close = 100.0 (Buy filled at close @ 100.0, qty = 1000)
                                 Holding: equity = cash + qty*(close - entry) = 100,000 + 1000*(100-100) = 100,000.0
      2024-01-03: close = 110.0 (Holding: equity = 100,000 + 1000*(110-100) = 110,000.0)
      2024-01-04: close = 120.0 (Sell filled at close @ 120.0)
                                 pnl = (120 - 100) * 1000 = +20,000.0
                                 Trade completed: cash = 120,000.0, flat -> equity = 120,000.0
    """
    df = pd.DataFrame({
        "date": pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04"]),
        "open": [100.0, 100.0, 105.0, 115.0],
        "high": [102.0, 102.0, 112.0, 122.0],
        "low": [98.0, 98.0, 103.0, 114.0],
        "close": [100.0, 100.0, 110.0, 120.0],
        "volume": [1000.0] * 4,
    })

    trade = TradeRecord(
        entry_date=date(2024, 1, 2),
        exit_date=date(2024, 1, 4),
        entry_price=100.0,
        exit_price=120.0,
        quantity=1000,
        pnl=20000.0,
    )

    curve = build_equity_curve(df, [trade], initial_capital=100000.0)

    assert len(curve) == 4
    assert curve[0].date == date(2024, 1, 1)
    assert curve[0].equity == 100000.0

    assert curve[1].date == date(2024, 1, 2)
    assert curve[1].equity == 100000.0

    assert curve[2].date == date(2024, 1, 3)
    assert curve[2].equity == 110000.0

    assert curve[3].date == date(2024, 1, 4)
    assert curve[3].equity == 120000.0

def test_build_equity_curve_empty():
    assert build_equity_curve(pd.DataFrame(), []) == []
