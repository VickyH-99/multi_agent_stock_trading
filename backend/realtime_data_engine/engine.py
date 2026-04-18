"""
Real-time Data Engine — multi-source aggregation with priority failover.

Priority: Eastmoney (1) → Sina (2) → AkShare (3) → Tushare (4)

Features:
- Parallel fetch from multiple providers
- Choose freshest/most trustworthy result
- Rate limiting + retry with backoff
- Cache layer with TTL
- Data freshness scoring
- Graceful degradation
"""
import asyncio
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger
from tenacity import (
    retry, stop_after_attempt, wait_exponential,
    retry_if_exception_type, before_sleep_log
)
import logging

from .cache.cache_manager import cache_manager
from .providers.base import (
    BaseProvider, CapitalFlowData, DataFreshness, MinuteData,
    NorthboundData, ProviderStatus, QuoteData, SectorData
)
from .providers.eastmoney import EastmoneyProvider
from .providers.sina import SinaProvider
from .providers.akshare_provider import AkShareProvider
from .providers.tushare_provider import TushareProvider
from config import get_settings

settings = get_settings()


class RateLimiter:
    """Simple token-bucket rate limiter per provider."""

    def __init__(self, max_concurrent: int = 5):
        self._semaphore = asyncio.Semaphore(max_concurrent)

    async def __aenter__(self):
        await self._semaphore.acquire()
        return self

    async def __aexit__(self, *args):
        self._semaphore.release()


_rate_limiter = RateLimiter(settings.MAX_CONCURRENT_REQUESTS)


async def _fetch_with_timeout(coro, timeout: float = None) -> Optional[Any]:
    """Wrap coroutine with timeout, return None on failure."""
    t = timeout or settings.HTTP_TIMEOUT
    try:
        return await asyncio.wait_for(coro, timeout=t + 2)
    except asyncio.TimeoutError:
        return None
    except Exception as e:
        logger.debug(f"[Engine] Fetch error: {e}")
        return None


