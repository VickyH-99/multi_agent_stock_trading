// ============================================================
// API Type Definitions
// ============================================================

export interface DataStatus {
  freshness: 'realtime' | 'near_realtime' | 'delayed' | 'stale' | 'unknown';
  source: string;
  timestamp: string;
  label: string;   // "🟢 实时" | "🟡 延迟" | "🔴 数据异常"
  is_live: boolean;
}

export interface Quote {
  symbol: string;
  name: string;
  price: number;
  change: number;
  change_pct: number;
  volume: number;
  amount: number;
  high: number;
  low: number;
  open_price: number;
  prev_close: number;
  turnover_rate: number | null;
  pe_ratio: number | null;
  total_market_cap: number | null;
  circulating_market_cap: number | null;
  bid_price: number | null;
  ask_price: number | null;
  limit_up: boolean;
  limit_down: boolean;
  data_status: DataStatus;
  exchange: string;
  stock_type: string;
}

export interface CapitalFlow {
  symbol: string;
  main_net_inflow: number;
  super_large_inflow: number;
  super_large_outflow: number;
  large_inflow: number;
  large_outflow: number;
  medium_inflow: number;
  medium_outflow: number;
  small_inflow: number;
  small_outflow: number;
  main_net_inflow_fmt: string;
  data_status: DataStatus;
}

export interface MinuteData {
  symbol: string;
  times: string[];
  prices: number[];
  volumes: number[];
  avg_prices: number[];
  data_status: DataStatus;
}

export interface TechnicalSignals {
  symbol: string;
  above_ma5: boolean;
  above_ma10: boolean;
  above_ma20: boolean;
  above_ma60: boolean;
  golden_cross: boolean;
  death_cross: boolean;
  volume_surge: boolean;
  volume_ratio: number;
  rsi_14: number;
  rsi_signal: 'overbought' | 'oversold' | 'neutral';
  price_breakout: boolean;
  near_support: boolean;
  macd: number;
  macd_signal: number;
  macd_hist: number;
  macd_golden_cross: boolean;
  bb_upper: number;
  bb_middle: number;
  bb_lower: number;
  bb_position: number;
  signal_score: number;
  signal_label: string;
}

export interface StockScore {
  symbol: string;
  name: string;
  technical_score: number;
  capital_flow_score: number;
  composite_score: number;
  grade: string;
  recommendation: string;
  risk_level: string;
  risk_warnings: string[];
}

export interface FullAnalysis {
  quote: Quote | null;
  capital_flow: CapitalFlow | null;
  minute_data: MinuteData | null;
  technical: TechnicalSignals | null;
  score: StockScore | null;
  is_fallback: boolean;
  fallback_message: string | null;
}

export interface Sector {
  name: string;
  change_pct: number;
  leading_stock: string;
  leading_stock_change: number;
  net_inflow: number;
  net_inflow_fmt: string;
}

export interface SectorRanking {
  sectors: Sector[];
  top_inflow: Sector[];
  rotation_strength: number;
  data_status: DataStatus;
}

export interface LimitStock {
  symbol: string;
  name: string;
  price: number;
  change_pct: number;
  volume: number;
  amount: number;
  continuous_count: number;
  exchange: string;
}

export interface LimitUpPool {
  stocks: LimitStock[];
  count: number;
  data_status: DataStatus;
}

export interface Northbound {
  date: string;
  sh_net_inflow: number;
  sz_net_inflow: number;
  total_net_inflow: number;
  sh_buy: number;
  sh_sell: number;
  sz_buy: number;
  sz_sell: number;
  total_net_inflow_fmt: string;
  data_status: DataStatus;
}

export interface Sentiment {
  date: string;
  limit_up_count: number;
  limit_down_count: number;
  continuous_limit_up_max: number;
  sentiment_score: number;
  sentiment_label: string;
  up_count: number;
  down_count: number;
  flat_count: number;
  market_breadth: number;
  market_status: string;
  market_status_label: string;
}

export interface MarketOverview {
  sectors: SectorRanking;
  limit_up_pool: LimitUpPool;
  northbound: Northbound | null;
  sentiment: Sentiment;
  provider_status: {
    providers: Record<string, string>;
    last_updated: string;
  };
}

export interface HistoryBar {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  amount: number;
  change_pct: number;
}

export interface HistoryData {
  symbol: string;
  period: string;
  count: number;
  data: HistoryBar[];
}

// WebSocket message types
export type WsMessage =
  | { type: 'quote'; symbol: string; data: Quote; timestamp: string }
  | { type: 'market_pulse'; status: string; timestamp: string }
  | { type: 'subscribed'; symbols: string[] }
  | { type: 'interval_set'; interval: number }
  | { type: 'pong'; timestamp: string }
  | { type: 'error'; message: string };
