import { describe, it, expect } from 'vitest';
import { formatAmount, formatDate, formatNumber } from '../lib/utils';

describe('utils', () => {
  describe('formatAmount', () => {
    it('formats small number as currency', () => {
      const result = formatAmount(1000);
      expect(result).toContain('1,000');
    });

    it('formats large number as 万元', () => {
      const result = formatAmount(10000);
      expect(result).toContain('1.00万元');
    });

    it('formats very large number as 亿元', () => {
      const result = formatAmount(100000000);
      expect(result).toContain('1.00亿元');
    });

    it('returns dash for null', () => {
      expect(formatAmount(null)).toBe('-');
    });

    it('returns dash for undefined', () => {
      expect(formatAmount(undefined)).toBe('-');
    });
  });

  describe('formatDate', () => {
    it('extracts date from ISO string', () => {
      expect(formatDate('2024-01-15T10:30:00Z')).toBe('2024-01-15');
    });

    it('returns dash for null', () => {
      expect(formatDate(null)).toBe('-');
    });
  });

  describe('formatNumber', () => {
    it('formats number with locale', () => {
      expect(formatNumber(1000000)).toBe('1,000,000');
    });

    it('returns dash for null', () => {
      expect(formatNumber(null)).toBe('-');
    });
  });
});
