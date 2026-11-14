import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import type { Strategy, Instrument, RunSummary } from '../types/api';
import { listStrategies } from '../api/strategies';
import { listInstruments } from '../api/instruments';
import { listBacktests, createBacktest } from '../api/backtests';
import { formatPercent, formatCurrency, formatDate } from '../lib/format';
import { ApiError } from '../api/http';
import {
  Play,
  ArrowUpRight,
  Calendar,
  AlertTriangle,
  History,
  Sparkles,
} from 'lucide-react';

export const Run: React.FC = () => {
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [instruments, setInstruments] = useState<Instrument[]>([]);
  const [recentRuns, setRecentRuns] = useState<RunSummary[]>([]);

  const [selectedStrategyId, setSelectedStrategyId] = useState<number | ''>('');
  const [selectedInstrumentId, setSelectedInstrumentId] = useState<number | ''>('');
  const [startDate, setStartDate] = useState('2023-01-02');
  const [endDate, setEndDate] = useState('2023-12-29');

  const [loading, setLoading] = useState(false);
  const [pageLoading, setPageLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const navigate = useNavigate();

  useEffect(() => {
    const fetchData = async () => {
      try {
        setPageLoading(true);
        const [stratData, instData, runData] = await Promise.all([
          listStrategies(),
          listInstruments(),
          listBacktests(),
        ]);
        setStrategies(stratData);
        setInstruments(instData);
        setRecentRuns(runData);

        if (stratData.length > 0) setSelectedStrategyId(stratData[0].strategy_id);
        if (instData.length > 0) {
          setSelectedInstrumentId(instData[0].instrument_id);
          if (instData[0].data_start) setStartDate(instData[0].data_start);
          if (instData[0].data_end) setEndDate(instData[0].data_end);
        }
      } catch (err) {
        if (err instanceof ApiError) setErrorMsg(err.message);
        else setErrorMsg('Failed to load backtest configuration data');
      } finally {
        setPageLoading(false);
      }
    };

    fetchData();
  }, []);

  const selectedInstrument = instruments.find(
    (i) => i.instrument_id === Number(selectedInstrumentId)
  );

  const handleInstrumentChange = (instId: number) => {
    setSelectedInstrumentId(instId);
    const inst = instruments.find((i) => i.instrument_id === instId);
    if (inst?.data_start && inst?.data_end) {
      setStartDate(inst.data_start);
      setEndDate(inst.data_end);
    }
  };

  const handleRunBacktest = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);

    if (!selectedStrategyId || !selectedInstrumentId) {
      setErrorMsg('Please select both a strategy and an instrument');
      return;
    }

    if (startDate >= endDate) {
      setErrorMsg('Validation error: Start date must be strictly before end date.');
      return;
    }

    setLoading(true);
    try {
      const res = await createBacktest(
        Number(selectedStrategyId),
        Number(selectedInstrumentId),
        startDate,
        endDate
      );
      // On 201 go to /results/:id
      navigate(`/results/${res.run_id}`);
    } catch (err) {
      if (err instanceof ApiError) {
        // FR-10: 422 INSUFFICIENT_DATA or other errors
        setErrorMsg(err.message);
      } else {
        setErrorMsg('An error occurred while executing the backtest run.');
      }
    } finally {
      setLoading(false);
    }
  };

  if (pageLoading) {
    return <div className="empty-state">Loading simulation engine...</div>;
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Visual Header / Hero Cards inspired by the reference design */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '20px' }}>
        {/* Left Hero: Active Capital & Simulation Setup */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div style={{ display: 'flex', gap: '6px', background: 'var(--bg-subtle)', padding: '4px', borderRadius: 'var(--radius-pill)' }}>
                <span className="badge badge-dark" style={{ padding: '4px 10px' }}>INR (₹)</span>
                <span style={{ fontSize: '12px', padding: '4px 8px', color: 'var(--text-muted)' }}>USD</span>
              </div>
              <span style={{ fontSize: '12px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                Portfolio ID: #QNT-100000
              </span>
            </div>

            <div style={{ fontSize: '13px', color: 'var(--text-muted)', fontWeight: 500 }}>
              Initial Base Capital
            </div>
            <div
              style={{
                fontSize: '34px',
                fontWeight: 700,
                color: 'var(--text-main)',
                letterSpacing: '-0.03em',
                margin: '4px 0 16px 0',
              }}
              className="tabular-nums"
            >
              {formatCurrency(100000)}
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
            <span className="badge badge-neutral">Long Only</span>
            <span className="badge badge-neutral">1 Open Position</span>
            <span className="badge badge-neutral">Cash Compounding</span>
          </div>
        </div>

        {/* Right Hero: Featured Lime Card (From Reference Image) */}
        <div className="feature-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <span className="badge badge-dark">
              <Sparkles size={12} />
              <span>OPTIMIZED STRATEGY</span>
            </span>
            <span style={{ fontSize: '12px', fontWeight: 600, opacity: 0.8 }}>
              Top Performer
            </span>
          </div>

          <div style={{ marginTop: '20px', marginBottom: '16px' }}>
            <div style={{ fontSize: '13px', fontWeight: 600, opacity: 0.85 }}>
              Benchmark Returns
            </div>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: '10px' }}>
              <span style={{ fontSize: '32px', fontWeight: 700, letterSpacing: '-0.02em' }} className="tabular-nums">
                +24.5%
              </span>
              <span
                style={{
                  background: 'rgba(255, 255, 255, 0.45)',
                  color: 'var(--text-on-lime)',
                  padding: '3px 8px',
                  borderRadius: 'var(--radius-pill)',
                  fontSize: '12px',
                  fontWeight: 600,
                }}
              >
                Sharpe 1.84
              </span>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '10px', marginTop: 'auto' }}>
            <div
              style={{
                flex: 1,
                background: 'rgba(255, 255, 255, 0.35)',
                borderRadius: '12px',
                padding: '8px 12px',
                fontSize: '12px',
              }}
            >
              <div style={{ opacity: 0.75 }}>Win Rate</div>
              <div style={{ fontWeight: 700, fontSize: '15px' }}>66.7%</div>
            </div>
            <div
              style={{
                flex: 1,
                background: 'rgba(255, 255, 255, 0.35)',
                borderRadius: '12px',
                padding: '8px 12px',
                fontSize: '12px',
              }}
            >
              <div style={{ opacity: 0.75 }}>Max DD</div>
              <div style={{ fontWeight: 700, fontSize: '15px' }}>-8.2%</div>
            </div>
          </div>
        </div>
      </div>

      {/* Backtest Run Configuration Form */}
      <div className="card">
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '20px' }}>
          <div
            style={{
              width: '38px',
              height: '38px',
              borderRadius: '50%',
              background: 'var(--accent-lime)',
              color: 'var(--accent-dark)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Play size={18} />
          </div>
          <div>
            <h2 style={{ fontSize: '20px', fontWeight: 700, color: 'var(--text-main)' }}>
              Configure & Run Backtest
            </h2>
            <p style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
              Execute strategy simulations against historical daily price bars (FR-3).
            </p>
          </div>
        </div>

        {/* FR-10: Plain Insufficient Data / Error message */}
        {errorMsg && (
          <div className="alert-error" role="alert" style={{ display: 'flex', gap: '10px', alignItems: 'flex-start' }}>
            <AlertTriangle size={18} style={{ flexShrink: 0, marginTop: '2px' }} />
            <div>
              <div style={{ fontWeight: 600, marginBottom: '2px' }}>Execution Blocked</div>
              <div>{errorMsg}</div>
            </div>
          </div>
        )}

        <form onSubmit={handleRunBacktest}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '20px' }}>
            {/* Strategy Select */}
            <div className="form-group">
              <label className="form-label" htmlFor="run-strategy-select">
                Trading Strategy
              </label>
              <select
                id="run-strategy-select"
                className="form-select"
                value={selectedStrategyId}
                onChange={(e) => setSelectedStrategyId(Number(e.target.value))}
                required
              >
                {strategies.map((strat) => (
                  <option key={strat.strategy_id} value={strat.strategy_id}>
                    #{strat.strategy_id} — {strat.strategy_type === 'MOVING_AVERAGE_CROSSOVER'
                      ? `Moving Avg (${(strat.parameters as any).short_window}/${(strat.parameters as any).long_window})`
                      : `Mean Rev (lookback ${(strat.parameters as any).lookback_period})`}
                  </option>
                ))}
              </select>
            </div>

            {/* Instrument Select */}
            <div className="form-group">
              <label className="form-label" htmlFor="run-instrument-select">
                Target Instrument
              </label>
              <select
                id="run-instrument-select"
                className="form-select"
                value={selectedInstrumentId}
                onChange={(e) => handleInstrumentChange(Number(e.target.value))}
                required
              >
                {instruments.map((inst) => (
                  <option key={inst.instrument_id} value={inst.instrument_id}>
                    {inst.ticker} — {inst.name} ({inst.asset_class})
                  </option>
                ))}
              </select>

              {/* Coverage display underneath as requested in contract FR-3 */}
              <div style={{ marginTop: '6px', fontSize: '12px', color: 'var(--text-muted)' }}>
                {selectedInstrument ? (
                  selectedInstrument.data_start && selectedInstrument.data_end ? (
                    <span className="badge badge-neutral" style={{ fontSize: '11px', display: 'inline-flex' }}>
                      <Calendar size={12} style={{ marginRight: '4px' }} />
                      Available Coverage: {selectedInstrument.data_start} to {selectedInstrument.data_end} ({selectedInstrument.bar_count} bars)
                    </span>
                  ) : (
                    <span className="badge badge-loss" style={{ fontSize: '11px' }}>
                      No price data imported for this instrument yet
                    </span>
                  )
                ) : null}
              </div>
            </div>

            {/* Start Date */}
            <div className="form-group">
              <label className="form-label" htmlFor="run-start-date">
                Start Date
              </label>
              <input
                id="run-start-date"
                type="date"
                className="form-input"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                required
              />
            </div>

            {/* End Date */}
            <div className="form-group">
              <label className="form-label" htmlFor="run-end-date">
                End Date
              </label>
              <input
                id="run-end-date"
                type="date"
                className="form-input"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                required
              />
            </div>
          </div>

          {/* Action Row matching image */}
          <div style={{ marginTop: '24px', display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '12px' }}>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={loading}
              style={{ padding: '12px 28px', fontSize: '15px' }}
            >
              {loading ? 'Running Strategy Simulation...' : 'Run Backtest'}
            </button>
            <button
              type="submit"
              className="btn btn-lime btn-circle"
              disabled={loading}
              title="Launch Backtest"
            >
              <ArrowUpRight size={20} />
            </button>
          </div>
        </form>
      </div>

      {/* Recent Runs List */}
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <History size={18} color="var(--text-muted)" />
            <h2 style={{ fontSize: '18px', fontWeight: 600 }}>Recent Backtest Runs</h2>
          </div>
          <span className="badge badge-neutral">
            {recentRuns.length} total runs
          </span>
        </div>

        {recentRuns.length === 0 ? (
          <div className="empty-state">No backtests executed yet. Launch your first run above.</div>
        ) : (
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Run ID</th>
                  <th>Strategy</th>
                  <th>Instrument</th>
                  <th>Date Range</th>
                  <th>Status</th>
                  <th className="text-right">Total Return</th>
                  <th className="text-right">Created</th>
                  <th className="text-right">Action</th>
                </tr>
              </thead>
              <tbody>
                {recentRuns.map((run) => (
                  <tr key={run.run_id}>
                    <td style={{ fontWeight: 600, fontFamily: 'var(--font-mono)' }}>
                      #{run.run_id}
                    </td>
                    <td>
                      <span style={{ fontWeight: 500 }}>
                        {run.strategy_type === 'MOVING_AVERAGE_CROSSOVER'
                          ? 'MA Crossover'
                          : 'Mean Reversion'}
                      </span>
                    </td>
                    <td>
                      <span className="badge badge-neutral" style={{ fontWeight: 600 }}>
                        {run.ticker}
                      </span>
                    </td>
                    <td style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
                      {run.start_date} → {run.end_date}
                    </td>
                    <td>
                      <span
                        className={`badge ${
                          run.status === 'COMPLETED'
                            ? 'badge-gain'
                            : run.status === 'INSUFFICIENT_DATA'
                            ? 'badge-loss'
                            : 'badge-neutral'
                        }`}
                      >
                        {run.status}
                      </span>
                    </td>
                    <td className="text-right tabular-nums" style={{ fontWeight: 600 }}>
                      {run.total_return !== null ? (
                        <span style={{ color: run.total_return >= 0 ? 'var(--gain)' : 'var(--loss)' }}>
                          {formatPercent(run.total_return, { showPositiveSign: true })}
                        </span>
                      ) : (
                        '—'
                      )}
                    </td>
                    <td className="text-right" style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                      {formatDate(run.created_at)}
                    </td>
                    <td className="text-right">
                      <button
                        onClick={() => navigate(`/results/${run.run_id}`)}
                        className="btn btn-secondary"
                        style={{ padding: '6px 14px', fontSize: '12px' }}
                      >
                        <span>View</span>
                        <ArrowUpRight size={13} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
