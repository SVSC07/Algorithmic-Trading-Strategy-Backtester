import { describe, it, expect } from 'vitest';
import { formatPercent, formatSharpe, formatCurrency, formatDate } from './format';

describe('format utilities', () => {
  it('formats fractions to percent with one decimal', () => {
    expect(formatPercent(0.1856)).toBe('18.6%');
    expect(formatPercent(-0.0523)).toBe('-5.2%');
    expect(formatPercent(0.1856, { showPositiveSign: true })).toBe('+18.6%');
    expect(formatPercent(-0.052, { showPositiveSign: true })).toBe('-5.2%');
    expect(formatPercent(0)).toBe('0.0%');
    expect(formatPercent(null)).toBe('—');
    expect(formatPercent(undefined)).toBe('—');
  });

  it('formats Sharpe ratio with two decimals', () => {
    expect(formatSharpe(1.854)).toBe('1.85');
    expect(formatSharpe(0.5)).toBe('0.50');
    expect(formatSharpe(-0.432)).toBe('-0.43');
    expect(formatSharpe(0)).toBe('0.00');
    expect(formatSharpe(null)).toBe('—');
  });

  it('formats currency in en-IN style', () => {
    const formatted = formatCurrency(100000);
    // en-IN format separates thousands and lakhs: 1,00,000.00
    expect(formatted).toContain('1,00,000.00');
    expect(formatCurrency(null)).toBe('—');
  });

  it('formats dates as YYYY-MM-DD', () => {
    expect(formatDate('2024-03-15')).toBe('2024-03-15');
    expect(formatDate(new Date('2024-05-20T10:00:00Z'))).toBe('2024-05-20');
    expect(formatDate(null)).toBe('—');
  });
});
