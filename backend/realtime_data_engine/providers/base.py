"""
Base provider interface for all data sources.
All providers must implement this interface.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional


class DataFreshness(str, Enum):
    REALTIME = "realtime"          # < 3 seconds old
    NEAR_REALTIME = "near_realtime"  # 3–30 seconds
    DELAYED = "delayed"            # 30s – 15 min
    STALE = "stale"               # > 15 min
    UNKNOWN = "unknown"


class ProviderStatus(str, Enum):
    OK = "ok"
    DEGRADED = "degraded"
    FAILED = "failed"


@dataclass
class QuoteData:
    symbol: str
    name: str
    price: float
    change: float             # absolute change
    change_pct: float         # percentage change
    volume: float             # shares
    amount: float             # turnover in yuan
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
    limit_up: bool = False     # 涨停
    limit_down: bool = False   # 跌停
    timestamp: datetime = field(default_factory=datetime.now)
    source: str = "unknown"
    freshness: DataFreshness = DataFreshness.UNKNOWN


@dataclass
class CapitalFlowData:
    symbol: str
    main_net_inflow: float         # 主力净流入
    super_large_inflow: float      # 超大单流入
    super_large_outflow: float     # 超大单流出
    large_inflow: float            # 大单流入
    large_outflow: float           # 大单流出
    medium_inflow: float           # 中单流入
    medium_outflow: float          # 中单流出
    small_inflow: float            # 小单流入
    small_outflow: float           # 小单流出
    timestamp: datetime = field(default_factory=datetime.now)
    source: str = "unknown"


@dataclass
class SectorData:
    name: str
    change_pct: float
    leading_stock: str = ""
    leading_stock_change: float = 0.0
    up_count: int = 0
    down_count: int = 0
    net_inflow: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class MinuteData:
    symbol: str
    times: List[str]
    prices: List[float]
    volumes: List[float]
    avg_prices: List[float]
    timestamp: datetime = field(default_factory=datetime.now)
    source: str = "unknown"


@dataclass
class NorthboundData:
    date: str
    sh_net_inflow: float    # Shanghai connect net inflow
    sz_net_inflow: float    # Shenzhen connect net inflow
    total_net_inflow: float
    sh_buy: float
    sh_sell: float
    sz_buy: float
    sz_sell: float
    timestamp: datetime = field(default_factory=datetime.now)


class BaseProvider(ABC):
    name: str = "base"
    priority: int = 99  # lower = higher priority

    @abstractmethod
    async def get_realtime_quote(self, symbol: str) -> Optional[QuoteData]:
        pass

    @abstractmethod
    async def get_batch_quotes(self, symbols: List[str]) -> List[QuoteData]:
        pass

    async def get_minute_data(self, symbol: str) -> Optional[MinuteData]:
        return None

    async def get_capital_flow(self, symbol: str) -> Optional[CapitalFlowData]:
        return None

    async def get_sector_data(self) -> List[SectorData]:
        return []

    async def get_limit_up_stocks(self) -> List[QuoteData]:
        return []

    async def get_northbound_flow(self) -> Optional[NorthboundData]:
        return None

    async def health_check(self) -> ProviderStatus:
        return ProviderStatus.DEGRADED

    def _compute_freshness(self, ts: datetime) -> DataFreshness:
        age = (datetime.now() - ts).total_seconds()
        if age < 3:
            return DataFreshness.REALTIME
        elif age < 30:
            return DataFreshness.NEAR_REALTIME
        elif age < 900:
            return DataFreshness.DELAYED
        else:
            return DataFreshness.STALE
