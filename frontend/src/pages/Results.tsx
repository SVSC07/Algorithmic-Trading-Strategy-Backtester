import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import type { RunDetail } from '../types/api';
import { getBacktest } from '../api/backtests';
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
import {
  TrendingUp,
  Percent,
  Activity,
  ArrowDownRight,
  Target,
  ArrowLeft,
  Calendar,
  Layers,
  ArrowUpRight,
} from 'lucide-react';

export const Results: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [data, setData] = useState<RunDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const navigate = useNavigate();

  useEffect(() => {
    const fetchRun = async () => {
      if (!id) return;
      try {
        setLoading(true);
        const detail = await getBacktest(Number(id));
        setData(detail);
      } catch (err) {
        if (err instanceof ApiError) setError(err.message);
        else setError('Failed to load backtest results');
      } finally {
        setLoading(false);
      }
    };

    fetchRun();
  }, [id]);

  if (loading) {
    return <div className="empty-state">Loading simulation telemetry and equity trajectory...</div>;
  }

  if (error || !data) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <div className="alert-error">{error || 'Run details not found'}</div>
        <button onClick={() => navigate('/run')} className="btn btn-secondary" style={{ width: 'fit-content' }}>
          <ArrowLeft size={16} />
          <span>Back to Runs</span>
        </button>
      </div>
    );
  }

  const { run, strategy, instrument, metrics, trades, equity_curve } = data;

  // Set of dates for entry and exit markers
  const entryDates = new Set(trades.map((t) => t.entry_date));
  const exitDates = new Set(trades.map((t) => t.exit_date));

  // Custom Dot renderer for Recharts: filled dot for entry, hollow for exit
  const renderCustomDot = (props: any) => {
    const { cx, cy, payload } = props;
    if (!payload) return null;

    const isEntry = entryDates.has(payload.date);
    const isExit = exitDates.has(payload.date);

    if (isEntry) {
      return (
        <circle
          key={`entry-${payload.date}`}
          cx={cx}
          cy={cy}
          r={5}
          fill="var(--gain)"
          stroke="#FFFFFF"
          strokeWidth={2}
        />
      );
    }

    if (isExit) {
      return (
        <circle
          key={`exit-${payload.date}`}
          cx={cx}
          cy={cy}
          r={5}
          fill="#FFFFFF"
          stroke="var(--loss)"
          strokeWidth={2}
        />
      );
    }

    return null;
  };

  const isPositiveReturn = metrics.total_return >= 0;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Top Header & Breadcrumbs */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <button
              onClick={() => navigate('/run')}
              className="btn btn-secondary"
              style={{ padding: '6px 12px', fontSize: '12px' }}
            >
              <ArrowLeft size={14} />
              <span>Back</span>
            </button>
            <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
              Run ID #{run.run_id}
            </span>
          </div>
          <h1 style={{ fontSize: '26px', fontWeight: 700, color: 'var(--text-main)', letterSpacing: '-0.02em' }}>
            {instrument.ticker} Backtest Performance
          </h1>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginTop: '4px' }}>
            <span style={{ fontSize: '13px', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '4px' }}>
              <Layers size={14} />
              {strategy.strategy_type === 'MOVING_AVERAGE_CROSSOVER'
                ? `SMA Crossover (${(strategy.parameters as any).short_window}/${(strategy.parameters as any).long_window})`
                : `Mean Reversion (lookback ${(strategy.parameters as any).lookback_period})`}
            </span>
            <span style={{ fontSize: '13px', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '4px' }}>
              <Calendar size={14} />
              {run.start_date} to {run.end_date}
            </span>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '10px' }}>
          <button
            onClick={() => navigate(`/compare?runA=${run.run_id}&runB=2`)}
            className="btn btn-secondary"
          >
            <span>Compare Run</span>
            <ArrowUpRight size={15} />
          </button>
        </div>
      </div>

      {/* Contract: A row of five figures (Total Return, CAGR, Sharpe Ratio, Max Drawdown, Win Rate) */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))', gap: '16px' }}>
        {/* Metric 1: Total Return */}
        <div className="card" style={{ padding: '18px 20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-muted)' }}>
              TOTAL RETURN
            </span>
            <div
              style={{
                width: '28px',
                height: '28px',
                borderRadius: '50%',
                background: isPositiveReturn ? 'var(--gain-bg)' : 'var(--loss-bg)',
                color: isPositiveReturn ? 'var(--gain-text)' : 'var(--loss-text)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <TrendingUp size={15} />
            </div>
          </div>
          <div
            className="tabular-nums"
            style={{
              fontSize: '24px',
              fontWeight: 700,
              color: isPositiveReturn ? 'var(--gain)' : 'var(--loss)',
            }}
          >
            {formatPercent(metrics.total_return, { showPositiveSign: true })}
          </div>
        </div>

        {/* Metric 2: CAGR */}
        <div className="card" style={{ padding: '18px 20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-muted)' }}>
              CAGR
            </span>
            <div
              style={{
                width: '28px',
                height: '28px',
                borderRadius: '50%',
                background: 'var(--bg-subtle)',
                color: 'var(--text-main)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <Percent size={15} />
            </div>
          </div>
          <div className="tabular-nums" style={{ fontSize: '24px', fontWeight: 700, color: 'var(--text-main)' }}>
            {formatPercent(metrics.cagr, { showPositiveSign: true })}
          </div>
        </div>

        {/* Metric 3: Sharpe Ratio */}
        <div className="card" style={{ padding: '18px 20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-muted)' }}>
              SHARPE RATIO
            </span>
            <div
              style={{
                width: '28px',
                height: '28px',
                borderRadius: '50%',
                background: 'var(--accent-lime)',
                color: 'var(--accent-dark)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <Activity size={15} />
            </div>
          </div>
          <div className="tabular-nums" style={{ fontSize: '24px', fontWeight: 700, color: 'var(--text-main)' }}>
            {formatSharpe(metrics.sharpe_ratio)}
          </div>
        </div>

        {/* Metric 4: Max Drawdown */}
        <div className="card" style={{ padding: '18px 20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-muted)' }}>
              MAX DRAWDOWN
            </span>
            <div
              style={{
                width: '28px',
                height: '28px',
                borderRadius: '50%',
                background: 'var(--loss-bg)',
                color: 'var(--loss-text)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <ArrowDownRight size={15} />
            </div>
          </div>
          <div className="tabular-nums" style={{ fontSize: '24px', fontWeight: 700, color: 'var(--loss)' }}>
            {formatPercent(metrics.max_drawdown)}
          </div>
        </div>

        {/* Metric 5: Win Rate */}
        <div className="card" style={{ padding: '18px 20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-muted)' }}>
              WIN RATE
            </span>
            <div
              style={{
                width: '28px',
                height: '28px',
                borderRadius: '50%',
                background: 'var(--bg-subtle)',
                color: 'var(--text-main)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <Target size={15} />
            </div>
          </div>
          <div className="tabular-nums" style={{ fontSize: '24px', fontWeight: 700, color: 'var(--text-main)' }}>
            {formatPercent(metrics.win_rate)}
          </div>
        </div>
      </div>

      {/* Equity Curve Chart Card */}
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', flexWrap: 'wrap', gap: '10px' }}>
          <div>
            <h2 style={{ fontSize: '18px', fontWeight: 600, color: 'var(--text-main)' }}>
              Portfolio Equity Trajectory
            </h2>
            <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
              Continuous daily marked-to-market valuation (Initial: ₹1,00,000.00)
            </div>
          </div>

          {/* Chart Legend */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px', fontSize: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ width: '12px', height: '3px', background: 'var(--accent-dark)', borderRadius: '2px' }} />
              <span>Equity Curve</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ width: '8px', height: '8px', background: 'var(--gain)', borderRadius: '50%' }} />
              <span>Buy Entry (Filled)</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ width: '8px', height: '8px', border: '2px solid var(--loss)', borderRadius: '50%' }} />
              <span>Sell Exit (Hollow)</span>
            </div>
          </div>
        </div>

        <div style={{ width: '100%', height: '340px' }}>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={equity_curve} margin={{ top: 10, right: 20, left: 20, bottom: 20 }}>
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
                    const val = payload[0].value as number;
                    return (
                      <div
                        style={{
                          background: 'var(--accent-dark)',
                          color: '#FFFFFF',
                          padding: '10px 14px',
                          borderRadius: '12px',
                          boxShadow: 'var(--shadow-card)',
                          fontSize: '13px',
                        }}
                      >
                        <div style={{ opacity: 0.7, fontSize: '11px', marginBottom: '2px' }}>{label}</div>
                        <div style={{ fontWeight: 700, color: 'var(--accent-lime)' }}>
                          {formatCurrency(val)}
                        </div>
                      </div>
                    );
                  }
                  return null;
                }}
              />
              <Line
                type="monotone"
                dataKey="equity"
                stroke="var(--accent-dark)"
                strokeWidth={2.5}
                dot={renderCustomDot}
                activeDot={{ r: 6, fill: 'var(--accent-lime)', stroke: 'var(--accent-dark)', strokeWidth: 2 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Trade Log Table Card */}
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px' }}>
          <div>
            <h2 style={{ fontSize: '18px', fontWeight: 600 }}>Executed Trades</h2>
            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
              Completed long transactions filled at daily closing prices
            </span>
          </div>
          <span className="badge badge-neutral">
            {trades.length} {trades.length === 1 ? 'trade' : 'trades'}
          </span>
        </div>

        {/* FR-6: Zero trade runs show 'No trades were generated for this range.' */}
        {trades.length === 0 ? (
          <div className="empty-state" style={{ padding: '36px 16px' }}>
            No trades were generated for this range.
          </div>
        ) : (
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Trade ID</th>
                  <th>Entry Date</th>
                  <th>Exit Date</th>
                  <th className="text-right">Entry Price</th>
                  <th className="text-right">Exit Price</th>
                  <th className="text-right">Quantity</th>
                  <th className="text-right">P&amp;L</th>
                </tr>
              </thead>
              <tbody>
                {trades.map((t) => {
                  const isProfitable = t.pnl > 0;
                  return (
                    <tr key={t.trade_id}>
                      <td style={{ fontWeight: 600, fontFamily: 'var(--font-mono)' }}>
                        #{t.trade_id}
                      </td>
                      <td>{t.entry_date}</td>
                      <td>{t.exit_date}</td>
                      <td className="text-right tabular-nums">{formatCurrency(t.entry_price)}</td>
                      <td className="text-right tabular-nums">{formatCurrency(t.exit_price)}</td>
                      <td className="text-right tabular-nums">{t.quantity}</td>
                      <td
                        className="text-right tabular-nums"
                        style={{
                          fontWeight: 700,
                          color: isProfitable ? 'var(--gain)' : 'var(--loss)',
                        }}
                      >
                        {isProfitable ? '+' : ''}
                        {formatCurrency(t.pnl)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
