from datetime import date
import pandas as pd
from app.domain import TradeRecord, EquityPoint

def _to_date(val) -> date:
    if hasattr(val, "date") and callable(val.date):
        return val.date()
    if isinstance(val, date):
        return val
    return pd.to_datetime(val).date()

def build_equity_curve(
    price_data: pd.DataFrame,
    trades: list[TradeRecord],
    initial_capital: float = 100000.0,
) -> list[EquityPoint]:
    """
    Build the equity curve with one point per trading day in the range.
    Rule 3:
    Equity equals cash while flat and cash + quantity * (close - entry_price) while holding.
    A signal fills at the close of its date.
    """
    if price_data is None or price_data.empty:
        return []

    # Sort trades chronologically
    sorted_trades = sorted(trades, key=lambda t: (t.entry_date, t.exit_date))

    curve: list[EquityPoint] = []
    current_cash = float(initial_capital)
    trade_idx = 0
    n_trades = len(sorted_trades)

    for i in range(len(price_data)):
        row = price_data.iloc[i]
        d = _to_date(row["date"])
        close = float(row["close"])

        # Check if we have an active or upcoming trade
        if trade_idx < n_trades:
            curr_trade = sorted_trades[trade_idx]

            if d < curr_trade.entry_date:
                # Flat before trade entry
                equity = current_cash
            elif curr_trade.entry_date <= d < curr_trade.exit_date:
                # Holding position
                equity = current_cash + curr_trade.quantity * (close - curr_trade.entry_price)
            elif d == curr_trade.exit_date:
                # Trade completes on this bar at close
                current_cash += curr_trade.pnl
                equity = current_cash
                trade_idx += 1
                # In case subsequent trades immediately start (edge cases)
                while trade_idx < n_trades and sorted_trades[trade_idx].exit_date < d:
                    current_cash += sorted_trades[trade_idx].pnl
                    equity = current_cash
                    trade_idx += 1
            else:
                # d is past curr_trade.exit_date, advance until relevant
                while trade_idx < n_trades and sorted_trades[trade_idx].exit_date <= d:
                    current_cash += sorted_trades[trade_idx].pnl
                    trade_idx += 1
                
                if trade_idx < n_trades:
                    next_trade = sorted_trades[trade_idx]
                    if d < next_trade.entry_date:
                        equity = current_cash
                    elif next_trade.entry_date <= d < next_trade.exit_date:
                        equity = current_cash + next_trade.quantity * (close - next_trade.entry_price)
                    else:
                        current_cash += next_trade.pnl
                        equity = current_cash
                        trade_idx += 1
                else:
                    equity = current_cash
        else:
            # All trades completed, flat
            equity = current_cash

        curve.append(EquityPoint(date=d, equity=equity))

    return curve
