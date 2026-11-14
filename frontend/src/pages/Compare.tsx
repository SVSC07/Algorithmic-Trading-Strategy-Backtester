import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import type { RunSummary, RunDetail } from '../types/api';
import { listBacktests, compareBacktests } from '../api/backtests';
import { formatPercent, formatSharpe, formatCurrency } from '../lib/format';
import { ApiError } from '../api/http';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { GitCompare } from 'lucide-react';

export const Compare: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [recentRuns, setRecentRuns] = useState<RunSummary[]>([]);
  const [runAId, setRunAId] = useState<number | ''>('');
  const [runBId, setRunBId] = useState<number | ''>('');

  const [compareData, setCompareData] = useState<{ run_a: RunDetail; run_b: RunDetail } | null>(null);
  const [loading, setLoading] = useState(false);
  const [initialLoading, setInitialLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchRuns = async () => {
      try {
        setInitialLoading(true);
        const runs = await listBacktests();
        setRecentRuns(runs);

        const paramA = searchParams.get('runA');
        const paramB = searchParams.get('runB');

        const initialA = paramA ? Number(paramA) : (runs[0]?.run_id ?? '');
        const initialB = paramB ? Number(paramB) : (runs[1]?.run_id ?? runs[0]?.run_id ?? '');

        setRunAId(initialA);
        setRunBId(initialB);

        if (initialA && initialB) {
          executeCompare(Number(initialA), Number(initialB));
        }
      } catch (err) {
        if (err instanceof ApiError) setError(err.message);
        else setError('Failed to load recent backtests');
      } finally {
        setInitialLoading(false);
      }
    };

    fetchRuns();
  }, []);

  const executeCompare = async (a: number, b: number) => {
    try {
      setLoading(true);
      setError(null);
      const res = await compareBacktests(a, b);
      setCompareData(res);
      setSearchParams({ runA: String(a), runB: String(b) });
    } catch (err) {
      if (err instanceof ApiError) setError(err.message);
      else setError('Failed to compare backtest runs');
    } finally {
      setLoading(false);
    }
  };

  const handleRunChange = (type: 'A' | 'B', val: number) => {
    if (type === 'A') {
      setRunAId(val);
      if (runBId) executeCompare(val, Number(runBId));
    } else {
      setRunBId(val);
      if (runAId) executeCompare(Number(runAId), val);
    }
  };

  // Merge equity curve data by date (declared before any early returns to respect Rules of Hooks)
  const chartData = React.useMemo(() => {
    if (!compareData) return [];
    const map = new Map<string, { date: string; equity_a?: number; equity_b?: number }>();

    compareData.run_a.equity_curve.forEach((pt) => {
      map.set(pt.date, { date: pt.date, equity_a: pt.equity });
    });

    compareData.run_b.equity_curve.forEach((pt) => {
      const existing = map.get(pt.date);
      if (existing) {
        existing.equity_b = pt.equity;
      } else {
        map.set(pt.date, { date: pt.date, equity_b: pt.equity });
      }
    });

    return Array.from(map.values()).sort((a, b) => a.date.localeCompare(b.date));
  }, [compareData]);

  if (initialLoading) {
    return <div className="empty-state">Loading comparison workspace...</div>;
  }

  const mA = compareData?.run_a.metrics;
  const mB = compareData?.run_b.metrics;

  const metricsRows = [
    {
      name: 'Total Return',
      valA: mA ? formatPercent(mA.total_return, { showPositiveSign: true }) : '—',
      valB: mB ? formatPercent(mB.total_return, { showPositiveSign: true }) : '—',
      diff: mA && mB ? mA.total_return - mB.total_return : 0,
      diffFormatted: mA && mB ? formatPercent(mA.total_return - mB.total_return, { showPositiveSign: true }) : '—',
    },
    {
      name: 'CAGR',
      valA: mA ? formatPercent(mA.cagr, { showPositiveSign: true }) : '—',
      valB: mB ? formatPercent(mB.cagr, { showPositiveSign: true }) : '—',
      diff: mA && mB ? mA.cagr - mB.cagr : 0,
      diffFormatted: mA && mB ? formatPercent(mA.cagr - mB.cagr, { showPositiveSign: true }) : '—',
    },
    {
      name: 'Sharpe Ratio',
      valA: mA ? formatSharpe(mA.sharpe_ratio) : '—',
      valB: mB ? formatSharpe(mB.sharpe_ratio) : '—',
      diff: mA && mB ? mA.sharpe_ratio - mB.sharpe_ratio : 0,
      diffFormatted: mA && mB ? (mA.sharpe_ratio - mB.sharpe_ratio >= 0 ? `+${(mA.sharpe_ratio - mB.sharpe_ratio).toFixed(2)}` : (mA.sharpe_ratio - mB.sharpe_ratio).toFixed(2)) : '—',
    },
    {
      name: 'Max Drawdown',
      valA: mA ? formatPercent(mA.max_drawdown) : '—',
      valB: mB ? formatPercent(mB.max_drawdown) : '—',
      diff: mA && mB ? mA.max_drawdown - mB.max_drawdown : 0,
      diffFormatted: mA && mB ? formatPercent(mA.max_drawdown - mB.max_drawdown, { showPositiveSign: true }) : '—',
    },
    {
      name: 'Win Rate',
      valA: mA ? formatPercent(mA.win_rate) : '—',
      valB: mB ? formatPercent(mB.win_rate) : '—',
      diff: mA && mB ? mA.win_rate - mB.win_rate : 0,
      diffFormatted: mA && mB ? formatPercent(mA.win_rate - mB.win_rate, { showPositiveSign: true }) : '—',
    },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Title */}
      <div>
        <h1 style={{ fontSize: '26px', fontWeight: 700, color: 'var(--text-main)', letterSpacing: '-0.02em' }}>
          Strategy Comparison
        </h1>
        <p style={{ fontSize: '14px', color: 'var(--text-muted)', marginTop: '4px' }}>
          Compare performance metrics and equity trajectories between two backtest runs (FR-7).
        </p>
      </div>

      {error && <div className="alert-error">{error}</div>}

      {/* Selectors Card */}
      <div className="card">
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '18px' }}>
          <GitCompare size={20} color="var(--accent-dark)" />
          <h2 style={{ fontSize: '18px', fontWeight: 600 }}>Select Runs to Compare</h2>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '20px' }}>
          {/* Run A select */}
          <div className="form-group">
            <label className="form-label" htmlFor="select-run-a">
              <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: 'var(--accent-dark)' }} />
                Run A (Accent Curve)
              </span>
            </label>
            <select
              id="select-run-a"
              className="form-select"
              value={runAId}
              onChange={(e) => handleRunChange('A', Number(e.target.value))}
            >
              {recentRuns.map((r) => (
                <option key={`a-${r.run_id}`} value={r.run_id}>
                  #{r.run_id} — {r.ticker} ({r.strategy_type === 'MOVING_AVERAGE_CROSSOVER' ? 'MA Crossover' : 'Mean Rev'}) | Return: {formatPercent(r.total_return, { showPositiveSign: true })}
                </option>
              ))}
            </select>
          </div>

          {/* Run B select */}
          <div className="form-group">
            <label className="form-label" htmlFor="select-run-b">
              <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: 'var(--text-muted)' }} />
                Run B (Muted Curve)
              </span>
            </label>
            <select
              id="select-run-b"
              className="form-select"
              value={runBId}
              onChange={(e) => handleRunChange('B', Number(e.target.value))}
            >
              {recentRuns.map((r) => (
                <option key={`b-${r.run_id}`} value={r.run_id}>
                  #{r.run_id} — {r.ticker} ({r.strategy_type === 'MOVING_AVERAGE_CROSSOVER' ? 'MA Crossover' : 'Mean Rev'}) | Return: {formatPercent(r.total_return, { showPositiveSign: true })}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {loading && <div className="empty-state">Calculating differential analysis...</div>}

      {compareData && (
        <>
          {/* Dual Metrics Table Card */}
          <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px' }}>
              <div>
                <h2 style={{ fontSize: '18px', fontWeight: 600 }}>Comparative Performance Metrics</h2>
                <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                  Two metric columns side-by-side with difference Δ (Run A minus Run B)
                </span>
              </div>
            </div>

            <div className="table-container">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Metric</th>
                    <th className="text-right">
                      Run A (#{compareData.run_a.run.run_id} {compareData.run_a.instrument.ticker})
                    </th>
                    <th className="text-right">
                      Run B (#{compareData.run_b.run.run_id} {compareData.run_b.instrument.ticker})
                    </th>
                    <th className="text-right">Difference (Δ A - B)</th>
                  </tr>
                </thead>
                <tbody>
                  {metricsRows.map((row) => {
                    const isDiffPositive = row.diff > 0;
                    const isDiffZero = row.diff === 0;
                    return (
                      <tr key={row.name}>
                        <td style={{ fontWeight: 600 }}>{row.name}</td>
                        <td className="text-right tabular-nums" style={{ fontWeight: 600 }}>
                          {row.valA}
                        </td>
                        <td className="text-right tabular-nums" style={{ color: 'var(--text-muted)' }}>
                          {row.valB}
                        </td>
                        <td
                          className="text-right tabular-nums"
                          style={{
                            fontWeight: 700,
                            color: isDiffZero
                              ? 'var(--text-muted)'
                              : isDiffPositive
                              ? 'var(--gain)'
                              : 'var(--loss)',
                          }}
                        >
                          {row.diffFormatted}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* Dual Equity Curves Chart Card */}
          <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px', flexWrap: 'wrap', gap: '10px' }}>
              <div>
                <h2 style={{ fontSize: '18px', fontWeight: 600 }}>Comparative Equity Curves</h2>
                <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                  Run A (Accent) vs Run B (Muted)
                </span>
              </div>

              {/* Chart Legend */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '16px', fontSize: '12px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span style={{ width: '12px', height: '3px', background: 'var(--accent-dark)', borderRadius: '2px' }} />
                  <span style={{ fontWeight: 600 }}>Run A (#{compareData.run_a.run.run_id})</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span style={{ width: '12px', height: '3px', background: 'var(--text-muted)', borderRadius: '2px' }} />
                  <span style={{ color: 'var(--text-muted)' }}>Run B (#{compareData.run_b.run.run_id})</span>
                </div>
              </div>
            </div>

            <div style={{ width: '100%', height: '360px' }}>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData} margin={{ top: 10, right: 20, left: 20, bottom: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border)" opacity={0.6} />
                  <XAxis
                    dataKey="date"
                    stroke="var(--text-muted)"
                    fontSize={12}
                    tickLine={false}
                    minTickGap={35}
                  />
                  <YAxis
                    stroke="var(--text-muted)"
                    fontSize={12}
                    tickLine={false}
                    axisLine={false}
                    domain={['auto', 'auto']}
                    tickFormatter={(v) => `₹${(v / 1000).toFixed(0)}k`}
                  />
                  <Tooltip
                    content={({ active, payload, label }) => {
                      if (active && payload && payload.length) {
                        return (
                          <div
                            style={{
                              background: 'var(--accent-dark)',
                              color: '#FFFFFF',
                              padding: '12px 16px',
                              borderRadius: '12px',
                              boxShadow: 'var(--shadow-card)',
                              fontSize: '13px',
                            }}
                          >
                            <div style={{ opacity: 0.7, fontSize: '11px', marginBottom: '6px' }}>{label}</div>
                            {payload.map((entry, idx) => (
                              <div
                                key={`tooltip-${idx}`}
                                style={{
                                  display: 'flex',
                                  alignItems: 'center',
                                  justifyContent: 'space-between',
                                  gap: '16px',
                                  marginBottom: '3px',
                                  color: entry.name === 'Run A' ? 'var(--accent-lime)' : '#E5E7EB',
                                }}
                              >
                                <span>{entry.name}:</span>
                                <span style={{ fontWeight: 600 }}>{formatCurrency(entry.value as number)}</span>
                              </div>
                            ))}
                          </div>
                        );
                      }
                      return null;
                    }}
                  />
                  <Line
                    type="monotone"
                    name="Run A"
                    dataKey="equity_a"
                    stroke="var(--accent-dark)"
                    strokeWidth={2.8}
                    dot={false}
                    activeDot={{ r: 5, fill: 'var(--accent-lime)', stroke: 'var(--accent-dark)', strokeWidth: 2 }}
                  />
                  <Line
                    type="monotone"
                    name="Run B"
                    dataKey="equity_b"
                    stroke="var(--text-muted)"
                    strokeWidth={2}
                    strokeDasharray="4 4"
                    dot={false}
                    activeDot={{ r: 5, fill: 'var(--text-muted)' }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </>
      )}
    </div>
  );
};
