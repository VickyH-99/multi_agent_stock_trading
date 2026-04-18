'use client';
import { useEffect, useRef, useState } from 'react';
import { clsx } from 'clsx';
import type { Quote } from '@/types/api';
import { formatPrice, formatPct, formatAmount, getPriceColorClass } from '@/lib/format';
import { DataStatusBadge } from './DataStatusBadge';

interface StockQuoteCardProps {
  quote: Quote | null;
  loading?: boolean;
  isFallback?: boolean;
  fallbackMessage?: string | null;
}

export function StockQuoteCard({ quote, loading, isFallback, fallbackMessage }: StockQuoteCardProps) {
  const prevPrice = useRef<number | null>(null);
  const [flashClass, setFlashClass] = useState('');
  const currentPrice = quote?.price ?? null;

  // Flash animation on price update
  useEffect(() => {
    if (currentPrice == null) return;
    const curr = currentPrice;
    const prev = prevPrice.current;
    if (prev !== null && curr !== prev) {
      const cls = curr > prev ? 'animate-flash-rise' : 'animate-flash-fall';
      setFlashClass(cls);
      const timer = setTimeout(() => setFlashClass(''), 500);
      prevPrice.current = curr;
      return () => clearTimeout(timer);
    }
    prevPrice.current = curr;
  }, [currentPrice]);

  if (loading && !quote) {
    return (
      <div className="bg-card-bg border border-border rounded-xl p-4 animate-pulse">
        <div className="h-6 bg-border rounded w-32 mb-3" />
        <div className="h-12 bg-border rounded w-48 mb-2" />
        <div className="h-4 bg-border rounded w-24" />
      </div>
    );
  }

  if (!quote) {
    return (
      <div className="bg-card-bg border border-border rounded-xl p-4 text-text-secondary text-sm">
        暂无行情数据
      </div>
    );
  }

  const isPositive = quote.change_pct >= 0;

  return (
    <div className={clsx(
      'bg-card-bg border rounded-xl p-5 transition-all',
      quote.limit_up ? 'border-gold' : quote.limit_down ? 'border-fall' : 'border-border',
    )}>
      {/* Fallback warning */}
      {isFallback && (
        <div className="mb-3 px-3 py-1.5 bg-yellow-500/10 border border-yellow-500/30 rounded-lg text-yellow-400 text-xs flex items-center gap-1.5">
          ⚠️ {fallbackMessage || 'Live data unavailable, showing latest cached data'}
        </div>
      )}

      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div>
          <div className="text-text-primary font-bold text-lg leading-tight">{quote.name}</div>
          <div className="text-text-secondary text-sm font-mono">{quote.symbol}</div>
          <div className="flex items-center gap-1.5 mt-1">
            <span className="text-xs text-text-secondary bg-border/60 px-1.5 py-0.5 rounded">
              {quote.exchange}
            </span>
            <span className="text-xs text-text-secondary">
              {quote.stock_type}
            </span>
          </div>
        </div>
        <div className="text-right">
          <DataStatusBadge status={quote.data_status} showSource />
          {quote.limit_up && (
            <div className="mt-1 text-xs font-bold bg-gold text-dark-bg px-2 py-0.5 rounded animate-pulse-fast">
              🔥 涨停
            </div>
          )}
          {quote.limit_down && (
            <div className="mt-1 text-xs font-bold bg-fall text-white px-2 py-0.5 rounded">
              跌停
            </div>
          )}
        </div>
      </div>

      {/* Price */}
      <div className={clsx(
        'rounded-lg px-3 py-2 mb-3 transition-all',
        flashClass,
        isPositive ? 'bg-rise/5' : 'bg-fall/5'
      )}>
        <div className={clsx('text-4xl font-bold font-mono tabular-nums', getPriceColorClass(quote.change_pct))}>
          {formatPrice(quote.price)}
        </div>
        <div className="flex items-center gap-3 mt-1">
          <span className={clsx('text-xl font-mono font-semibold', getPriceColorClass(quote.change_pct))}>
            {formatPct(quote.change_pct)}
          </span>
          <span className={clsx('text-base font-mono', getPriceColorClass(quote.change))}>
            {quote.change >= 0 ? '+' : ''}{formatPrice(quote.change)}
          </span>
        </div>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-2 gap-2 text-sm">
        <StatRow label="今开" value={formatPrice(quote.open_price)} />
        <StatRow label="昨收" value={formatPrice(quote.prev_close)} />
        <StatRow label="最高" value={formatPrice(quote.high)} color="text-rise" />
        <StatRow label="最低" value={formatPrice(quote.low)} color="text-fall" />
        <StatRow
          label="成交量"
          value={quote.volume >= 1e8
            ? `${(quote.volume / 1e8).toFixed(2)}亿`
            : `${(quote.volume / 1e4).toFixed(2)}万`}
        />
        <StatRow label="成交额" value={formatAmount(quote.amount)} />
        {quote.turnover_rate != null && (
          <StatRow label="换手率" value={`${quote.turnover_rate.toFixed(2)}%`} />
        )}
        {quote.pe_ratio != null && (
          <StatRow label="市盈率" value={quote.pe_ratio.toFixed(2)} />
        )}
        {quote.total_market_cap != null && (
          <StatRow label="总市值" value={formatAmount(quote.total_market_cap)} />
        )}
        {quote.circulating_market_cap != null && (
          <StatRow label="流通市值" value={formatAmount(quote.circulating_market_cap)} />
        )}
      </div>
    </div>
  );
}

function StatRow({ label, value, color }: { label: string; value: string; color?: string }) {
  return (
    <div className="flex items-center justify-between py-0.5">
      <span className="text-text-secondary text-xs">{label}</span>
      <span className={clsx('font-mono text-xs font-medium', color || 'text-text-primary')}>
        {value}
      </span>
    </div>
  );
}
