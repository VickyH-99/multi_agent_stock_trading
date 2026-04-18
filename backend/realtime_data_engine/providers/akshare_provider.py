"""
AkShare provider — comprehensive backbone for China A-share data.
AkShare integrates many sources: Eastmoney, Sina, Tencent, Wind, etc.
It's used for historical data, fundamentals, sector data, and as a robust fallback.
"""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import List, Optional

from loguru import logger

from akshare_runtime import run_akshare_in_executor
from .base import (
    BaseProvider, CapitalFlowData, DataFreshness, MinuteData,
    NorthboundData, ProviderStatus, QuoteData, SectorData
)

# AkShare is synchronous — we run it in a thread pool
_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="akshare")


async def _run_sync(func, *args):
    """Run a synchronous function in a thread pool."""
    return await run_akshare_in_executor(func, *args, executor=_executor)


def _safe_float(value) -> float:
    try:
        return float(value) if value is not None else 0.0
    except Exception:
        return 0.0


def _split_net_flow(value: float) -> tuple[float, float]:
    amount = _safe_float(value)
    if amount >= 0:
        return amount, 0.0
    return 0.0, abs(amount)


class AkShareProvider(BaseProvider):
    name = "akshare"
    priority = 3

    def __init__(self):
        self._ak = None
        self._import_failed = False

    def _get_ak(self):
        if self._ak is None and not self._import_failed:
            try:
                import akshare as ak
                self._ak = ak
            except ImportError:
                logger.error("[AkShare] akshare not installed! Run: pip install akshare")
                self._import_failed = True
        return self._ak

    def _fetch_spot_quote(self, symbol: str):
        ak = self._get_ak()
        if not ak:
            return None
        try:
            # stock_zh_a_spot_em fetches all A-share spots from Eastmoney via akshare
            # This is heavy — use for single stock only via specific API
            df = ak.stock_bid_ask_em(symbol=symbol)
            return df
        except Exception as e:
            logger.debug(f"[AkShare] spot quote {symbol}: {e}")
            return None

    def _fetch_realtime_quote(self, symbol: str):
        ak = self._get_ak()
        if not ak:
            return None
        try:
            # Use stock_zh_a_hist_min_em for intraday, or spot
            df = ak.stock_intraday_em(symbol=symbol)
            return df
        except Exception as e:
            logger.debug(f"[AkShare] intraday {symbol}: {e}")
            return None

    def _fetch_minute_em(self, symbol: str):
        ak = self._get_ak()
        if not ak:
            return None
        try:
            df = ak.stock_zh_a_hist_min_em(
                symbol=symbol, period="1", start_date="today", adjust=""
            )
            return df
        except Exception as e:
            logger.debug(f"[AkShare] minute {symbol}: {e}")
            return None

    def _fetch_capital_flow(self, symbol: str):
        ak = self._get_ak()
        if not ak:
            return None
        try:
            df = ak.stock_individual_fund_flow(stock=symbol, market="sh" if symbol.startswith("6") else "sz")
            return df
        except Exception as e:
            logger.debug(f"[AkShare] capital flow {symbol}: {e}")
            return None

    def _fetch_sector_boards(self):
        ak = self._get_ak()
        if not ak:
            return None
        try:
            df = ak.stock_board_concept_name_em()
            return df
        except Exception as e:
            logger.debug(f"[AkShare] sector boards: {e}")
            return None

    def _fetch_limit_up(self):
        ak = self._get_ak()
        if not ak:
            return None
        try:
            df = ak.stock_zt_pool_em(date=datetime.now().strftime("%Y%m%d"))
            return df
        except Exception as e:
            logger.debug(f"[AkShare] limit up: {e}")
            return None

    def _fetch_northbound(self):
        ak = self._get_ak()
        if not ak:
            return None
        try:
            df = ak.stock_em_hsgt_north_net_flow_in(symbol="北向资金")
            return df
        except Exception as e:
            logger.debug(f"[AkShare] northbound: {e}")
            return None

    async def get_realtime_quote(self, symbol: str) -> Optional[QuoteData]:
        try:
            df = await _run_sync(self._fetch_realtime_quote, symbol)
            if df is None or df.empty:
                return None
            last = df.iloc[-1]
            price = float(last.get("成交价", last.get("price", 0)))
            if price <= 0:
                return None

            return QuoteData(
                symbol=symbol,
                name=symbol,
                price=price,
                change=0.0,
                change_pct=0.0,
                volume=float(last.get("成交量", last.get("volume", 0))),
                amount=float(last.get("成交额", last.get("amount", 0))),
                high=price,
                low=price,
                open_price=price,
                prev_close=price,
                timestamp=datetime.now(),
                source="akshare",
                freshness=DataFreshness.NEAR_REALTIME,
            )
        except Exception as e:
            logger.warning(f"[AkShare] Quote failed for {symbol}: {e}")
            return None

    async def get_batch_quotes(self, symbols: List[str]) -> List[QuoteData]:
        """AkShare batch via all A-shares spot (heavy, used as fallback)."""
        results = []
        tasks = [self.get_realtime_quote(s) for s in symbols]
        quotes = await asyncio.gather(*tasks, return_exceptions=True)
        for q in quotes:
            if isinstance(q, QuoteData):
                results.append(q)
        return results

    async def get_minute_data(self, symbol: str) -> Optional[MinuteData]:
        try:
            df = await _run_sync(self._fetch_minute_em, symbol)
            if df is None or df.empty:
                return None

            times, prices, volumes, avg_prices = [], [], [], []
            for _, row in df.iterrows():
                t = str(row.get("时间", row.get("time", "")))
                if " " in t:
                    t = t.split(" ")[1][:5]
                times.append(t)
                prices.append(float(row.get("收盘", row.get("close", 0))))
                volumes.append(float(row.get("成交量", row.get("volume", 0))))
                avg_prices.append(float(row.get("均价", row.get("avg", prices[-1]))))

            return MinuteData(
                symbol=symbol,
                times=times,
                prices=prices,
                volumes=volumes,
                avg_prices=avg_prices,
                timestamp=datetime.now(),
                source="akshare",
            )
        except Exception as e:
            logger.warning(f"[AkShare] Minute data failed for {symbol}: {e}")
            return None

    async def get_capital_flow(self, symbol: str) -> Optional[CapitalFlowData]:
        try:
            df = await _run_sync(self._fetch_capital_flow, symbol)
            if df is None or df.empty:
                return None
            last = df.iloc[-1]
            main_net = _safe_float(
                last.get("主力净流入-净额", last.get("主力净流入", last.get("今日主力净流入", 0)))
            )
            super_large_net = _safe_float(last.get("超大单净流入-净额", last.get("超大单净流入", 0)))
            large_net = _safe_float(last.get("大单净流入-净额", last.get("大单净流入", 0)))
            medium_net = _safe_float(last.get("中单净流入-净额", last.get("中单净流入", 0)))
            small_net = _safe_float(last.get("小单净流入-净额", last.get("小单净流入", 0)))
            super_large_inflow, super_large_outflow = _split_net_flow(super_large_net)
            large_inflow, large_outflow = _split_net_flow(large_net)
            medium_inflow, medium_outflow = _split_net_flow(medium_net)
            small_inflow, small_outflow = _split_net_flow(small_net)

            return CapitalFlowData(
                symbol=symbol,
                main_net_inflow=main_net,
                super_large_inflow=super_large_inflow,
                super_large_outflow=super_large_outflow,
                large_inflow=large_inflow,
                large_outflow=large_outflow,
                medium_inflow=medium_inflow,
                medium_outflow=medium_outflow,
                small_inflow=small_inflow,
                small_outflow=small_outflow,
                timestamp=datetime.now(),
                source="akshare",
            )
        except Exception as e:
            logger.warning(f"[AkShare] Capital flow failed for {symbol}: {e}")
            return None

    async def get_sector_data(self) -> List[SectorData]:
        try:
            df = await _run_sync(self._fetch_sector_boards)
            if df is None or df.empty:
                return []
            results = []
            for _, row in df.head(30).iterrows():
                results.append(SectorData(
                    name=str(row.get("板块名称", row.get("name", ""))),
                    change_pct=float(row.get("涨跌幅", row.get("change_pct", 0)) or 0),
                    leading_stock=str(row.get("领涨股票", "")),
                    timestamp=datetime.now(),
                ))
            return results
        except Exception as e:
            logger.warning(f"[AkShare] Sector data failed: {e}")
            return []

    async def get_limit_up_stocks(self) -> List[QuoteData]:
        try:
            df = await _run_sync(self._fetch_limit_up)
            if df is None or df.empty:
                return []
            results = []
            for _, row in df.iterrows():
                try:
                    price = float(row.get("最新价", row.get("price", 0)) or 0)
                    change_pct = float(row.get("涨跌幅", 10.0) or 10.0)
                    prev = price / (1 + change_pct / 100) if change_pct > -100 else price
                    results.append(QuoteData(
                        symbol=str(row.get("代码", "")),
                        name=str(row.get("名称", "")),
                        price=price,
                        change=price - prev,
                        change_pct=change_pct,
                        volume=float(row.get("成交量", 0) or 0),
                        amount=float(row.get("成交额", 0) or 0),
                        high=price,
                        low=price,
                        open_price=price * 0.9,
                        prev_close=prev,
                        limit_up=True,
                        timestamp=datetime.now(),
                        source="akshare",
                        freshness=DataFreshness.NEAR_REALTIME,
                    ))
                except Exception:
                    continue
            return results
        except Exception as e:
            logger.warning(f"[AkShare] Limit-up failed: {e}")
            return []

    async def health_check(self) -> ProviderStatus:
        ak = self._get_ak()
        if ak is None:
            return ProviderStatus.FAILED
        return ProviderStatus.OK
