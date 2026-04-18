'use client';
import { clsx } from 'clsx';
import type { MarketOverview } from '@/types/api';
import { formatNetFlow, getPriceColorClass } from '@/lib/format';

interface MarketPanelProps {
  overview: MarketOverview | null;
  loading?: boolean;
}

export function MarketOverviewPanel({ overview, loading }: MarketPanelProps) {
  if (loading && !overview) {
    return (
      <div className="space-y-3 animate-pulse">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="bg-card-bg border border-border rounded-xl p-3 h-16" />
        ))}
      </div>
    );
  }

  if (!overview) return null;
  const { sentiment, northbound, limit_up_pool } = overview;

  return (
    <div className="space-y-3">
      {/* Market Status + Sentiment */}
      <div className="bg-card-bg border border-border rounded-xl p-3">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-semibold text-text-primary">市场状态</span>
          <span className={clsx(
            'text-xs px-2 py-0.5 rounded-full',
            sentiment.market_status === 'morning' || sentiment.market_status === 'afternoon'
              ? 'bg-fall/20 text-fall' : 'bg-border/50 text-text-secondary'
          )}>
            {sentiment.market_status_label}
          </span>
        </div>
        <div className="flex items-center justify-between">
          <div className="text-center">
            <div className="text-lg font-bold text-rise">{sentiment.limit_up_count}</div>
            <div className="text-[10px] text-text-secondary">涨停</div>
          </div>
          <div className="text-center">
            <div className="text-lg font-bold text-fall">{sentiment.limit_down_count}</div>
            <div className="text-[10px] text-text-secondary">跌停</div>
          </div>
          <div className="text-center">
            <div className={clsx(
              'text-lg font-bold',
              sentiment.sentiment_score >= 60 ? 'text-rise' : sentiment.sentiment_score <= 40 ? 'text-fall' : 'text-yellow-400'
            )}>
              {sentiment.sentiment_score}
            </div>
            <div className="text-[10px] text-text-secondary">情绪值</div>
          </div>
          <div className="text-center">
            <div className={clsx(
              'text-sm font-semibold',
              sentiment.sentiment_score >= 60 ? 'text-rise' : sentiment.sentiment_score <= 40 ? 'text-fall' : 'text-yellow-400'
            )}>
              {sentiment.sentiment_label}
            </div>
            <div className="text-[10px] text-text-secondary">市场情绪</div>
          </div>
        </div>
      </div>

      {/* Northbound */}
      {northbound && (
        <div className="bg-card-bg border border-border rounded-xl p-3">
          <div className="text-xs font-semibold text-text-primary mb-2">北向资金</div>
          <div className={clsx(
            'text-xl font-bold font-mono mb-1',
            northbound.total_net_inflow >= 0 ? 'text-rise' : 'text-fall'
          )}>
            {formatNetFlow(northbound.total_net_inflow)}
          </div>
          <div className="flex gap-4 text-[10px] text-text-secondary">
            <span>沪: {formatNetFlow(northbound.sh_net_inflow)}</span>
            <span>深: {formatNetFlow(northbound.sz_net_inflow)}</span>
          </div>
        </div>
      )}

      {/* Limit-up pool (top 5) */}
      <div className="bg-card-bg border border-border rounded-xl p-3">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-semibold text-text-primary">涨停板</span>
          <span className="text-xs text-gold font-mono">{limit_up_pool.count}只</span>
        </div>
        <div className="space-y-1">
          {limit_up_pool.stocks.slice(0, 8).map(s => (
            <div key={s.symbol} className="flex items-center justify-between text-xs py-0.5">
              <div className="flex items-center gap-1.5">
                <span className="font-mono text-text-secondary text-[10px]">{s.symbol}</span>
                <span className="text-text-primary">{s.name}</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="font-mono text-rise">{s.price.toFixed(2)}</span>
                <span className="text-[10px] bg-rise/20 text-rise px-1 rounded">
                  +{s.change_pct.toFixed(2)}%
                </span>
              </div>
            </div>
          ))}
          {limit_up_pool.count === 0 && (
            <div className="text-text-secondary text-xs">暂无涨停数据</div>
          )}
        </div>
      </div>

      {/* Top sectors */}
      <div className="bg-card-bg border border-border rounded-xl p-3">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-semibold text-text-primary">热门板块</span>
          <span className="text-[10px] text-text-secondary">轮动强度: {(overview.sectors.rotation_strength * 100).toFixed(0)}%</span>
        </div>
        <div className="space-y-1">
          {overview.sectors.sectors.slice(0, 8).map(s => (
            <div key={s.name} className="flex items-center justify-between text-xs py-0.5">
              <span className="text-text-primary truncate max-w-[120px]">{s.name}</span>
              <div className="flex items-center gap-1.5">
                <span className={clsx('font-mono text-xs', getPriceColorClass(s.change_pct))}>
                  {s.change_pct >= 0 ? '+' : ''}{s.change_pct.toFixed(2)}%
                </span>
                {s.net_inflow !== 0 && (
                  <span className={clsx('text-[10px]', s.net_inflow >= 0 ? 'text-rise' : 'text-fall')}>
                    {formatNetFlow(s.net_inflow)}
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
