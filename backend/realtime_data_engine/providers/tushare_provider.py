"""
Tushare provider — fundamentals and financial data (free tier).
Requires a free token from https://tushare.pro
"""
import asyncio
from datetime import datetime
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor

from loguru import logger

from .base import BaseProvider, DataFreshness, ProviderStatus, QuoteData
from config import get_settings

settings = get_settings()
_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="tushare")


async def _run_sync(func, *args):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_executor, func, *args)


class TushareProvider(BaseProvider):
    name = "tushare"
    priority = 4  # Lower priority — used for fundamentals

    def __init__(self):
        self._pro = None
        self._initialized = False
        self._failed = False

    def _init(self):
        if self._initialized or self._failed:
            return
        token = settings.TUSHARE_TOKEN
        if not token:
            logger.info("[Tushare] No token configured, skipping")
            self._failed = True
            return
        try:
            import tushare as ts
            ts.set_token(token)
            self._pro = ts.pro_api()
            self._initialized = True
            logger.info("[Tushare] Initialized successfully")
        except ImportError:
            logger.warning("[Tushare] tushare not installed")
            self._failed = True
        except Exception as e:
            logger.warning(f"[Tushare] Init failed: {e}")
            self._failed = True

    def _fetch_daily(self, symbol: str):
        self._init()
        if not self._pro:
            return None
        try:
            ts_code = f"{symbol}.SH" if symbol.startswith("6") else f"{symbol}.SZ"
            df = self._pro.daily(ts_code=ts_code, limit=1)
            return df
        except Exception as e:
            logger.debug(f"[Tushare] daily {symbol}: {e}")
            return None

    def _fetch_basics(self, symbol: str):
        self._init()
        if not self._pro:
            return None
        try:
            ts_code = f"{symbol}.SH" if symbol.startswith("6") else f"{symbol}.SZ"
            df = self._pro.daily_basic(ts_code=ts_code, limit=1,
                                       fields="ts_code,trade_date,pe,pb,turnover_rate,circ_mv,total_mv")
            return df
        except Exception as e:
            logger.debug(f"[Tushare] basics {symbol}: {e}")
            return None

    async def get_realtime_quote(self, symbol: str) -> Optional[QuoteData]:
        """Tushare daily is T+1 — use as fundamentals supplement only."""
        try:
            df = await _run_sync(self._fetch_daily, symbol)
            if df is None or df.empty:
                return None
            row = df.iloc[0]
            price = float(row.get("close", 0))
            if price <= 0:
                return None
            prev = float(row.get("pre_close", price))
            change = price - prev
            change_pct = change / prev * 100 if prev > 0 else 0

            return QuoteData(
                symbol=symbol,
                name=symbol,
                price=price,
                change=change,
                change_pct=change_pct,
                volume=float(row.get("vol", 0)) * 100,
                amount=float(row.get("amount", 0)) * 1000,
                high=float(row.get("high", price)),
                low=float(row.get("low", price)),
                open_price=float(row.get("open", price)),
                prev_close=prev,
                timestamp=datetime.now(),
                source="tushare",
                freshness=DataFreshness.STALE,  # Always T+1
            )
        except Exception as e:
            logger.warning(f"[Tushare] Quote failed for {symbol}: {e}")
            return None

    async def get_batch_quotes(self, symbols: List[str]) -> List[QuoteData]:
        tasks = [self.get_realtime_quote(s) for s in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [r for r in results if isinstance(r, QuoteData)]

    async def health_check(self) -> ProviderStatus:
        self._init()
        if self._failed:
            return ProviderStatus.FAILED
        if self._initialized:
            return ProviderStatus.OK
        return ProviderStatus.DEGRADED
