'use client';
import { useCallback, useEffect, useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import { clsx } from 'clsx';

import { Header } from '@/components/Header';
import { SearchBar } from '@/components/SearchBar';
import { StockQuoteCard } from '@/components/StockQuoteCard';
import { MinuteChart } from '@/components/MinuteChart';
import { CandlestickChart } from '@/components/CandlestickChart';
import { SignalBoard } from '@/components/SignalBoard';
import { CapitalFlowPanel } from '@/components/CapitalFlowPanel';
import { MarketOverviewPanel } from '@/components/MarketOverviewPanel';
import { DataStatusBadge } from '@/components/DataStatusBadge';
import { useStockWebSocket } from '@/hooks/useWebSocket';
import { useAppStore } from '@/lib/store';
import {
  fetchStockAnalysis, fetchHistory, fetchMarketOverview, fetchMarketStatus
} from '@/lib/api';
import type { Quote, FullAnalysis } from '@/types/api';

type ChartMode = 'minute' | 'daily' | 'weekly';

export default function HomePage() {
  const queryClient = useQueryClient();
  const {
    selectedSymbol, setSelectedSymbol, refreshInterval,
    liveQuotes, updateLiveQuote, setMarketStatus,
    setMarketOverview,
  } = useAppStore();

  const [chartMode, setChartMode] = useState<ChartMode>('minute');

  // ---------------------------------------------------------------- //
  //  API queries                                                       //
  // ---------------------------------------------------------------- //

  const analysisQuery = useQuery({
    queryKey: ['analysis', selectedSymbol],
    queryFn: () => fetchStockAnalysis(selectedSymbol),
    refetchInterval: refreshInterval * 1000,
    staleTime: (refreshInterval - 1) * 1000,
    retry: 2,
    enabled: !!selectedSymbol,
  });

  const historyQuery = useQuery({
    queryKey: ['history', selectedSymbol, chartMode],
    queryFn: () => fetchHistory(
      selectedSymbol,
      chartMode === 'daily' ? 'daily' : chartMode === 'weekly' ? 'weekly' : 'daily',
      120
    ),
    enabled: chartMode !== 'minute',
    staleTime: 60000,
    retry: 2,
  });

  const overviewQuery = useQuery({
    queryKey: ['market-overview'],
    queryFn: fetchMarketOverview,
    refetchInterval: 30000,
    staleTime: 25000,
    retry: 2,
  });

  // Market status poll
  useEffect(() => {
    const pollStatus = async () => {
      try {
        const data = await fetchMarketStatus();
        setMarketStatus(data.status);
      } catch {}
    };
    pollStatus();
    const id = setInterval(pollStatus, 60000);
    return () => clearInterval(id);
  }, [setMarketStatus]);

  // Sync market overview to store
  useEffect(() => {
    if (overviewQuery.data) setMarketOverview(overviewQuery.data);
  }, [overviewQuery.data, setMarketOverview]);

  // ---------------------------------------------------------------- //
  //  WebSocket                                                         //
  // ---------------------------------------------------------------- //

  const handleQuoteUpdate = useCallback((symbol: string, quote: Quote) => {
    updateLiveQuote(symbol, quote);
    // Invalidate query to merge with live data
    if (symbol === selectedSymbol) {
      queryClient.setQueryData<FullAnalysis>(['analysis', symbol], (old) => {
        if (!old) return old;
        return { ...old, quote };
      });
    }
  }, [updateLiveQuote, selectedSymbol, queryClient]);

  const handleMarketPulse = useCallback((status: string) => {
    setMarketStatus(status);
  }, [setMarketStatus]);

  const { connected, setInterval: wsSetInterval } = useStockWebSocket({
    symbols: [selectedSymbol],
    onQuoteUpdate: handleQuoteUpdate,
    onMarketPulse: handleMarketPulse,
    refreshInterval,
    enabled: true,
  });

  // ---------------------------------------------------------------- //
  //  Handlers                                                          //
  // ---------------------------------------------------------------- //

  const handleSearch = useCallback((symbol: string) => {
    setSelectedSymbol(symbol);
    queryClient.invalidateQueries({ queryKey: ['analysis', symbol] });
  }, [setSelectedSymbol, queryClient]);

  const handleManualRefresh = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: ['analysis', selectedSymbol] });
    queryClient.invalidateQueries({ queryKey: ['market-overview'] });
    toast.success('数据已刷新', { duration: 1500 });
  }, [queryClient, selectedSymbol]);

  const handleIntervalChange = useCallback((interval: number) => {
    wsSetInterval(interval);
  }, [wsSetInterval]);

  // ---------------------------------------------------------------- //
  //  Derived data — prefer live WebSocket quote                        //
  // ---------------------------------------------------------------- //

  const analysis = analysisQuery.data;
  const liveQuote = liveQuotes[selectedSymbol];
  const displayQuote = liveQuote ?? analysis?.quote ?? null;

  // Merge live quote into analysis for display
  const displayAnalysis: FullAnalysis | null = analysis
    ? { ...analysis, quote: displayQuote }
    : null;

  return (
    <div className="min-h-screen bg-dark-bg">
      <Header
        wsConnected={connected}
        onRefreshIntervalChange={handleIntervalChange}
        onManualRefresh={handleManualRefresh}
      />

      <div className="max-w-screen-2xl mx-auto px-3 py-3">
        <div className="grid grid-cols-12 gap-3 min-h-[calc(100vh-60px)]">

          {/* ---- LEFT SIDEBAR ---- */}
          <aside className="col-span-12 lg:col-span-2 space-y-3">
            <div className="bg-card-bg border border-border rounded-xl p-3">
              <SearchBar onSearch={handleSearch} />
            </div>
            <MarketOverviewPanel
              overview={overviewQuery.data ?? null}
              loading={overviewQuery.isLoading}
            />
          </aside>

          {/* ---- MAIN CONTENT ---- */}
          <main className="col-span-12 lg:col-span-7 space-y-3">
            {/* Quote card */}
            <StockQuoteCard
              quote={displayQuote}
              loading={analysisQuery.isLoading}
              isFallback={displayAnalysis?.is_fallback}
              fallbackMessage={displayAnalysis?.fallback_message}
            />

            {/* Chart tabs */}
            <div className="bg-card-bg border border-border rounded-xl overflow-hidden">
              <div className="flex items-center border-b border-border px-3 pt-2 gap-1">
                {(['minute', 'daily', 'weekly'] as ChartMode[]).map(mode => (
                  <button
                    key={mode}
                    onClick={() => setChartMode(mode)}
                    className={clsx(
                      'px-3 py-1.5 text-xs rounded-t border-b-2 transition-colors',
                      chartMode === mode
                        ? 'border-accent-blue text-accent-blue bg-accent-blue/5'
                        : 'border-transparent text-text-secondary hover:text-text-primary'
                    )}
                  >
                    {mode === 'minute' ? '分时' : mode === 'daily' ? '日K' : '周K'}
                  </button>
                ))}
                <div className="ml-auto flex items-center gap-1.5 pb-1">
                  {analysisQuery.isFetching && (
                    <span className="text-[10px] text-text-secondary animate-pulse">更新中...</span>
                  )}
                  {analysis?.quote?.data_status && (
                    <DataStatusBadge status={analysis.quote.data_status} />
                  )}
                </div>
              </div>
              <div className="p-2">
                {chartMode === 'minute' ? (
                  <MinuteChart
                    quote={displayQuote}
                    minuteData={analysis?.minute_data ?? null}
                  />
                ) : (
                  <CandlestickChart
                    data={historyQuery.data?.data ?? []}
                    showMA
                  />
                )}
              </div>
            </div>

            {/* Capital flow */}
            <CapitalFlowPanel flow={analysis?.capital_flow ?? null} />
          </main>

          {/* ---- RIGHT SIDEBAR ---- */}
          <aside className="col-span-12 lg:col-span-3 space-y-3">
            <SignalBoard
              technical={analysis?.technical ?? null}
              score={analysis?.score ?? null}
            />

            {/* Provider health */}
            {overviewQuery.data?.provider_status && (
              <div className="bg-card-bg border border-border rounded-xl p-3">
                <div className="text-xs font-semibold text-text-primary mb-2">数据源状态</div>
                <div className="space-y-1">
                  {Object.entries(overviewQuery.data.provider_status.providers).map(([name, status]) => (
                    <div key={name} className="flex items-center justify-between text-xs">
                      <span className="text-text-secondary capitalize">{name}</span>
                      <span className={clsx(
                        'text-[10px] px-1.5 py-0.5 rounded',
                        status === 'ok' ? 'bg-fall/20 text-fall'
                          : status === 'degraded' ? 'bg-yellow-500/20 text-yellow-400'
                          : 'bg-rise/20 text-rise'
                      )}>
                        {status === 'ok' ? '正常' : status === 'degraded' ? '降级' : '故障'}
                      </span>
                    </div>
                  ))}
                  <div className="text-[10px] text-text-secondary border-t border-border/30 pt-1 mt-1">
                    更新: {overviewQuery.data.provider_status.last_updated}
                  </div>
                </div>
              </div>
            )}
          </aside>

        </div>
      </div>
    </div>
  );
}
