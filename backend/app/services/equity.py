# STUB — owned by Shaurya, replaced on merge
"""
services/equity.py
build_equity_curve stub — real implementation owned by Shaurya.
"""
import math
from datetime import date, timedelta
from typing import List

import pandas as pd

from app.domain import EquityPoint, TradeRecord


def build_equity_curve(
    price_data: pd.DataFrame,
    trades: List[TradeRecord],
    initial_capital: float = 100_000.0,
) -> List[EquityPoint]:
    """
    Build a daily equity curve (one point per trading day).

    TRADING RULE 3:
    - Equity = cash while flat.
    - Equity = cash + quantity * (close - entry_price) while holding.
    Initial capital = 100_000.0.
    """
    if price_data.empty:
        return []

    # Build a quick lookup from trade exit_date → trade for fast access
    # Sort trades by entry_date for linear sweep
    sorted_trades = sorted(trades, key=lambda t: t.entry_date)
    trade_idx = 0

    cash = initial_capital
    holding: bool = False
    current_trade: "TradeRecord | None" = None

    curve: List[EquityPoint] = []

    for _, row in price_data.iterrows():
        bar_date: date = row["date"].date() if hasattr(row["date"], "date") else row["date"]
        close: float = float(row["close"])

        # Check if a new trade starts on this bar
        if not holding and trade_idx < len(sorted_trades):
            t = sorted_trades[trade_idx]
            if t.entry_date == bar_date:
                holding = True
                current_trade = t

        # Check if the current trade exits on this bar
        if holding and current_trade is not None and current_trade.exit_date == bar_date:
            cash = cash + current_trade.pnl
            holding = False
            current_trade = None
            trade_idx += 1

        # Compute equity
        if holding and current_trade is not None:
            equity = cash + current_trade.quantity * (close - current_trade.entry_price)
        else:
            equity = cash

        curve.append(EquityPoint(date=bar_date, equity=equity))

    return curve
