"""
tests/test_metrics_calculator.py
Tests for MetricsCalculator (Milestone 2).

All expected values are hand-calculated in the comments above each assertion.
"""
import math
from dataclasses import dataclass
from datetime import date, timedelta

import pytest

from app.domain import EquityPoint, TradeRecord
from app.services.metrics_calculator import MetricsCalculator


# ---------------------------------------------------------------------------
# Minimal stand-in for a backtest run (needs .start_date, .end_date)
# ---------------------------------------------------------------------------

@dataclass
class FakeRun:
    start_date: date
    end_date: date


calc = MetricsCalculator()


def _ep(dates_and_equities):
    """Build a list of EquityPoint from [(date, equity), ...]."""
    return [EquityPoint(date=d, equity=e) for d, e in dates_and_equities]


# ---------------------------------------------------------------------------
# Shared fixture: 4-point equity curve [100000, 101000, 99000, 102000]
# ---------------------------------------------------------------------------

CURVE_4 = _ep([
    (date(2023, 1, 2), 100_000.0),
    (date(2023, 1, 3), 101_000.0),
    (date(2023, 1, 4),  99_000.0),
    (date(2023, 1, 5), 102_000.0),
])

RUN_4 = FakeRun(start_date=date(2023, 1, 2), end_date=date(2023, 1, 5))


class TestTotalReturn:
    def test_four_point_curve(self):
        # total_return = 102000 / 100000 - 1 = 0.02
        result = calc._total_return(CURVE_4)
        assert abs(result - 0.02) < 1e-10

    def test_zero_equity_points(self):
        # fewer than 2 → 0.0
        assert calc._total_return([]) == 0.0

    def test_single_equity_point(self):
        assert calc._total_return([EquityPoint(date(2023, 1, 1), 100_000.0)]) == 0.0

    def test_initial_equity_zero(self):
        pts = _ep([(date(2023, 1, 1), 0.0), (date(2023, 1, 2), 100.0)])
        assert calc._total_return(pts) == 0.0

    def test_always_losing(self):
        # 100000 → 90000 → total_return = -0.1
        pts = _ep([(date(2023, 1, 1), 100_000.0), (date(2023, 1, 2), 90_000.0)])
        assert abs(calc._total_return(pts) - (-0.1)) < 1e-10

    def test_flat(self):
        pts = _ep([(date(2023, 1, 1), 100_000.0), (date(2023, 1, 2), 100_000.0)])
        assert calc._total_return(pts) == 0.0


class TestMaxDrawdown:
    def test_four_point_curve(self):
        # peak after bar 2 = 101000, then 99000 → dd = 99000/101000 - 1 ≈ -0.01980198
        result = calc._max_drawdown(CURVE_4)
        expected = 99_000 / 101_000 - 1  # ≈ -0.019801980198
        assert abs(result - expected) < 1e-8

    def test_always_rising(self):
        # never falls below running peak → 0.0
        pts = _ep([
            (date(2023, 1, 1), 100_000.0),
            (date(2023, 1, 2), 101_000.0),
            (date(2023, 1, 3), 102_000.0),
        ])
        assert calc._max_drawdown(pts) == 0.0

    def test_empty_curve(self):
        assert calc._max_drawdown([]) == 0.0

    def test_single_point(self):
        pts = [EquityPoint(date(2023, 1, 1), 100_000.0)]
        assert calc._max_drawdown(pts) == 0.0

    def test_always_losing_run(self):
        # 100000 → 80000, drawdown = 80000/100000 - 1 = -0.2
        pts = _ep([(date(2023, 1, 1), 100_000.0), (date(2023, 1, 2), 80_000.0)])
        assert abs(calc._max_drawdown(pts) - (-0.2)) < 1e-10


class TestSharpe:
    def test_four_point_curve(self):
        # daily returns: (101000-100000)/100000 = 0.01,
        #                (99000-101000)/101000  ≈ -0.019802,
        #                (102000-99000)/99000   ≈  0.030303
        # mean ≈ (0.01 - 0.019802 + 0.030303) / 3 ≈ 0.006834
        # variance ddof=1 of 3 values ≈ 0.0006287
        # std ≈ 0.025074
        # sharpe = sqrt(252) * 0.006834 / 0.025074 ≈ 4.325
        r1 = (101_000 - 100_000) / 100_000      #  0.01
        r2 = (99_000  - 101_000) / 101_000      # -0.019802...
        r3 = (102_000 -  99_000) /  99_000      #  0.030303...
        returns = [r1, r2, r3]
        mean_r = sum(returns) / 3
        var = sum((r - mean_r) ** 2 for r in returns) / 2  # ddof=1
        expected = math.sqrt(252) * mean_r / math.sqrt(var)
        result = calc._sharpe(CURVE_4)
        assert abs(result - expected) < 1e-8

    def test_constant_equity_sharpe_zero(self):
        # std of daily returns = 0 → Sharpe = 0.0
        pts = _ep([
            (date(2023, 1, 1), 100_000.0),
            (date(2023, 1, 2), 100_000.0),
            (date(2023, 1, 3), 100_000.0),
        ])
        assert calc._sharpe(pts) == 0.0

    def test_single_point_sharpe_zero(self):
        pts = [EquityPoint(date(2023, 1, 1), 100_000.0)]
        assert calc._sharpe(pts) == 0.0

    def test_two_points_one_return(self):
        # only 1 return → fewer than 2 returns → 0.0
        pts = _ep([(date(2023, 1, 1), 100_000.0), (date(2023, 1, 2), 101_000.0)])
        assert calc._sharpe(pts) == 0.0

    def test_empty_curve_sharpe_zero(self):
        assert calc._sharpe([]) == 0.0