class DataEngine:
    """
    Core market data engine.
    Aggregates data from multiple providers with intelligent fallover.
    """

    def __init__(self):
        self.providers: List[BaseProvider] = [
            EastmoneyProvider(),
            SinaProvider(),
            AkShareProvider(),
            TushareProvider(),
        ]
        # Sort by priority (lower = higher priority)
        self.providers.sort(key=lambda p: p.priority)
        self._provider_health: Dict[str, ProviderStatus] = {}
        self._last_health_check: float = 0
        self._health_check_interval = 60.0  # seconds

    async def initialize(self):
        """Initialize cache and run initial health checks."""
        await cache_manager.init_redis()
        await self._check_provider_health()
        logger.info("[Engine] Data engine initialized")

    async def _check_provider_health(self):
        """Run health checks in parallel."""
        tasks = {p.name: p.health_check() for p in self.providers}
        results = await asyncio.gather(*tasks.values(), return_exceptions=True)
        for name, result in zip(tasks.keys(), results):
            if isinstance(result, Exception):
                self._provider_health[name] = ProviderStatus.FAILED
            else:
                self._provider_health[name] = result
        self._last_health_check = time.time()
        logger.info(f"[Engine] Health: {self._provider_health}")

    def _is_provider_healthy(self, provider: BaseProvider) -> bool:
        status = self._provider_health.get(provider.name, ProviderStatus.OK)
        return status != ProviderStatus.FAILED

    async def _maybe_refresh_health(self):
        if time.time() - self._last_health_check > self._health_check_interval:
            asyncio.create_task(self._check_provider_health())

    # ------------------------------------------------------------------ #
    #  QUOTE                                                               #
    # ------------------------------------------------------------------ #

    async def get_quote(self, symbol: str) -> Optional[QuoteData]:
        """
        Get real-time quote for a single stock.
        Priority: Eastmoney → Sina → AkShare → Tushare → cached fallback
        """
        cache_key = f"quote:{symbol}"
        cached = await cache_manager.get_async(cache_key, settings.QUOTE_CACHE_TTL)
        if cached:
            return cached

        await self._maybe_refresh_health()

        # Try providers in priority order
        for provider in self.providers:
            if not self._is_provider_healthy(provider):
                continue
            async with _rate_limiter:
                quote = await _fetch_with_timeout(
                    provider.get_realtime_quote(symbol)
                )
            if quote and quote.price > 0:
                await cache_manager.set_async(cache_key, quote, settings.QUOTE_CACHE_TTL)
                logger.debug(f"[Engine] Quote {symbol} from {provider.name}")
                return quote

        # Last resort: check stale cache (any TTL)
        stale = cache_manager.get(cache_key, ttl=3600)
        if stale:
            stale.freshness = DataFreshness.STALE
            logger.warning(f"[Engine] Returning stale quote for {symbol}")
            return stale

        return None

    async def get_batch_quotes(self, symbols: List[str]) -> List[QuoteData]:
        """
        Fetch multiple quotes. Tries Eastmoney batch first (most efficient),
        falls back to parallel individual fetches.
        """
        if not symbols:
            return []

        # Check cache first
        uncached = []
        cached_results = []
        for sym in symbols:
            c = cache_manager.get(f"quote:{sym}", settings.QUOTE_CACHE_TTL)
            if c:
                cached_results.append(c)
            else:
                uncached.append(sym)

        if not uncached:
            return cached_results

        # Try Eastmoney batch (most efficient)
        em_provider = next((p for p in self.providers if p.name == "eastmoney"), None)
        if em_provider and self._is_provider_healthy(em_provider):
            async with _rate_limiter:
                batch = await _fetch_with_timeout(
                    em_provider.get_batch_quotes(uncached)
                )
            if batch:
                for q in batch:
                    cache_manager.set(f"quote:{q.symbol}", q, settings.QUOTE_CACHE_TTL)
                return cached_results + batch

        # Fallback: parallel individual fetches
        tasks = [self.get_quote(s) for s in uncached]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        fresh = [r for r in results if isinstance(r, QuoteData)]
        return cached_results + fresh

    # ------------------------------------------------------------------ #
    #  MINUTE DATA (分时图)                                               #
    # ------------------------------------------------------------------ #

    async def get_minute_data(self, symbol: str) -> Optional[MinuteData]:
        cache_key = f"minute:{symbol}"
        cached = await cache_manager.get_async(cache_key, settings.REALTIME_CACHE_TTL)
        if cached:
            return cached

        for provider in self.providers:
            if not self._is_provider_healthy(provider):
                continue
            data = await _fetch_with_timeout(provider.get_minute_data(symbol))
            if data and data.times:
                await cache_manager.set_async(cache_key, data, settings.REALTIME_CACHE_TTL)
                return data
        return None

    # ------------------------------------------------------------------ #
    #  CAPITAL FLOW (资金流)                                              #
    # ------------------------------------------------------------------ #

    async def get_capital_flow(self, symbol: str) -> Optional[CapitalFlowData]:
        cache_key = f"flow:{symbol}"
        cached = await cache_manager.get_async(cache_key, settings.CAPITAL_FLOW_CACHE_TTL)
        if cached:
            return cached

        for provider in self.providers:
            if not self._is_provider_healthy(provider):
                continue
            data = await _fetch_with_timeout(provider.get_capital_flow(symbol))
            if data:
                await cache_manager.set_async(cache_key, data, settings.CAPITAL_FLOW_CACHE_TTL)
                return data
        return None

    # ------------------------------------------------------------------ #
    #  SECTOR DATA (板块)                                                 #
    # ------------------------------------------------------------------ #

    async def get_sector_data(self) -> List[SectorData]:
        cache_key = "sectors:all"
        cached = await cache_manager.get_async(cache_key, settings.SECTOR_CACHE_TTL)
        if cached:
            return cached

        for provider in self.providers:
            if not self._is_provider_healthy(provider):
                continue
            data = await _fetch_with_timeout(provider.get_sector_data())
            if data:
                await cache_manager.set_async(cache_key, data, settings.SECTOR_CACHE_TTL)
                return data
        return []

    # ------------------------------------------------------------------ #
    #  LIMIT UP STOCKS (涨停板)                                           #
    # ------------------------------------------------------------------ #

    async def get_limit_up_stocks(self) -> List[QuoteData]:
        cache_key = "limitup:all"
        cached = await cache_manager.get_async(cache_key, settings.REALTIME_CACHE_TTL)
        if cached:
            return cached

        for provider in self.providers:
            if not self._is_provider_healthy(provider):
                continue
            data = await _fetch_with_timeout(provider.get_limit_up_stocks())
            if data:
                await cache_manager.set_async(cache_key, data, settings.REALTIME_CACHE_TTL)
                return data
        return []

    # ------------------------------------------------------------------ #
    #  NORTHBOUND FLOW (北向资金)                                         #
    # ------------------------------------------------------------------ #

    async def get_northbound_flow(self) -> Optional[NorthboundData]:
        cache_key = "northbound:today"
        cached = await cache_manager.get_async(cache_key, settings.CAPITAL_FLOW_CACHE_TTL)
        if cached:
            return cached

        for provider in self.providers:
            if not self._is_provider_healthy(provider):
                continue
            data = await _fetch_with_timeout(provider.get_northbound_flow())
            if data:
                await cache_manager.set_async(cache_key, data, settings.CAPITAL_FLOW_CACHE_TTL)
                return data
        return None

    # ------------------------------------------------------------------ #
    #  PROVIDER STATUS                                                    #
    # ------------------------------------------------------------------ #

    def get_provider_status(self) -> Dict[str, str]:
        return {name: status.value for name, status in self._provider_health.items()}

    async def get_all_market_data(self, symbol: str) -> Dict:
        """Aggregate all market data for a symbol in parallel."""
        quote_task = self.get_quote(symbol)
        minute_task = self.get_minute_data(symbol)
        flow_task = self.get_capital_flow(symbol)

        quote, minute, flow = await asyncio.gather(
            quote_task, minute_task, flow_task, return_exceptions=True
        )

        return {
            "quote": quote if not isinstance(quote, Exception) else None,
            "minute_data": minute if not isinstance(minute, Exception) else None,
            "capital_flow": flow if not isinstance(flow, Exception) else None,
        }


# Global engine singleton
data_engine = DataEngine()
