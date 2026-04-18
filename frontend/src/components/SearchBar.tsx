'use client';
import { useState, useCallback } from 'react';
import { Search } from 'lucide-react';
import { clsx } from 'clsx';
import { useAppStore } from '@/lib/store';

// Common A-share stocks for quick access
const QUICK_STOCKS = [
  { symbol: '000001', name: '平安银行' },
  { symbol: '600036', name: '招商银行' },
  { symbol: '600519', name: '贵州茅台' },
  { symbol: '300750', name: '宁德时代' },
  { symbol: '000858', name: '五粮液' },
  { symbol: '601318', name: '中国平安' },
  { symbol: '600900', name: '长江电力' },
  { symbol: '688599', name: '天合光能' },
];

interface SearchBarProps {
  onSearch: (symbol: string) => void;
}

export function SearchBar({ onSearch }: SearchBarProps) {
  const [input, setInput] = useState('');
  const [error, setError] = useState('');
  const { selectedSymbol, watchlist, addToWatchlist, removeFromWatchlist } = useAppStore();

  const handleSubmit = useCallback((e: React.FormEvent | React.MouseEvent, sym?: string) => {
    e.preventDefault();
    const symbol = (sym || input).trim();
    if (!symbol) return;
    if (!/^\d{6}$/.test(symbol)) {
      setError('请输入6位股票代码');
      return;
    }
    setError('');
    if (!sym) {
      addToWatchlist(symbol);
    }
    onSearch(symbol);
    if (!sym) setInput('');
  }, [addToWatchlist, input, onSearch]);

  return (
    <div className="space-y-3">
      {/* Search form */}
      <form onSubmit={handleSubmit} className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-secondary" />
        <input
          type="text"
          value={input}
          onChange={e => { setInput(e.target.value); setError(''); }}
          placeholder="输入6位股票代码..."
          className={clsx(
            'w-full bg-[#0d1117] border rounded-lg pl-9 pr-4 py-2',
            'text-text-primary text-sm placeholder:text-text-secondary',
            'focus:outline-none focus:border-accent-blue transition-colors',
            error ? 'border-rise' : 'border-border hover:border-text-secondary'
          )}
          maxLength={6}
        />
        <button
          type="submit"
          className="absolute right-2 top-1/2 -translate-y-1/2 bg-accent-blue/80 hover:bg-accent-blue text-white text-xs px-2.5 py-1 rounded transition-colors"
        >
          查询
        </button>
      </form>
      {error && <p className="text-rise text-xs px-1">{error}</p>}

      {/* Quick access */}
      <div>
        <div className="text-[10px] text-text-secondary mb-1.5 px-0.5">快速访问</div>
        <div className="flex flex-wrap gap-1.5">
          {QUICK_STOCKS.map(s => (
            <button
              key={s.symbol}
              type="button"
              onClick={e => handleSubmit(e, s.symbol)}
              title={s.name}
              className={clsx(
                'text-[11px] px-2 py-1 rounded border transition-colors',
                selectedSymbol === s.symbol
                  ? 'bg-accent-blue/20 border-accent-blue/50 text-accent-blue'
                  : 'bg-border/20 border-border/40 text-text-secondary hover:text-text-primary hover:border-text-secondary'
              )}
            >
              {s.symbol}
            </button>
          ))}
        </div>
      </div>

      {/* Watchlist */}
      {watchlist.length > 0 && (
        <div>
          <div className="text-[10px] text-text-secondary mb-1.5 px-0.5">自选股</div>
          <div className="flex flex-wrap gap-1.5">
            {watchlist.map(sym => (
              <div
                key={sym}
                className={clsx(
                  'flex items-center rounded border transition-colors overflow-hidden',
                  selectedSymbol === sym
                    ? 'bg-accent-blue/20 border-accent-blue/50 text-accent-blue'
                    : 'bg-border/20 border-border/40 text-text-secondary hover:text-text-primary'
                )}
              >
                <button
                  type="button"
                  onClick={e => handleSubmit(e, sym)}
                  className="px-2 py-1 text-[11px]"
                >
                  {sym}
                </button>
                <button
                  type="button"
                  onClick={() => removeFromWatchlist(sym)}
                  className="border-l border-current/15 px-1.5 py-1 text-[10px] opacity-70 hover:opacity-100"
                  aria-label={`移除 ${sym}`}
                  title={`移除 ${sym}`}
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
