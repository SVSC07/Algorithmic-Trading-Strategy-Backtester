import type { StrategyType } from '../types/api';

export interface StrategyValidationResult {
  isValid: boolean;
  error?: string;
}

export function validateStrategyForm(
  strategyType: StrategyType,
  params: {
    short_window?: number | string;
    long_window?: number | string;
    lookback_period?: number | string;
    threshold?: number | string;
  }
): StrategyValidationResult {
  if (strategyType === 'MOVING_AVERAGE_CROSSOVER') {
    const short = Number(params.short_window);
    const long = Number(params.long_window);

    if (!params.short_window || Number.isNaN(short) || short <= 0) {
      return { isValid: false, error: 'Short window must be a positive integer' };
    }
    if (!params.long_window || Number.isNaN(long) || long <= 0) {
      return { isValid: false, error: 'Long window must be a positive integer' };
    }
    if (short >= long) {
      return { isValid: false, error: 'short_window must be less than long_window' };
    }
    return { isValid: true };
  }

  if (strategyType === 'MEAN_REVERSION') {
    const lookback = Number(params.lookback_period);
    const threshold = Number(params.threshold);

    if (!params.lookback_period || Number.isNaN(lookback) || lookback < 2) {
      return { isValid: false, error: 'Lookback period must be an integer at least 2' };
    }
    if (params.threshold === undefined || params.threshold === '' || Number.isNaN(threshold) || threshold <= 0) {
      return { isValid: false, error: 'Threshold must be a number greater than 0' };
    }
    return { isValid: true };
  }

  return { isValid: false, error: 'Unknown strategy type' };
}
