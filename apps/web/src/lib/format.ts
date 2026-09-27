/**
 * NEXORA ATLAS - Centralized Financial & Metric Formatting Utilities
 * Standardizes Indian currency numbering (Lakhs/Crores), international currencies,
 * UTC to Asia/Kolkata dates, and percentages across all views.
 */

export function parseNumber(val: number | string | null | undefined): number {
  if (val === null || val === undefined) return 0;
  if (typeof val === 'number') return val;
  const parsed = parseFloat(val);
  return isNaN(parsed) ? 0 : parsed;
}

/**
 * Formats a monetary amount into standard Indian currency format (e.g. ₹36,83,194.61)
 * or compact financial notation (e.g. ₹36.83L, ₹4.60L, ₹2.40Cr).
 */
export function formatCurrency(
  amount: number | string | null | undefined,
  currency: string = 'INR',
  compact: boolean = false
): string {
  const num = parseNumber(amount);
  const isNegative = num < 0;
  const absNum = Math.abs(num);

  const symbol = currency === 'INR' ? '₹' : currency === 'USD' ? '$' : currency === 'EUR' ? '€' : currency === 'GBP' ? '£' : `${currency} `;

  if (compact) {
    let formatted = '';
    if (currency === 'INR') {
      if (absNum >= 10000000) {
        // Crores (>= 1 Cr)
        formatted = `${symbol}${(absNum / 10000000).toFixed(2)}Cr`;
      } else if (absNum >= 100000) {
        // Lakhs (>= 1 Lakh)
        formatted = `${symbol}${(absNum / 100000).toFixed(2)}L`;
      } else if (absNum >= 1000) {
        formatted = `${symbol}${(absNum / 1000).toFixed(1)}K`;
      } else {
        formatted = `${symbol}${absNum.toFixed(0)}`;
      }
    } else {
      // International compact (M, K)
      if (absNum >= 1000000) {
        formatted = `${symbol}${(absNum / 1000000).toFixed(2)}M`;
      } else if (absNum >= 1000) {
        formatted = `${symbol}${(absNum / 1000).toFixed(1)}K`;
      } else {
        formatted = `${symbol}${absNum.toFixed(0)}`;
      }
    }
    return isNegative ? `-${formatted}` : formatted;
  }

  // Exact tabular formatting
  try {
    const locale = currency === 'INR' ? 'en-IN' : 'en-US';
    return new Intl.NumberFormat(locale, {
      style: 'currency',
      currency: currency,
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(num);
  } catch {
    return `${symbol}${num.toFixed(2)}`;
  }
}

/**
 * Formats UTC ISO date strings into clean display strings in Asia/Kolkata timezone.
 */
export function formatDate(
  dateStr: string | null | undefined,
  style: 'short' | 'medium' | 'full' = 'short'
): string {
  if (!dateStr) return '—';
  try {
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return dateStr;

    const timeZone = 'Asia/Kolkata';

    if (style === 'short') {
      // e.g. "14 Sep"
      return new Intl.DateTimeFormat('en-IN', {
        timeZone,
        day: 'numeric',
        month: 'short',
      }).format(d);
    }

    if (style === 'medium') {
      // e.g. "14 Sep 2026"
      return new Intl.DateTimeFormat('en-IN', {
        timeZone,
        day: 'numeric',
        month: 'short',
        year: 'numeric',
      }).format(d);
    }

    // e.g. "14 Sep 2026, 14:00 IST"
    return new Intl.DateTimeFormat('en-IN', {
      timeZone,
      day: 'numeric',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      timeZoneName: 'short',
    }).format(d);
  } catch {
    return dateStr;
  }
}

/**
 * Formats a signed percentage change (e.g. +38.24%, -12.49%, 0.00%).
 */
export function formatPercent(pct: number | string | null | undefined): string {
  if (pct === null || pct === undefined) return '—';
  const num = parseNumber(pct);
  const sign = num > 0 ? '+' : '';
  return `${sign}${num.toFixed(2)}%`;
}

/**
 * Formats raw counts with commas (e.g. 5,220).
 */
export function formatNumber(num: number | string | null | undefined): string {
  const n = parseNumber(num);
  return new Intl.NumberFormat('en-US').format(n);
}
