import type {
  User,
  Strategy,
  Instrument,
  RunSummary,
  RunDetail,
  CompareRunsResponse,
  ImportPricesResponse,
  AuthResponse,
  RegisterResponse,
} from '../types/api';
import { ApiError } from './http';

// Initial Mock Data
let mockUsers: User[] = [
  {
    user_id: 1,
    name: 'Shourya Vardhan',
    email: 'trader@jss.ac.in',
    role: 'TRADER',
  },
  {
    user_id: 2,
    name: 'Admin System',
    email: 'admin@jss.ac.in',
    role: 'ADMIN',
  },
];

let mockStrategies: Strategy[] = [
  {
    strategy_id: 1,
    user_id: 1,
    strategy_type: 'MOVING_AVERAGE_CROSSOVER',
    parameters: { short_window: 20, long_window: 50 },
    created_at: '2024-03-01T10:00:00Z',
  },
  {
    strategy_id: 2,
    user_id: 1,
    strategy_type: 'MEAN_REVERSION',
    parameters: { lookback_period: 20, threshold: 2.0 },
    created_at: '2024-03-10T14:30:00Z',
  },
  {
    strategy_id: 3,
    user_id: 1,
    strategy_type: 'MOVING_AVERAGE_CROSSOVER',
    parameters: { short_window: 10, long_window: 30 },
    created_at: '2024-03-15T09:15:00Z',
  },
];

let mockInstruments: Instrument[] = [
  {
    instrument_id: 1,
    ticker: 'RELIANCE',
    name: 'Reliance Industries Ltd',
    asset_class: 'EQUITY',
    data_start: '2023-01-02',
    data_end: '2023-12-29',
    bar_count: 248,
  },
  {
    instrument_id: 2,
    ticker: 'TCS',
    name: 'Tata Consultancy Services',
    asset_class: 'EQUITY',
    data_start: '2023-01-02',
    data_end: '2023-12-29',
    bar_count: 248,
  },
  {
    instrument_id: 3,
    ticker: 'INFY',
    name: 'Infosys Limited',
    asset_class: 'EQUITY',
    data_start: '2023-06-01',
    data_end: '2023-12-29',
    bar_count: 145,
  },
  {
    instrument_id: 4,
    ticker: 'HDFCBANK',
    name: 'HDFC Bank Ltd',
    asset_class: 'EQUITY',
    data_start: null,
    data_end: null,
    bar_count: 0,
  },
];

function generateEquityCurve(
  startDateStr: string,
  days: number,
  initialEquity: number,
  drift: number,
  volatility: number
) {
  const curve = [];
  let currentEquity = initialEquity;
  const start = new Date(startDateStr);

  for (let i = 0; i < days; i++) {
    const d = new Date(start);
    d.setDate(d.getDate() + i);
    // skip weekends
    if (d.getDay() === 0 || d.getDay() === 6) continue;

    const change = (Math.sin(i / 5) * volatility + drift) * currentEquity;
    currentEquity = Math.max(1000, currentEquity + change);
    curve.push({
      date: d.toISOString().split('T')[0],
      equity: Math.round(currentEquity * 100) / 100,
    });
  }
  return curve;
}

const run1Curve = generateEquityCurve('2023-01-02', 240, 100000.0, 0.0011, 0.008);
const run3Curve = generateEquityCurve('2023-01-02', 240, 100000.0, 0.0008, 0.012);

