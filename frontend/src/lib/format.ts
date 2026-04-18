/**
 * Formatting utilities for China stock market display.
 */

/** Format large numbers in Chinese financial style (万/亿) */
export function formatAmount(value: number | null | undefined): string {
  if (value == null || isNaN(value)) return '--';
  const abs = Math.abs(value);
  const sign = value < 0 ? '-' : '';
  if (abs >= 1e8) return `${sign}${(abs / 1e8).toFixed(2)}亿`;
  if (abs >= 1e4) return `${sign}${(abs / 1e4).toFixed(2)}万`;
  return `${sign}${abs.toFixed(0)}`;
}

/** Format large amount with + sign for positive */
export function formatNetFlow(value: number | null | undefined): string {
  if (value == null || isNaN(value)) return '--';
  const sign = value > 0 ? '+' : '';
  return sign + formatAmount(value);
}

/** Format percentage with sign and color class */
export function formatPct(value: number | null | undefined): string {
  if (value == null || isNaN(value)) return '--';
  const sign = value > 0 ? '+' : '';
  return `${sign}${value.toFixed(2)}%`;
}

/** Get Tailwind color class for price change */
export function getPriceColorClass(value: number): string {
  if (value > 0) return 'text-rise';
  if (value < 0) return 'text-fall';
  return 'text-flat';
}

/** Get background color class for price change */
export function getPriceBgClass(value: number): string {
  if (value > 0) return 'bg-rise/10 border-rise/30';
  if (value < 0) return 'bg-fall/10 border-fall/30';
  return 'bg-flat/10 border-flat/30';
}

/** Format volume (shares) */
export function formatVolume(value: number | null | undefined): string {
  if (value == null || isNaN(value)) return '--';
  if (value >= 1e8) return `${(value / 1e8).toFixed(2)}亿股`;
  if (value >= 1e4) return `${(value / 1e4).toFixed(2)}万股`;
  return `${value}股`;
}

/** Format price to currency string */
export function formatPrice(value: number | null | undefined): string {
  if (value == null || isNaN(value) || value <= 0) return '--';
  return value.toFixed(2);
}

/** Get color for RSI signal */
export function getRsiColor(rsi: number): string {
  if (rsi >= 70) return 'text-rise';
  if (rsi <= 30) return 'text-fall';
  return 'text-text-secondary';
}

/** Get grade badge color */
export function getGradeColor(grade: string): string {
  const map: Record<string, string> = {
    'A+': 'bg-rise text-white',
    'A': 'bg-rise/80 text-white',
    'B+': 'bg-yellow-500 text-white',
    'B': 'bg-yellow-500/80 text-white',
    'C': 'bg-flat/40 text-text-primary',
    'D': 'bg-fall/60 text-white',
    'F': 'bg-fall text-white',
  };
  return map[grade] || 'bg-flat/40 text-text-primary';
}

/** Get recommendation badge color */
export function getRecColor(rec: string): string {
  const map: Record<string, string> = {
    '强烈买入': 'bg-rise text-white',
    '买入': 'bg-rise/70 text-white',
    '观望': 'bg-flat/40 text-text-primary',
    '减仓': 'bg-fall/70 text-white',
    '出局': 'bg-fall text-white',
  };
  return map[rec] || 'bg-flat/40 text-text-primary';
}

/** Get risk level styling */
export function getRiskStyle(level: string): { border: string; bg: string } {
  const map: Record<string, { border: string; bg: string }> = {
    low: { border: 'border-fall/40', bg: 'bg-fall/5' },
    medium: { border: 'border-yellow-500/40', bg: 'bg-yellow-500/5' },
    high: { border: 'border-rise/40', bg: 'bg-rise/5' },
    extreme: { border: 'border-rise', bg: 'bg-rise/10' },
  };
  return map[level] || { border: 'border-border', bg: '' };
}

/** Format market cap */
export function formatMarketCap(value: number | null | undefined): string {
  if (value == null || !value) return '--';
  return formatAmount(value);
}

/** Get data freshness indicator */
export function getFreshnessInfo(freshness: string): { icon: string; class: string } {
  switch (freshness) {
    case 'realtime':
    case 'near_realtime':
      return { icon: '🟢', class: 'text-fall' };
    case 'delayed':
      return { icon: '🟡', class: 'text-yellow-500' };
    case 'stale':
      return { icon: '🔴', class: 'text-rise' };
    default:
      return { icon: '⚪', class: 'text-flat' };
  }
}