class TestCAGR:
    def test_exactly_365_days(self):
        # 100000 → 110000 over exactly 365 days
        # cagr = (110000/100000)^(365.25/365) - 1 ≈ 0.10068...
        start = date(2023, 1, 1)
        end = date(2024, 1, 1)
        pts = _ep([(start, 100_000.0), (end, 110_000.0)])
        run = FakeRun(start_date=start, end_date=end)
        expected = (110_000 / 100_000) ** (365.25 / 365) - 1
        result = calc._cagr(pts, run)
        assert abs(result - expected) < 1e-8

    def test_exactly_730_days(self):
        # 100000 → 121000 over 730 days
        # cagr = (121000/100000)^(365.25/730) - 1 = (1.21)^0.5003... - 1 ≈ 0.10001...
        start = date(2022, 1, 1)
        end = date(2024, 1, 1)
        pts = _ep([(start, 100_000.0), (end, 121_000.0)])
        run = FakeRun(start_date=start, end_date=end)
        days = (end - start).days  # 730
        expected = (121_000 / 100_000) ** (365.25 / days) - 1
        result = calc._cagr(pts, run)
        assert abs(result - expected) < 1e-8

    def test_zero_calendar_days(self):
        # end == start → 0.0
        d = date(2023, 6, 1)
        pts = _ep([(d, 100_000.0)])
        run = FakeRun(start_date=d, end_date=d)
        assert calc._cagr(pts, run) == 0.0

    def test_negative_calendar_days_guard(self):
        pts = _ep([(date(2023, 1, 1), 100_000.0)])
        run = FakeRun(start_date=date(2023, 6, 1), end_date=date(2023, 1, 1))
        assert calc._cagr(pts, run) == 0.0

    def test_single_point_cagr_zero(self):
        d = date(2023, 1, 1)
        pts = [EquityPoint(d, 100_000.0)]
        run = FakeRun(start_date=d, end_date=date(2023, 12, 31))
        assert calc._cagr(pts, run) == 0.0


class TestWinRate:
    def test_mixed_trades(self):
        # 3 trades, 2 winners (pnl > 0) → win_rate = 2/3 ≈ 0.6667
        trades = [
            TradeRecord(date(2023,1,2), date(2023,1,3), 100.0, 110.0, 10,  100.0),
            TradeRecord(date(2023,1,4), date(2023,1,5), 100.0, 105.0, 10,   50.0),
            TradeRecord(date(2023,1,6), date(2023,1,9), 100.0,  90.0, 10, -100.0),
        ]
        result = calc._win_rate(trades)
        # expected = 2 / 3 ≈ 0.6667
        assert abs(result - 2 / 3) < 1e-10

    def test_no_trades(self):
        assert calc._win_rate([]) == 0.0

    def test_all_losers(self):
        trades = [
            TradeRecord(date(2023,1,1), date(2023,1,2), 100.0, 90.0, 5, -50.0),
        ]
        # 0 winners / 1 trade = 0.0
        assert calc._win_rate(trades) == 0.0

    def test_all_winners(self):
        trades = [
            TradeRecord(date(2023,1,1), date(2023,1,2), 100.0, 110.0, 5, 50.0),
            TradeRecord(date(2023,1,3), date(2023,1,4), 100.0, 115.0, 5, 75.0),
        ]
        # 2/2 = 1.0
        assert calc._win_rate(trades) == 1.0

    def test_pnl_zero_not_a_win(self):
        # pnl == 0 is not > 0, so not a win
        trades = [
            TradeRecord(date(2023,1,1), date(2023,1,2), 100.0, 100.0, 5, 0.0),
        ]
        assert calc._win_rate(trades) == 0.0


class TestEdgeCasesOnFullCalculate:
    def test_zero_trades_no_raise(self):
        """Zero trades must not raise; win_rate = 0."""
        result = calc.calculate([], RUN_4, CURVE_4)
        assert result.win_rate == 0.0

    def test_constant_equity_sharpe_zero(self):
        pts = _ep([
            (date(2023, 1, 2), 100_000.0),
            (date(2023, 1, 3), 100_000.0),
            (date(2023, 1, 4), 100_000.0),
        ])
        run = FakeRun(date(2023, 1, 2), date(2023, 1, 4))
        result = calc.calculate([], run, pts)
        assert result.sharpe_ratio == 0.0

    def test_always_rising_max_drawdown_zero(self):
        pts = _ep([
            (date(2023, 1, 2), 100_000.0),
            (date(2023, 1, 3), 101_000.0),
            (date(2023, 1, 4), 102_000.0),
        ])
        run = FakeRun(date(2023, 1, 2), date(2023, 1, 4))
        result = calc.calculate([], run, pts)
        assert result.max_drawdown == 0.0

    def test_result_has_all_fields(self):
        result = calc.calculate([], RUN_4, CURVE_4)
        for attr in ("sharpe_ratio", "max_drawdown", "win_rate", "cagr", "total_return"):
            assert hasattr(result, attr)
            assert isinstance(getattr(result, attr), float)

    def test_no_nan_or_inf_returned(self):
        """No field may be NaN or Inf, even for degenerate inputs."""
        result = calc.calculate([], RUN_4, CURVE_4)
        for attr in ("sharpe_ratio", "max_drawdown", "win_rate", "cagr", "total_return"):
            v = getattr(result, attr)
            assert not math.isnan(v), f"{attr} is NaN"
            assert not math.isinf(v), f"{attr} is Inf"