let mockRunDetails: Record<number, RunDetail> = {
  1: {
    run: {
      run_id: 1,
      user_id: 1,
      strategy_id: 1,
      instrument_id: 1,
      start_date: '2023-01-02',
      end_date: '2023-12-29',
      status: 'COMPLETED',
      created_at: '2024-03-20T10:15:00Z',
    },
    strategy: mockStrategies[0],
    instrument: mockInstruments[0],
    metrics: {
      sharpe_ratio: 1.84,
      max_drawdown: -0.082,
      win_rate: 0.667,
      cagr: 0.224,
      total_return: 0.245,
    },
    trades: [
      { trade_id: 101, entry_date: '2023-02-14', exit_date: '2023-03-22', entry_price: 2320.5, exit_price: 2480.0, quantity: 43, pnl: 6858.5 },
      { trade_id: 102, entry_date: '2023-04-10', exit_date: '2023-05-18', entry_price: 2410.0, exit_price: 2390.0, quantity: 44, pnl: -880.0 },
      { trade_id: 103, entry_date: '2023-06-05', exit_date: '2023-07-28', entry_price: 2470.0, exit_price: 2620.0, quantity: 42, pnl: 6300.0 },
      { trade_id: 104, entry_date: '2023-08-15', exit_date: '2023-09-29', entry_price: 2550.0, exit_price: 2680.0, quantity: 43, pnl: 5590.0 },
      { trade_id: 105, entry_date: '2023-10-18', exit_date: '2023-11-20', entry_price: 2590.0, exit_price: 2540.0, quantity: 45, pnl: -2250.0 },
      { trade_id: 106, entry_date: '2023-11-28', exit_date: '2023-12-29', entry_price: 2560.0, exit_price: 2710.0, quantity: 44, pnl: 6600.0 },
    ],
    equity_curve: run1Curve,
  },
  2: {
    run: {
      run_id: 2,
      user_id: 1,
      strategy_id: 1,
      instrument_id: 2,
      start_date: '2023-06-01',
      end_date: '2023-08-01',
      status: 'COMPLETED',
      created_at: '2024-03-21T11:00:00Z',
    },
    strategy: mockStrategies[0],
    instrument: mockInstruments[1],
    metrics: {
      sharpe_ratio: 0.0,
      max_drawdown: 0.0,
      win_rate: 0.0,
      cagr: 0.0,
      total_return: 0.0,
    },
    trades: [], // Zero trades test case
    equity_curve: [
      { date: '2023-06-01', equity: 100000.0 },
      { date: '2023-06-15', equity: 100000.0 },
      { date: '2023-07-01', equity: 100000.0 },
      { date: '2023-07-15', equity: 100000.0 },
      { date: '2023-08-01', equity: 100000.0 },
    ],
  },
  3: {
    run: {
      run_id: 3,
      user_id: 1,
      strategy_id: 2,
      instrument_id: 1,
      start_date: '2023-01-02',
      end_date: '2023-12-29',
      status: 'COMPLETED',
      created_at: '2024-03-22T14:45:00Z',
    },
    strategy: mockStrategies[1],
    instrument: mockInstruments[0],
    metrics: {
      sharpe_ratio: 1.42,
      max_drawdown: -0.125,
      win_rate: 0.55,
      cagr: 0.168,
      total_return: 0.181,
    },
    trades: [
      { trade_id: 201, entry_date: '2023-02-01', exit_date: '2023-02-28', entry_price: 2310.0, exit_price: 2420.0, quantity: 43, pnl: 4730.0 },
      { trade_id: 202, entry_date: '2023-04-12', exit_date: '2023-05-05', entry_price: 2450.0, exit_price: 2410.0, quantity: 42, pnl: -1680.0 },
      { trade_id: 203, entry_date: '2023-06-20', exit_date: '2023-07-18', entry_price: 2510.0, exit_price: 2610.0, quantity: 41, pnl: 4100.0 },
      { trade_id: 204, entry_date: '2023-09-01', exit_date: '2023-09-25', entry_price: 2600.0, exit_price: 2670.0, quantity: 40, pnl: 2800.0 },
    ],
    equity_curve: run3Curve,
  },
};

let mockSummaries: RunSummary[] = [
  {
    run_id: 1,
    strategy_id: 1,
    strategy_type: 'MOVING_AVERAGE_CROSSOVER',
    instrument_id: 1,
    ticker: 'RELIANCE',
    start_date: '2023-01-02',
    end_date: '2023-12-29',
    status: 'COMPLETED',
    total_return: 0.245,
    created_at: '2024-03-20T10:15:00Z',
  },
  {
    run_id: 2,
    strategy_id: 1,
    strategy_type: 'MOVING_AVERAGE_CROSSOVER',
    instrument_id: 2,
    ticker: 'TCS',
    start_date: '2023-06-01',
    end_date: '2023-08-01',
    status: 'COMPLETED',
    total_return: 0.0,
    created_at: '2024-03-21T11:00:00Z',
  },
  {
    run_id: 3,
    strategy_id: 2,
    strategy_type: 'MEAN_REVERSION',
    instrument_id: 1,
    ticker: 'RELIANCE',
    start_date: '2023-01-02',
    end_date: '2023-12-29',
    status: 'COMPLETED',
    total_return: 0.181,
    created_at: '2024-03-22T14:45:00Z',
  },
];

// Helper to simulate short async delay
const delay = (ms = 120) => new Promise((resolve) => setTimeout(resolve, ms));

