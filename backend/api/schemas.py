"""
Pydantic response schemas for all API endpoints.
"""
from dataclasses import asdict
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class DataStatusSchema(BaseModel):
    freshness: str
    source: str
    timestamp: str
    label: str   # 🟢 实时 / 🟡 延迟 / 🔴 数据异常
    is_live: bool


class QuoteSchema(BaseModel):
    symbol: str
    name: str
    price: float
    change: float
    change_pct: float
    volume: float
    amount: float
    high: float
    low: float
    open_price: float
    prev_close: float
    turnover_rate: Optional[float] = None
    pe_ratio: Optional[float] = None
    total_market_cap: Optional[float] = None
    circulating_market_cap: Optional[float] = None
    bid_price: Optional[float] = None
    ask_price: Optional[float] = None
    limit_up: bool = False
    limit_down: bool = False
    data_status: DataStatusSchema
    exchange: str
    stock_type: str


class CapitalFlowSchema(BaseModel):
    symbol: str
    main_net_inflow: float
    super_large_inflow: float
    super_large_outflow: float
    large_inflow: float
    large_outflow: float
    medium_inflow: float
    medium_outflow: float
    small_inflow: float
    small_outflow: float
    main_net_inflow_fmt: str
    data_status: DataStatusSchema


class MinuteDataSchema(BaseModel):
    symbol: str
    times: List[str]
    prices: List[float]
    volumes: List[float]
    avg_prices: List[float]
    data_status: DataStatusSchema


class SectorSchema(BaseModel):
    name: str
    change_pct: float
    leading_stock: str
    leading_stock_change: float
    net_inflow: float
    net_inflow_fmt: str


class SectorRankingSchema(BaseModel):
    sectors: List[SectorSchema]
    top_inflow: List[SectorSchema]
    rotation_strength: float
    data_status: DataStatusSchema


class LimitStockSchema(BaseModel):
    symbol: str
    name: str
    price: float
    change_pct: float
    volume: float
    amount: float
    continuous_count: int = 1  # 连板数
    exchange: str


class LimitUpPoolSchema(BaseModel):
    stocks: List[LimitStockSchema]
    count: int
    data_status: DataStatusSchema


class NorthboundSchema(BaseModel):
    date: str
    sh_net_inflow: float
    sz_net_inflow: float
    total_net_inflow: float
    sh_buy: float
    sh_sell: float
    sz_buy: float
    sz_sell: float
    total_net_inflow_fmt: str
    data_status: DataStatusSchema


class SentimentSchema(BaseModel):
    date: str
    limit_up_count: int
    limit_down_count: int
    continuous_limit_up_max: int
    sentiment_score: float
    sentiment_label: str
    up_count: int
    down_count: int
    flat_count: int
    market_breadth: float
    market_status: str
    market_status_label: str


class TechnicalSignalsSchema(BaseModel):
    symbol: str
    above_ma5: bool
    above_ma10: bool
    above_ma20: bool
    above_ma60: bool
    golden_cross: bool
    death_cross: bool
    volume_surge: bool
    volume_ratio: float
    rsi_14: float
    rsi_signal: str
    price_breakout: bool
    near_support: bool
    macd: float
    macd_signal: float
    macd_hist: float
    macd_golden_cross: bool
    bb_upper: float
    bb_middle: float
    bb_lower: float
    bb_position: float
    signal_score: float
    signal_label: str


class StockScoreSchema(BaseModel):
    symbol: str
    name: str
    technical_score: float
    capital_flow_score: float
    composite_score: float
    grade: str
    recommendation: str
    risk_level: str
    risk_warnings: List[str]


class FullAnalysisSchema(BaseModel):
    quote: Optional[QuoteSchema] = None
    capital_flow: Optional[CapitalFlowSchema] = None
    minute_data: Optional[MinuteDataSchema] = None
    technical: Optional[TechnicalSignalsSchema] = None
    score: Optional[StockScoreSchema] = None
    is_fallback: bool = False
    fallback_message: Optional[str] = None


class ProviderStatusSchema(BaseModel):
    providers: Dict[str, str]
    last_updated: str


class MarketOverviewSchema(BaseModel):
    sectors: SectorRankingSchema
    limit_up_pool: LimitUpPoolSchema
    northbound: Optional[NorthboundSchema]
    sentiment: SentimentSchema
    provider_status: ProviderStatusSchema
