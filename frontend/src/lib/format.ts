/**
 * Formatting utilities conforming to the project contract:
 * - fractions to percent with one decimal
 * - Sharpe with two decimals
 * - currency in en-IN
 * - dates as YYYY-MM-DD
 */

export function formatPercent(
  fraction: number | null | undefined,
  options?: { showPositiveSign?: boolean }
): string {
  if (fraction === null || fraction === undefined || Number.isNaN(fraction)) {
    return '—';
  }
  const percent = fraction * 100;
  const formatted = percent.toFixed(1);
  if (options?.showPositiveSign && percent > 0) {
    return `+${formatted}%`;
  }
  return `${formatted}%`;
}

export function formatSharpe(val: number | null | undefined): string {
  if (val === null || val === undefined || Number.isNaN(val)) {
    return '—';
  }
  return val.toFixed(2);
}

export function formatCurrency(
  amount: number | null | undefined,
  currencyCode: string = 'INR'
): string {
  if (amount === null || amount === undefined || Number.isNaN(amount)) {
    return '—';
  }
  try {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: currencyCode,
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(amount);
  } catch {
    return `₹${amount.toFixed(2)}`;
  }
}

export function formatDate(val: string | Date | null | undefined): string {
  if (!val) {
    return '—';
  }
  if (typeof val === 'string') {
    // If it's already YYYY-MM-DD, return it
    if (/^\d{4}-\d{2}-\d{2}$/.test(val)) {
      return val;
    }
    const d = new Date(val);
    if (Number.isNaN(d.getTime())) return val;
    return d.toISOString().split('T')[0];
  }
  if (val instanceof Date) {
    if (Number.isNaN(val.getTime())) return '—';
    return val.toISOString().split('T')[0];
  }
  return '—';
}
