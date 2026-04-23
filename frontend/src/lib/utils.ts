import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatAmount(value: number | null | undefined): string {
  if (!value) return '-';
  if (value >= 100_000_000) {
    return `${(value / 100_000_000).toFixed(2)}亿元`;
  }
  if (value >= 10_000) {
    return `${(value / 10_000).toFixed(2)}万元`;
  }
  return new Intl.NumberFormat('zh-CN', { style: 'currency', currency: 'CNY' }).format(value);
}

export function formatDate(value: string | null | undefined): string {
  if (!value) return '-';
  return value.slice(0, 10);
}

export function formatNumber(value: number | null | undefined): string {
  if (value == null) return '-';
  return new Intl.NumberFormat('zh-CN').format(value);
}
