import { describe, it, expect } from 'vitest';
import { validateStrategyForm } from './strategy-validation';

describe('strategy form validation', () => {
  describe('MOVING_AVERAGE_CROSSOVER', () => {
    it('validates short_window < long_window', () => {
      const valid = validateStrategyForm('MOVING_AVERAGE_CROSSOVER', {
        short_window: 20,
        long_window: 50,
      });
      expect(valid.isValid).toBe(true);
      expect(valid.error).toBeUndefined();
    });

    it('rejects short_window >= long_window', () => {
      const invalidEqual = validateStrategyForm('MOVING_AVERAGE_CROSSOVER', {
        short_window: 50,
        long_window: 50,
      });
      expect(invalidEqual.isValid).toBe(false);
      expect(invalidEqual.error).toBe('short_window must be less than long_window');

      const invalidGreater = validateStrategyForm('MOVING_AVERAGE_CROSSOVER', {
        short_window: 60,
        long_window: 20,
      });
      expect(invalidGreater.isValid).toBe(false);
      expect(invalidGreater.error).toBe('short_window must be less than long_window');
    });

    it('rejects missing or zero windows', () => {
      const invalidZero = validateStrategyForm('MOVING_AVERAGE_CROSSOVER', {
        short_window: 0,
        long_window: 50,
      });
      expect(invalidZero.isValid).toBe(false);
    });
  });

  describe('MEAN_REVERSION', () => {
    it('validates lookback >= 2 and threshold > 0', () => {
      const valid = validateStrategyForm('MEAN_REVERSION', {
        lookback_period: 20,
        threshold: 2.0,
      });
      expect(valid.isValid).toBe(true);
    });

    it('rejects lookback < 2', () => {
      const invalid = validateStrategyForm('MEAN_REVERSION', {
        lookback_period: 1,
        threshold: 2.0,
      });
      expect(invalid.isValid).toBe(false);
      expect(invalid.error).toContain('at least 2');
    });

    it('rejects threshold <= 0', () => {
      const invalid = validateStrategyForm('MEAN_REVERSION', {
        lookback_period: 10,
        threshold: 0,
      });
      expect(invalid.isValid).toBe(false);
      expect(invalid.error).toContain('greater than 0');
    });
  });
});
