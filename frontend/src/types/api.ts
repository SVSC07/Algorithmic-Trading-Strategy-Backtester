// API Types matching the project contract exactly.
// All keys are snake_case.

export type UserRole = 'TRADER' | 'ADMIN';

export interface User {
  user_id: number;
  name: string;
  email: string;
  role: UserRole;
}

export type StrategyType = 'MOVING_AVERAGE_CROSSOVER' | 'MEAN_REVERSION';

export interface MovingAverageParameters {
  short_window: number;
  long_window: number;
}

export interface MeanReversionParameters {
  lookback_period: number;
  threshold: number;
}

export type StrategyParameters = MovingAverageParameters | MeanReversionParameters | Record<string, any>;

export interface Strategy {
  strategy_id: number;
  user_id: number;
  strategy_type: StrategyType;
  parameters: StrategyParameters;
  created_at: string;
}

export interface Instrument {
  instrument_id: number;
  ticker: string;
  name: string;
  asset_class: string;
  data_start: string | null;
  data_end: string | null;
  bar_count: number;
}

export type BacktestStatus = 'PENDING' | 'COMPLETED' | 'FAILED' | 'INSUFFICIENT_DATA';

export interface RunSummary {
  run_id: number;
  strategy_id: number;
  strategy_type: string;
  instrument_id: number;
  ticker: string;
  start_date: string;
  end_date: string;
  status: BacktestStatus;
  total_return: number | null;
  created_at: string;
}

export interface Metrics {
  sharpe_ratio: number;
  max_drawdown: number;
  win_rate: number;
  cagr: number;
  total_return: number;
}

export interface Trade {
  trade_id: number;
  entry_date: string;
  exit_date: string;
  entry_price: number;
  exit_price: number;
  quantity: number;
  pnl: number;
}

export interface EquityPoint {
  date: string;
  equity: number;
}

export interface RunDetail {
  run: {
    run_id: number;
    user_id: number;
    strategy_id: number;
    instrument_id: number;
    start_date: string;
    end_date: string;
    status: BacktestStatus;
    created_at: string;
  };
  strategy: Strategy;
  instrument: Instrument;
  metrics: Metrics;
  trades: Trade[];
  equity_curve: EquityPoint[];
}

export interface CompareRunsResponse {
  run_a: RunDetail;
  run_b: RunDetail;
}

export interface ImportPriceError {
  row: number;
  reason: string;
}

export interface ImportPricesResponse {
  imported: number;
  skipped: number;
  errors: ImportPriceError[];
}

export interface AuthResponse {
  token: string;
  user: User;
}

export interface RegisterResponse {
  user_id: number;
  name: string;
  email: string;
  role: 'TRADER';
}

export interface ApiErrorEnvelope {
  error: {
    code: 'VALIDATION_ERROR' | 'UNAUTHENTICATED' | 'FORBIDDEN' | 'NOT_FOUND' | 'CONFLICT' | 'INSUFFICIENT_DATA' | string;
    message: string;
  };
}
