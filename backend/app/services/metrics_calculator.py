# STUB, owned by Molik, replaced on merge
import math
import numpy as np
from app.domain import TradeRecord, EquityPoint, MetricsResult

class MetricsCalculator:
    """
    Calculates quantitative metrics according to Trading Rule 6:
    - total_return = final_equity / initial - 1
    - cagr = (final_equity / initial) ^ (365.25 / calendar_days) - 1
    - sharpe_ratio = sqrt(252) * mean(daily_returns) / std(daily_returns, ddof=1)
    - max_drawdown = min(equity / running_peak - 1)
    - win_rate = trades with pnl > 0 / total trades
    """

    @classmethod
    def calculate(
        cls,
        trades: list[TradeRecord],
        run,
        equity_curve: list[EquityPoint],
    ) -> MetricsResult:
        if not equity_curve:
            return MetricsResult(
                sharpe_ratio=0.0,
                max_drawdown=0.0,
                win_rate=0.0,
                cagr=0.0,
                total_return=0.0,
            )

        initial = equity_curve[0].equity
        final = equity_curve[-1].equity

        # 1. Total Return
        total_return = (final / initial - 1.0) if initial > 0 else 0.0

        # 2. CAGR
        start_date = getattr(run, "start_date", None)
        end_date = getattr(run, "end_date", None)
        cagr = 0.0
        if start_date and end_date and initial > 0 and final > 0:
            calendar_days = (end_date - start_date).days
            if calendar_days > 0:
                cagr = math.pow(final / initial, 365.25 / calendar_days) - 1.0

        # 3. Sharpe Ratio
        equities = [p.equity for p in equity_curve]
        if len(equities) >= 3:  # At least 2 daily returns
            daily_returns = [
                (equities[i] - equities[i - 1]) / equities[i - 1]
                for i in range(1, len(equities))
                if equities[i - 1] > 0
            ]
            if len(daily_returns) >= 2:
                mean_r = float(np.mean(daily_returns))
                std_r = float(np.std(daily_returns, ddof=1))
                if std_r > 1e-9:
                    sharpe_ratio = math.sqrt(252) * mean_r / std_r
                else:
                    sharpe_ratio = 0.0
            else:
                sharpe_ratio = 0.0
        else:
            sharpe_ratio = 0.0

        # 4. Max Drawdown
        running_peak = equities[0]
        min_drawdown = 0.0
        for eq in equities:
            if eq > running_peak:
                running_peak = eq
            if running_peak > 0:
                dd = (eq / running_peak) - 1.0
                if dd < min_drawdown:
                    min_drawdown = dd
        max_drawdown = min_drawdown

        # 5. Win Rate
        if trades:
            winning_trades = sum(1 for t in trades if t.pnl > 0)
            win_rate = winning_trades / len(trades)
        else:
            win_rate = 0.0

        return MetricsResult(
            sharpe_ratio=float(sharpe_ratio),
            max_drawdown=float(max_drawdown),
            win_rate=float(win_rate),
            cagr=float(cagr),
            total_return=float(total_return),
        )
