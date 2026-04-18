import axios from 'axios';
import type {
  FullAnalysis, Quote, MarketOverview, HistoryData, Sector
} from '@/types/api';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// ------------------------------------------------------------------ //
//  Stock APIs                                                          //
// ------------------------------------------------------------------ //

export async function fetchStockAnalysis(symbol: string): Promise<FullAnalysis> {
  const res = await api.get<FullAnalysis>(`/api/stock/${symbol}`);
  return res.data;
}

export async function fetchQuote(symbol: string): Promise<Quote> {
  const res = await api.get<Quote>(`/api/stock/${symbol}/quote`);
  return res.data;
}

export async function fetchBatchQuotes(symbols: string[]): Promise<Quote[]> {
  const res = await api.get<Quote[]>(`/api/stock/batch/quotes`, {
    params: { symbols: symbols.join(',') },
  });
  return res.data;
}

export async function fetchHistory(
  symbol: string,
  period: 'daily' | 'weekly' | 'monthly' = 'daily',
  count: number = 120
): Promise<HistoryData> {
  const res = await api.get<HistoryData>(`/api/stock/${symbol}/history`, {
    params: { period, count },
  });
  return res.data;
}

// ------------------------------------------------------------------ //
//  Market APIs                                                         //
// ------------------------------------------------------------------ //

export async function fetchMarketOverview(): Promise<MarketOverview> {
  const res = await api.get<MarketOverview>('/api/market/overview');
  return res.data;
}

export async function fetchSectors(): Promise<{ sectors: Sector[]; rotation_strength: number }> {
  const res = await api.get('/api/market/sectors');
  return res.data;
}

export async function fetchLimitUpPool() {
  const res = await api.get('/api/market/limit-up');
  return res.data;
}

export async function fetchNorthboundFlow() {
  const res = await api.get('/api/market/northbound');
  return res.data;
}

export async function fetchMarketStatus() {
  const res = await api.get('/api/market/status');
  return res.data;
}

export async function fetchHealth() {
  const res = await api.get('/health');
  return res.data;
}
