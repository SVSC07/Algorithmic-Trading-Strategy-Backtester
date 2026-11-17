"""
services/metrics_calculator.py
Stateless MetricsCalculator — implements TRADING RULE 6 exactly.

All metrics are decimal fractions (never percents). Every division is guarded
so edge cases (zero trades, constant equity, single point, zero calendar days,
NaN/inf) always return 0.0 instead of raising or propagating NaN.
"""
import math
from typing import List

from app.domain import EquityPoint, MetricsResult, TradeRecord


class MetricsCalculator:
    """
    calculate(trades, run, equity_curve) -> MetricsResult

    *run* only needs to expose `.start_date` and `.end_date` (date objects).
    *equity_curve* is a list of EquityPoint ordered by date.
    """

    def calculate(
        self,
        trades: List[TradeRecord],
        run,
        equity_curve: List[EquityPoint],
    ) -> MetricsResult:
        """Return MetricsResult for a completed backtest run."""
        return MetricsResult(
            total_return=self._total_return(equity_curve),
            cagr=self._cagr(equity_curve, run),
            sharpe_ratio=self._sharpe(equity_curve),
            max_drawdown=self._max_drawdown(equity_curve),
            win_rate=self._win_rate(trades),
        )

    # ------------------------------------------------------------------
    # Private formula helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _total_return(equity_curve: List[EquityPoint]) -> float:
        """
        total_return = final_equity / initial_equity - 1.
        Returns 0.0 if fewer than 2 points or initial equity is 0.
        """
        if len(equity_curve) < 2:
            return 0.0
        initial = equity_curve[0].equity
        final = equity_curve[-1].equity
        if initial == 0.0:
            return 0.0
        result = final / initial - 1.0
        return 0.0 if (math.isnan(result) or math.isinf(result)) else result

    @staticmethod
    def _cagr(equity_curve: List[EquityPoint], run) -> float:
        """
        cagr = (final / initial) ^ (365.25 / calendar_days) - 1.
        calendar_days = (end_date - start_date).days.
        Returns 0.0 if calendar_days <= 0, fewer than 2 points, or initial == 0.
        """
        if len(equity_curve) < 2:
            return 0.0
        calendar_days = (run.end_date - run.start_date).days
        if calendar_days <= 0:
            return 0.0
        initial = equity_curve[0].equity
        final = equity_curve[-1].equity
        if initial == 0.0:
            return 0.0
        try:
            result = (final / initial) ** (365.25 / calendar_days) - 1.0
        except (ZeroDivisionError, OverflowError, ValueError):
            return 0.0
        return 0.0 if (math.isnan(result) or math.isinf(result)) else result

    @staticmethod
    def _sharpe(equity_curve: List[EquityPoint]) -> float:
        """
        sharpe_ratio = sqrt(252) * mean(daily_returns) / std(daily_returns, ddof=1).
        daily_returns = day-over-day percentage changes of equity.
        Returns 0.0 if fewer than 2 returns or std == 0.
        """
        equities = [pt.equity for pt in equity_curve]
        if len(equities) < 2:
            return 0.0
        # percentage changes: (e[i] - e[i-1]) / e[i-1]
        returns: List[float] = []
        for i in range(1, len(equities)):
            prev = equities[i - 1]
            if prev == 0.0:
                returns.append(0.0)
            else:
                returns.append((equities[i] - prev) / prev)
        if len(returns) < 2:
            return 0.0
        n = len(returns)
        mean_r = sum(returns) / n
        variance = sum((r - mean_r) ** 2 for r in returns) / (n - 1)
        if variance == 0.0:
            return 0.0
        std_r = math.sqrt(variance)
        result = math.sqrt(252) * mean_r / std_r
        return 0.0 if (math.isnan(result) or math.isinf(result)) else result

    @staticmethod
    def _max_drawdown(equity_curve: List[EquityPoint]) -> float:
        """
        max_drawdown = min(equity / running_peak - 1).
        e.g. -0.186. Returns 0.0 if equity never falls below the running peak.
        """
        if not equity_curve:
            return 0.0
        peak = equity_curve[0].equity
        min_dd = 0.0
        for pt in equity_curve:
            if pt.equity > peak:
                peak = pt.equity
            if peak > 0.0:
                dd = pt.equity / peak - 1.0
                if dd < min_dd:
                    min_dd = dd
        return 0.0 if (math.isnan(min_dd) or math.isinf(min_dd)) else min_dd

    @staticmethod
    def _win_rate(trades: List[TradeRecord]) -> float:
        """
        win_rate = trades with pnl > 0 / total trades.
        Returns 0.0 if no trades.
        """
        if not trades:
            return 0.0
        winners = sum(1 for t in trades if t.pnl > 0)
        return winners / len(trades)