export const mockApi = {
  // Auth
  async login(email: string, password: string): Promise<AuthResponse> {
    await delay();
    if (password.length < 8) {
      throw new ApiError('VALIDATION_ERROR', 'Password must be at least 8 characters', 400);
    }
    const user = mockUsers.find((u) => u.email.toLowerCase() === email.toLowerCase());
    if (!user) {
      throw new ApiError('UNAUTHENTICATED', 'Invalid email or password', 401);
    }
    return {
      token: `mock_jwt_token_${user.user_id}_${Date.now()}`,
      user,
    };
  },

  async register(name: string, email: string, password: string): Promise<RegisterResponse> {
    await delay();
    if (!name || !email || !password) {
      throw new ApiError('VALIDATION_ERROR', 'All fields are required', 400);
    }
    if (password.length < 8) {
      throw new ApiError('VALIDATION_ERROR', 'Password must be at least 8 characters', 400);
    }
    if (mockUsers.some((u) => u.email.toLowerCase() === email.toLowerCase())) {
      throw new ApiError('CONFLICT', 'Email is already registered', 409);
    }
    const newUser: User = {
      user_id: mockUsers.length + 1,
      name,
      email,
      role: 'TRADER',
    };
    mockUsers.push(newUser);
    return {
      user_id: newUser.user_id,
      name: newUser.name,
      email: newUser.email,
      role: 'TRADER',
    };
  },

  // Strategies
  async getStrategies(): Promise<Strategy[]> {
    await delay();
    return [...mockStrategies];
  },

  async createStrategy(strategy_type: string, parameters: Record<string, any>): Promise<Strategy> {
    await delay();
    if (strategy_type === 'MOVING_AVERAGE_CROSSOVER') {
      const { short_window, long_window } = parameters;
      if (!short_window || !long_window || Number(short_window) >= Number(long_window)) {
        throw new ApiError('VALIDATION_ERROR', 'short_window must be less than long_window', 400);
      }
    } else if (strategy_type === 'MEAN_REVERSION') {
      const { lookback_period, threshold } = parameters;
      if (!lookback_period || lookback_period < 2 || !threshold || threshold <= 0) {
        throw new ApiError('VALIDATION_ERROR', 'lookback_period must be >= 2 and threshold > 0', 400);
      }
    } else {
      throw new ApiError('VALIDATION_ERROR', 'Unknown strategy type', 400);
    }

    const newStrat: Strategy = {
      strategy_id: mockStrategies.length + 1,
      user_id: 1,
      strategy_type: strategy_type as any,
      parameters,
      created_at: new Date().toISOString(),
    };
    mockStrategies.unshift(newStrat);
    return newStrat;
  },

  // Instruments
  async getInstruments(): Promise<Instrument[]> {
    await delay();
    return [...mockInstruments];
  },

  async createInstrument(ticker: string, name: string, asset_class: string): Promise<Instrument> {
    await delay();
    if (mockInstruments.some((i) => i.ticker.toUpperCase() === ticker.toUpperCase())) {
      throw new ApiError('CONFLICT', `Instrument with ticker ${ticker} already exists`, 409);
    }
    const newInst: Instrument = {
      instrument_id: mockInstruments.length + 1,
      ticker: ticker.toUpperCase(),
      name,
      asset_class,
      data_start: null,
      data_end: null,
      bar_count: 0,
    };
    mockInstruments.push(newInst);
    return newInst;
  },

  async updateInstrument(id: number, ticker: string, name: string, asset_class: string): Promise<Instrument> {
    await delay();
    const inst = mockInstruments.find((i) => i.instrument_id === id);
    if (!inst) throw new ApiError('NOT_FOUND', 'Instrument not found', 404);
    if (mockInstruments.some((i) => i.instrument_id !== id && i.ticker.toUpperCase() === ticker.toUpperCase())) {
      throw new ApiError('CONFLICT', `Ticker ${ticker} already taken`, 409);
    }
    inst.ticker = ticker.toUpperCase();
    inst.name = name;
    inst.asset_class = asset_class;
    return { ...inst };
  },

  async deleteInstrument(id: number): Promise<void> {
    await delay();
    const inst = mockInstruments.find((i) => i.instrument_id === id);
    if (!inst) throw new ApiError('NOT_FOUND', 'Instrument not found', 404);
    // FR-8 / CONFLICT check if runs reference this instrument
    if (mockSummaries.some((s) => s.instrument_id === id)) {
      throw new ApiError('CONFLICT', 'INSTRUMENT_IN_USE: Instrument is referenced by existing backtest runs', 409);
    }
    mockInstruments = mockInstruments.filter((i) => i.instrument_id !== id);
  },

  async importPrices(id: number, _file: File): Promise<ImportPricesResponse> {
    await delay(300);
    const inst = mockInstruments.find((i) => i.instrument_id === id);
    if (!inst) throw new ApiError('NOT_FOUND', 'Instrument not found', 404);

    inst.data_start = '2023-01-02';
    inst.data_end = '2023-12-29';
    inst.bar_count = 248;

    return {
      imported: 248,
      skipped: 2,
      errors: [
        { row: 14, reason: 'Duplicate date 2023-01-20' },
        { row: 88, reason: 'Negative volume on 2023-05-12' },
      ],
    };
  },

  // Backtests
  async getBacktests(): Promise<RunSummary[]> {
    await delay();
    return [...mockSummaries];
  },

  async getBacktest(id: number): Promise<RunDetail> {
    await delay();
    const detail = mockRunDetails[id];
    if (!detail) {
      throw new ApiError('NOT_FOUND', `Backtest run ${id} not found`, 404);
    }
    return detail;
  },

  async createBacktest(
    strategy_id: number,
    instrument_id: number,
    start_date: string,
    end_date: string
  ): Promise<{ run_id: number; status: 'COMPLETED' }> {
    await delay(250);
    if (start_date >= end_date) {
      throw new ApiError('VALIDATION_ERROR', 'start_date must be strictly before end_date', 400);
    }

    const inst = mockInstruments.find((i) => i.instrument_id === instrument_id);
    if (!inst) throw new ApiError('NOT_FOUND', 'Instrument not found', 404);

    const strat = mockStrategies.find((s) => s.strategy_id === strategy_id);
    if (!strat) throw new ApiError('NOT_FOUND', 'Strategy not found', 404);

    // FR-10 Insufficient data check
    if (!inst.data_start || !inst.data_end || inst.bar_count === 0) {
      throw new ApiError(
        'INSUFFICIENT_DATA',
        `Instrument ${inst.ticker} has no price bars available. Available coverage: None.`,
        422
      );
    }

    if (start_date < inst.data_start || end_date > inst.data_end) {
      throw new ApiError(
        'INSUFFICIENT_DATA',
        `Insufficient data for ${inst.ticker}: Requested ${start_date} to ${end_date}, but available range is ${inst.data_start} to ${inst.data_end}.`,
        422
      );
    }

    const newId = Math.max(...Object.keys(mockRunDetails).map(Number), 0) + 1;
    const curve = generateEquityCurve(start_date, 120, 100000.0, 0.0012, 0.007);
    const finalEquity = curve[curve.length - 1]?.equity ?? 100000.0;
    const totalReturn = Math.round(((finalEquity - 100000.0) / 100000.0) * 1000) / 1000;

    const newDetail: RunDetail = {
      run: {
        run_id: newId,
        user_id: 1,
        strategy_id,
        instrument_id,
        start_date,
        end_date,
        status: 'COMPLETED',
        created_at: new Date().toISOString(),
      },
      strategy: strat,
      instrument: inst,
      metrics: {
        sharpe_ratio: 1.65,
        max_drawdown: -0.094,
        win_rate: 0.62,
        cagr: 0.195,
        total_return: totalReturn,
      },
      trades: [
        { trade_id: 301, entry_date: start_date, exit_date: end_date, entry_price: 2450.0, exit_price: 2680.0, quantity: 40, pnl: 9200.0 },
      ],
      equity_curve: curve,
    };

    mockRunDetails[newId] = newDetail;

    mockSummaries.unshift({
      run_id: newId,
      strategy_id,
      strategy_type: strat.strategy_type,
      instrument_id,
      ticker: inst.ticker,
      start_date,
      end_date,
      status: 'COMPLETED',
      total_return: totalReturn,
      created_at: newDetail.run.created_at,
    });

    return { run_id: newId, status: 'COMPLETED' };
  },

  async compareBacktests(runA: number, runB: number): Promise<CompareRunsResponse> {
    await delay();
    const detailA = mockRunDetails[runA];
    const detailB = mockRunDetails[runB];
    if (!detailA || !detailB) {
      throw new ApiError('NOT_FOUND', 'One or both backtest runs could not be found', 404);
    }
    return {
      run_a: detailA,
      run_b: detailB,
    };
  },
};
