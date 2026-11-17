import React, { useState, useEffect } from 'react';
import type { Strategy, StrategyType } from '../types/api';
import { listStrategies, createStrategy } from '../api/strategies';
import { validateStrategyForm } from '../lib/strategy-validation';
import { ApiError } from '../api/http';
import { CustomSelect } from '../components/CustomSelect';
import { Sliders, Plus, CheckCircle2, AlertCircle } from 'lucide-react';

export const Strategies: React.FC = () => {
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [strategyType, setStrategyType] = useState<StrategyType>('MOVING_AVERAGE_CROSSOVER');

  // Moving Average inputs
  const [shortWindow, setShortWindow] = useState('20');
  const [longWindow, setLongWindow] = useState('50');

  // Mean Reversion inputs
  const [lookbackPeriod, setLookbackPeriod] = useState('20');
  const [threshold, setThreshold] = useState('2.0');

  const [loading, setLoading] = useState(false);
  const [fetchLoading, setFetchLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [inlineError, setInlineError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const loadStrategies = async () => {
    try {
      setFetchLoading(true);
      const data = await listStrategies();
      setStrategies(data);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError('Failed to fetch strategies');
      }
    } finally {
      setFetchLoading(false);
    }
  };

  useEffect(() => {
    loadStrategies();
  }, []);

  // Validate on input changes
  useEffect(() => {
    const valResult = validateStrategyForm(strategyType, {
      short_window: shortWindow,
      long_window: longWindow,
      lookback_period: lookbackPeriod,
      threshold,
    });
    if (!valResult.isValid) {
      setInlineError(valResult.error || 'Invalid configuration');
    } else {
      setInlineError(null);
    }
  }, [strategyType, shortWindow, longWindow, lookbackPeriod, threshold]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccessMsg(null);

    const validation = validateStrategyForm(strategyType, {
      short_window: shortWindow,
      long_window: longWindow,
      lookback_period: lookbackPeriod,
      threshold,
    });

    if (!validation.isValid) {
      setInlineError(validation.error || 'Please correct errors before saving');
      return;
    }

    setLoading(true);
    try {
      let params: Record<string, any> = {};
      if (strategyType === 'MOVING_AVERAGE_CROSSOVER') {
        params = {
          short_window: Number(shortWindow),
          long_window: Number(longWindow),
        };
      } else {
        params = {
          lookback_period: Number(lookbackPeriod),
          threshold: Number(threshold),
        };
      }

      const created = await createStrategy(strategyType, params);
      setStrategies((prev) => [created, ...prev]);
      setSuccessMsg('Strategy configuration saved successfully!');
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError('Failed to create strategy');
      }
    } finally {
      setLoading(false);
    }
  };

  const formatStrategySummary = (strat: Strategy): string => {
    if (strat.strategy_type === 'MOVING_AVERAGE_CROSSOVER') {
      const p = strat.parameters as { short_window: number; long_window: number };
      return `Moving Average Crossover, ${p.short_window} / ${p.long_window}`;
    }
    if (strat.strategy_type === 'MEAN_REVERSION') {
      const p = strat.parameters as { lookback_period: number; threshold: number };
      return `Mean Reversion, lookback ${p.lookback_period} / threshold ${p.threshold}`;
    }
    return `${strat.strategy_type}, ${JSON.stringify(strat.parameters)}`;
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Title & Introduction */}
      <div>
        <h1 style={{ fontSize: '26px', fontWeight: 700, color: 'var(--text-main)', letterSpacing: '-0.02em' }}>
          Strategy Configuration
        </h1>
        <p style={{ fontSize: '14px', color: 'var(--text-muted)', marginTop: '4px' }}>
          Configure parametric trading algorithms conforming to contract specifications (FR-2).
        </p>
      </div>

      {error && (
        <div className="alert-error" role="alert">
          {error}
        </div>
      )}

      {successMsg && (
        <div className="alert-success" role="status">
          {successMsg}
        </div>
      )}

      {/* Creation Form Card */}
      <div className="card">
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '20px' }}>
          <div
            style={{
              width: '36px',
              height: '36px',
              borderRadius: '50%',
              background: 'var(--bg-subtle)',
              border: '1px solid var(--border)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--accent-dark)',
            }}
          >
            <Sliders size={18} />
          </div>
          <div>
            <h2 style={{ fontSize: '18px', fontWeight: 600 }}>Create New Strategy</h2>
            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
              Select rule family and configure mathematical thresholds
            </span>
          </div>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label" htmlFor="strategy-type-select">
              Strategy Type
            </label>
            <CustomSelect
              id="strategy-type-select"
              value={strategyType}
              onChange={(val) => setStrategyType(val as StrategyType)}
              options={[
                {
                  value: 'MOVING_AVERAGE_CROSSOVER',
                  label: 'Moving Average Crossover (SMA)',
                  badge: 'Trend',
                },
                {
                  value: 'MEAN_REVERSION',
                  label: 'Mean Reversion (Rolling Mean & Threshold)',
                  badge: 'Mean Rev',
                },
              ]}
            />
          </div>

          {/* Conditional parameter inputs */}
          {strategyType === 'MOVING_AVERAGE_CROSSOVER' ? (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
              <div className="form-group">
                <label className="form-label" htmlFor="short-window-input">
                  Short Window (bars)
                </label>
                <input
                  id="short-window-input"
                  type="number"
                  min="1"
                  step="1"
                  className="form-input"
                  value={shortWindow}
                  onChange={(e) => setShortWindow(e.target.value)}
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label" htmlFor="long-window-input">
                  Long Window (bars)
                </label>
                <input
                  id="long-window-input"
                  type="number"
                  min="2"
                  step="1"
                  className="form-input"
                  value={longWindow}
                  onChange={(e) => setLongWindow(e.target.value)}
                  required
                />
              </div>
            </div>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
              <div className="form-group">
                <label className="form-label" htmlFor="lookback-period-input">
                  Lookback Period (bars, min 2)
                </label>
                <input
                  id="lookback-period-input"
                  type="number"
                  min="2"
                  step="1"
                  className="form-input"
                  value={lookbackPeriod}
                  onChange={(e) => setLookbackPeriod(e.target.value)}
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label" htmlFor="threshold-input">
                  Threshold (standard deviations, &gt; 0)
                </label>
                <input
                  id="threshold-input"
                  type="number"
                  min="0.1"
                  step="0.1"
                  className="form-input"
                  value={threshold}
                  onChange={(e) => setThreshold(e.target.value)}
                  required
                />
              </div>
            </div>
          )}

          {/* Inline Validation Alert */}
          {inlineError && (
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                fontSize: '13px',
                color: 'var(--loss)',
                marginTop: '4px',
                marginBottom: '16px',
              }}
            >
              <AlertCircle size={15} />
              <span>{inlineError}</span>
            </div>
          )}

          <div style={{ marginTop: '16px', display: 'flex', justifyContent: 'flex-end' }}>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={loading || !!inlineError}
              style={{ padding: '10px 24px' }}
            >
              <Plus size={16} />
              <span>{loading ? 'Saving...' : 'Save Strategy'}</span>
            </button>
          </div>
        </form>
      </div>

      {/* Saved Strategies List */}
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <div>
            <h2 style={{ fontSize: '18px', fontWeight: 600 }}>Saved Strategies</h2>
            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
              Active algorithmic rules available for backtesting runs
            </span>
          </div>
          <span className="badge badge-neutral">
            {strategies.length} {strategies.length === 1 ? 'strategy' : 'strategies'}
          </span>
        </div>

        {fetchLoading ? (
          <div className="empty-state">Loading saved strategies...</div>
        ) : strategies.length === 0 ? (
          <div className="empty-state">No strategies saved yet. Create your first strategy above.</div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {strategies.map((strat) => (
              <div
                key={strat.strategy_id}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '14px 18px',
                  borderRadius: 'var(--radius-md)',
                  background: 'var(--bg-subtle)',
                  border: '1px solid var(--border)',
                  transition: 'background 0.15s ease',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <CheckCircle2 size={18} color="var(--gain)" />
                  <div>
                    <span style={{ fontWeight: 600, fontSize: '15px', color: 'var(--text-main)' }}>
                      {formatStrategySummary(strat)}
                    </span>
                    <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '2px' }}>
                      Created on {strat.created_at ? strat.created_at.split('T')[0] : 'N/A'}
                    </div>
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span className="badge badge-neutral" style={{ fontSize: '11px' }}>
                    ID #{strat.strategy_id}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
