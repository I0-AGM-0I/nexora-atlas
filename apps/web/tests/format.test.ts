import { describe, it, expect } from 'vitest';
import { formatCurrency, formatPercent, formatDate, parseNumber } from '../src/lib/format';

describe('Financial & Localization Formatters', () => {
  describe('formatCurrency', () => {
    it('formats numbers with standard Indian commas and rupee symbol', () => {
      const formatted = formatCurrency(3683194.61);
      expect(formatted).toContain('₹');
      // Indian numbering format: 36,83,194.61
      expect(formatted).toContain('36,83,194');
    });

    it('formats compact Lakhs notation correctly', () => {
      const formatted = formatCurrency(460000, 'INR', true);
      expect(formatted).toBe('₹4.60L');
    });

    it('formats compact Crores notation correctly', () => {
      const formatted = formatCurrency(24000000, 'INR', true);
      expect(formatted).toBe('₹2.40Cr');
    });

    it('handles zero gracefully', () => {
      const formatted = formatCurrency(0);
      expect(formatted).toContain('₹0.00');
    });

    it('handles null and undefined safely', () => {
      expect(formatCurrency(null)).toContain('₹0.00');
      expect(formatCurrency(undefined)).toContain('₹0.00');
    });

    it('handles string numbers accurately without loss of precision', () => {
      const formatted = formatCurrency('1250000.00', 'INR', true);
      expect(formatted).toBe('₹12.50L');
    });
  });

  describe('formatPercent', () => {
    it('formats positive and negative percentages with signs', () => {
      expect(formatPercent(12.34)).toBe('+12.34%');
      expect(formatPercent(-8.5)).toBe('-8.50%');
    });

    it('handles null and undefined', () => {
      expect(formatPercent(null)).toBe('—');
      expect(formatPercent(undefined)).toBe('—');
    });
  });

  describe('formatDate', () => {
    it('formats ISO timestamps into short and medium IST dates', () => {
      const shortDate = formatDate('2026-03-15T12:00:00Z', 'short');
      expect(shortDate).toContain('15');
      expect(shortDate).toContain('Mar');

      const mediumDate = formatDate('2026-03-15T12:00:00Z', 'medium');
      expect(mediumDate).toContain('2026');
      expect(mediumDate).toContain('Mar');
    });

    it('handles invalid dates safely', () => {
      expect(formatDate('invalid-date')).toBe('invalid-date');
    });
  });

  describe('parseNumber', () => {
    it('extracts numbers from strings and handles fallbacks', () => {
      expect(parseNumber('1234.56')).toBe(1234.56);
      expect(parseNumber(789)).toBe(789);
      expect(parseNumber(null)).toBe(0);
      expect(parseNumber('invalid')).toBe(0);
    });
  });
});
