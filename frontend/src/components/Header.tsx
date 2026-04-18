'use client';
import { clsx } from 'clsx';
import { RefreshCw, Wifi, WifiOff } from 'lucide-react';
import { useAppStore } from '@/lib/store';

interface HeaderProps {
  wsConnected: boolean;
  onRefreshIntervalChange: (interval: number) => void;
  onManualRefresh: () => void;
}

const INTERVALS = [5, 10, 15, 30, 60];
const STATUS_LABELS: Record<string, string> = {
  pre_open: '集合竞价',
  call_auction: '竞价',
  morning: '上午交易',
  lunch: '午盘',
  afternoon: '下午交易',
  closed: '已收盘',
  weekend: '休市',
};

export function Header({ wsConnected, onRefreshIntervalChange, onManualRefresh }: HeaderProps) {
  const { refreshInterval, setRefreshInterval, marketStatus } = useAppStore();

  const isTrading = marketStatus === 'morning' || marketStatus === 'afternoon';

  return (
    <header className="sticky top-0 z-50 bg-dark-bg/95 backdrop-blur border-b border-border">
      <div className="max-w-screen-2xl mx-auto px-4 py-2 flex items-center justify-between">
        {/* Logo */}
        <div className="flex items-center gap-3">
          <div className="text-gold font-bold text-base leading-none">
            📈 A股实时分析
          </div>
          <div className="hidden sm:flex items-center gap-1.5">
            <div className={clsx(
              'w-2 h-2 rounded-full',
              isTrading ? 'bg-fall animate-pulse' : 'bg-flat'
            )} />
            <span className={clsx(
              'text-xs',
              isTrading ? 'text-fall' : 'text-text-secondary'
            )}>
              {STATUS_LABELS[marketStatus] || '未知'}
            </span>
          </div>
        </div>

        {/* Controls */}
        <div className="flex items-center gap-3">
          {/* WS status */}
          <div className={clsx(
            'flex items-center gap-1 text-xs',
            wsConnected ? 'text-fall' : 'text-text-secondary'
          )}>
            {wsConnected
              ? <Wifi className="w-3.5 h-3.5" />
              : <WifiOff className="w-3.5 h-3.5" />
            }
            <span className="hidden sm:inline">
              {wsConnected ? '实时连接' : '断开'}
            </span>
          </div>

          {/* Refresh interval */}
          <div className="flex items-center gap-1">
            <span className="text-xs text-text-secondary hidden sm:inline">刷新:</span>
            <select
              value={refreshInterval}
              onChange={e => {
                const v = parseInt(e.target.value);
                setRefreshInterval(v);
                onRefreshIntervalChange(v);
              }}
              className="bg-card-bg border border-border rounded text-xs text-text-primary px-1.5 py-1 focus:outline-none focus:border-accent-blue"
            >
              {INTERVALS.map(i => (
                <option key={i} value={i}>{i}秒</option>
              ))}
            </select>
          </div>

          {/* Manual refresh */}
          <button
            onClick={onManualRefresh}
            className="p-1.5 rounded border border-border text-text-secondary hover:text-text-primary hover:border-text-secondary transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </header>
  );
}
