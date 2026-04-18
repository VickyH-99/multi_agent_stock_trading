/**
 * Global app state store using Zustand.
 */
import { create } from 'zustand';
import type { Quote, MarketOverview } from '@/types/api';

interface AppState {
  // Watchlist
  watchlist: string[];
  addToWatchlist: (symbol: string) => void;
  removeFromWatchlist: (symbol: string) => void;

  // Live quotes (updated via WebSocket)
  liveQuotes: Record<string, Quote>;
  updateLiveQuote: (symbol: string, quote: Quote) => void;

  // Selected stock
  selectedSymbol: string;
  setSelectedSymbol: (symbol: string) => void;

  // Market status
  marketStatus: string;
  setMarketStatus: (status: string) => void;

  // Refresh interval (seconds)
  refreshInterval: number;
  setRefreshInterval: (interval: number) => void;

  // Market overview
  marketOverview: MarketOverview | null;
  setMarketOverview: (data: MarketOverview) => void;

  // Sidebar
  sidebarOpen: boolean;
  setSidebarOpen: (open: boolean) => void;
}

export const useAppStore = create<AppState>((set) => ({
  watchlist: ['000001', '600036', '300750', '000858', '600519'],
  addToWatchlist: (symbol) =>
    set((s) => ({
      watchlist: s.watchlist.includes(symbol) ? s.watchlist : [...s.watchlist, symbol],
    })),
  removeFromWatchlist: (symbol) =>
    set((s) => ({ watchlist: s.watchlist.filter((x) => x !== symbol) })),

  liveQuotes: {},
  updateLiveQuote: (symbol, quote) =>
    set((s) => ({ liveQuotes: { ...s.liveQuotes, [symbol]: quote } })),

  selectedSymbol: '000001',
  setSelectedSymbol: (symbol) => set({ selectedSymbol: symbol }),

  marketStatus: 'closed',
  setMarketStatus: (status) => set({ marketStatus: status }),

  refreshInterval: 10,
  setRefreshInterval: (interval) => set({ refreshInterval: interval }),

  marketOverview: null,
  setMarketOverview: (data) => set({ marketOverview: data }),

  sidebarOpen: true,
  setSidebarOpen: (open) => set({ sidebarOpen: open }),
}));
