"""
Eastmoney (东方财富) real-time data provider.
Uses public Eastmoney APIs for quotes, capital flow, sector data.
"""
import asyncio
import re
from datetime import datetime
from typing import Dict, List, Optional
from urllib.parse import urlencode

import httpx
from loguru import logger

from .base import (
    BaseProvider, CapitalFlowData, DataFreshness, MinuteData,
    NorthboundData, ProviderStatus, QuoteData, SectorData
)
from config import get_settings

settings = get_settings()

# Eastmoney field mapping for stock quotes
# secid format: 1. = SH, 0. = SZ
EM_FIELDS = (
    "f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f13,f14,f15,f16,f17,f18,"
    "f20,f21,f23,f62,f115,f152"
)


def _symbol_to_secid(symbol: str) -> str:
    """Convert 6-digit symbol to Eastmoney secid format."""
    if symbol.startswith("6"):
        return f"1.{symbol}"
    elif symbol.startswith(("0", "3")):
        return f"0.{symbol}"
    elif symbol.startswith("4") or symbol.startswith("8"):
        return f"0.{symbol}"  # Beijing exchange
    return f"1.{symbol}"


def _parse_em_quote(data: Dict, symbol: str) -> Optional[QuoteData]:
    """Parse Eastmoney quote API response."""
    try:
        f = data
        price = float(f.get("f2", 0)) / 100.0
        prev_close = float(f.get("f18", 0)) / 100.0
        if price <= 0 or prev_close <= 0:
            return None

        change_pct = float(f.get("f3", 0)) / 100.0
        change = float(f.get("f4", 0)) / 100.0
        volume = float(f.get("f5", 0)) * 100  # lots to shares
        amount = float(f.get("f6", 0))
        high = float(f.get("f15", 0)) / 100.0
        low = float(f.get("f16", 0)) / 100.0
        open_p = float(f.get("f17", 0)) / 100.0
        name = f.get("f14", symbol)
        turnover_rate = float(f.get("f8", 0)) / 100.0
        pe = float(f.get("f9", 0)) if f.get("f9") else None
        total_cap = float(f.get("f20", 0)) if f.get("f20") else None
        circ_cap = float(f.get("f21", 0)) if f.get("f21") else None

        # Limit up / down detection (China market ±10% or ±20% for STAR/ChiNext)
        limit_up = abs(change_pct - 10.0) < 0.15 or abs(change_pct - 20.0) < 0.15
        limit_down = abs(change_pct + 10.0) < 0.15 or abs(change_pct + 20.0) < 0.15

        return QuoteData(
            symbol=symbol,
            name=name,
            price=price,
            change=change,
            change_pct=change_pct,
            volume=volume,
            amount=amount,
            high=high,
            low=low,
            open_price=open_p,
            prev_close=prev_close,
            turnover_rate=turnover_rate,
            pe_ratio=pe,
            total_market_cap=total_cap,
            circulating_market_cap=circ_cap,
            limit_up=limit_up,
            limit_down=limit_down,
            timestamp=datetime.now(),
            source="eastmoney",
            freshness=DataFreshness.NEAR_REALTIME,
        )
    except Exception as e:
        logger.warning(f"[Eastmoney] Parse error for {symbol}: {e}")
        return None


class EastmoneyProvider(BaseProvider):
    name = "eastmoney"
    priority = 1

    def __init__(self):
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=settings.HTTP_TIMEOUT,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
                    ),
                    "Referer": "https://finance.eastmoney.com/",
                },
                follow_redirects=True,
            )
        return self._client

    async def get_realtime_quote(self, symbol: str) -> Optional[QuoteData]:
        secid = _symbol_to_secid(symbol)
        url = (
            "https://push2.eastmoney.com/api/qt/stock/get?"
            f"secid={secid}&fields={EM_FIELDS}&mpi=1000&ut=fa5fd1943c7b386f172d6893dbfba10b"
        )
        try:
            client = await self._get_client()
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()
            quote_data = data.get("data", {})
            if not quote_data:
                return None
            return _parse_em_quote(quote_data, symbol)
        except Exception as e:
            logger.warning(f"[Eastmoney] Quote fetch failed for {symbol}: {e}")
            return None

    async def get_batch_quotes(self, symbols: List[str]) -> List[QuoteData]:
        secids = ",".join(_symbol_to_secid(s) for s in symbols)
        url = (
            "https://push2.eastmoney.com/api/qt/ulist.np/get?"
            f"secids={secids}&fields={EM_FIELDS}&mpi=1000"
            "&ut=fa5fd1943c7b386f172d6893dbfba10b"
        )
        try:
            client = await self._get_client()
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()
            items = data.get("data", {}).get("diff", []) or []
            results = []
            for i, item in enumerate(items):
                if i < len(symbols):
                    q = _parse_em_quote(item, symbols[i])
                    if q:
                        results.append(q)
            return results
        except Exception as e:
            logger.warning(f"[Eastmoney] Batch quote failed: {e}")
            return []

    async def get_minute_data(self, symbol: str) -> Optional[MinuteData]:
        """Fetch intraday minute-level time series (分时图)."""
        secid = _symbol_to_secid(symbol)
        url = (
            "https://push2.eastmoney.com/api/qt/stock/trends2/get?"
            f"secid={secid}&fields1=f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f11"
            "&fields2=f51,f52,f53,f54,f55,f56,f57,f58"
            "&ut=fa5fd1943c7b386f172d6893dbfba10b&ndays=1"
        )
        try:
            client = await self._get_client()
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json().get("data", {})
            if not data:
                return None
            trends = data.get("trends", [])
            if not trends:
                return None

            times, prices, volumes, avg_prices = [], [], [], []
            for item in trends:
                parts = item.split(",")
                if len(parts) >= 7:
                    times.append(parts[0][-5:])  # HH:MM
                    prices.append(float(parts[2]))
                    volumes.append(float(parts[5]))
                    avg_prices.append(float(parts[7]) if len(parts) > 7 else float(parts[2]))

            return MinuteData(
                symbol=symbol,
                times=times,
                prices=prices,
                volumes=volumes,
                avg_prices=avg_prices,
                timestamp=datetime.now(),
                source="eastmoney",
            )
        except Exception as e:
            logger.warning(f"[Eastmoney] Minute data failed for {symbol}: {e}")
            return None

    async def get_capital_flow(self, symbol: str) -> Optional[CapitalFlowData]:
        """Fetch main capital flow data (主力资金流向)."""
        secid = _symbol_to_secid(symbol)
        url = (
            "https://push2.eastmoney.com/api/qt/stock/fflow/kline/get?"
            f"secid={secid}&fields1=f1,f2,f3,f7&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f62,f63"
            "&ut=fa5fd1943c7b386f172d6893dbfba10b&lmt=0&klt=1&fqt=1&beg=0&end=20500101"
        )
        # Use today's aggregated flow endpoint instead
        url2 = (
            "https://push2.eastmoney.com/api/qt/stock/fflow/get?"
            f"secid={secid}&fields=f62,f184,f66,f69,f72,f75,f78,f81,f84,f87,f64,f65,f70,f71,f76,f77,f82,f83"
            "&ut=fa5fd1943c7b386f172d6893dbfba10b"
        )
        try:
            client = await self._get_client()
            resp = await client.get(url2)
            resp.raise_for_status()
            data = resp.json().get("data", {})
            if not data:
                return None

            return CapitalFlowData(
                symbol=symbol,
                main_net_inflow=float(data.get("f62", 0) or 0),
                super_large_inflow=float(data.get("f66", 0) or 0),
                super_large_outflow=float(data.get("f69", 0) or 0),
                large_inflow=float(data.get("f72", 0) or 0),
                large_outflow=float(data.get("f75", 0) or 0),
                medium_inflow=float(data.get("f78", 0) or 0),
                medium_outflow=float(data.get("f81", 0) or 0),
                small_inflow=float(data.get("f84", 0) or 0),
                small_outflow=float(data.get("f87", 0) or 0),
                timestamp=datetime.now(),
                source="eastmoney",
            )
        except Exception as e:
            logger.warning(f"[Eastmoney] Capital flow failed for {symbol}: {e}")
            return None

    async def get_sector_data(self) -> List[SectorData]:
        """Fetch concept/sector board ranking (概念板块)."""
        url = (
            "https://push2.eastmoney.com/api/qt/clist/get?"
            "pn=1&pz=50&po=1&np=1"
            "&ut=fa5fd1943c7b386f172d6893dbfba10b"
            "&fltt=2&invt=2"
            "&fid=f3&fs=m:90+t:3"  # concept boards
            "&fields=f2,f3,f4,f8,f12,f14,f15,f16,f17,f18,f20,f21,f62,f115,f128,f136,f140,f141"
        )
        try:
            client = await self._get_client()
            resp = await client.get(url)
            resp.raise_for_status()
            items = resp.json().get("data", {}).get("diff", []) or []
            sectors = []
            for item in items:
                sectors.append(SectorData(
                    name=item.get("f14", ""),
                    change_pct=float(item.get("f3", 0)) / 100.0,
                    leading_stock=item.get("f128", ""),
                    leading_stock_change=float(item.get("f136", 0)) / 100.0,
                    net_inflow=float(item.get("f62", 0) or 0),
                    timestamp=datetime.now(),
                ))
            return sectors
        except Exception as e:
            logger.warning(f"[Eastmoney] Sector data failed: {e}")
            return []

    async def get_limit_up_stocks(self) -> List[QuoteData]:
        """Fetch real-time limit-up stocks (涨停股)."""
        url = (
            "https://push2ex.eastmoney.com/getTopicZTPool?"
            "ut=fa5fd1943c7b386f172d6893dbfba10b&dpt=wz.ztzt&Pageindex=0&pagesize=100"
            "&sort=fbt&asc=0&st=0&sr=-1"
        )
        try:
            client = await self._get_client()
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json().get("data", {})
            items = data.get("pool", []) if isinstance(data, dict) else []
            results = []
            for item in items:
                try:
                    price_raw = item.get("price") or item.get("p") or 0
                    price = float(price_raw) if price_raw else 0.0
                    change_pct = float(item.get("zdp") or item.get("pct_chg") or 10.0)
                    prev = price / (1 + change_pct / 100) if change_pct != -100 else price
                    results.append(QuoteData(
                        symbol=item.get("c", ""),
                        name=item.get("n", ""),
                        price=price,
                        change=price - prev,
                        change_pct=change_pct,
                        volume=float(item.get("vol") or 0),
                        amount=float(item.get("amount") or item.get("a") or 0),
                        high=price,
                        low=price,
                        open_price=float(item.get("o") or 0),
                        prev_close=prev,
                        limit_up=True,
                        timestamp=datetime.now(),
                        source="eastmoney",
                        freshness=DataFreshness.NEAR_REALTIME,
                    ))
                except Exception:
                    continue
            return results
        except Exception as e:
            logger.warning(f"[Eastmoney] Limit-up stocks failed: {e}")
            return []

    async def get_northbound_flow(self) -> Optional[NorthboundData]:
        """Fetch northbound capital flow (北向资金)."""
        url = (
            "https://push2.eastmoney.com/api/qt/kamt/get?"
            "fields1=f1,f2,f3,f4&fields2=f51,f52,f53,f54,f55,f56"
            "&ut=fa5fd1943c7b386f172d6893dbfba10b"
        )
        try:
            client = await self._get_client()
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json().get("data", {})
            if not data:
                return None

            sh = data.get("s2n", {}) or {}
            sz = data.get("s3n", {}) or {}
            sh_buy = float(sh.get("f64", 0) or 0)
            sh_sell = float(sh.get("f65", 0) or 0)
            sz_buy = float(sz.get("f64", 0) or 0)
            sz_sell = float(sz.get("f65", 0) or 0)

            return NorthboundData(
                date=datetime.now().strftime("%Y-%m-%d"),
                sh_net_inflow=sh_buy - sh_sell,
                sz_net_inflow=sz_buy - sz_sell,
                total_net_inflow=(sh_buy - sh_sell) + (sz_buy - sz_sell),
                sh_buy=sh_buy,
                sh_sell=sh_sell,
                sz_buy=sz_buy,
                sz_sell=sz_sell,
                timestamp=datetime.now(),
            )
        except Exception as e:
            logger.warning(f"[Eastmoney] Northbound flow failed: {e}")
            return None

    async def health_check(self) -> ProviderStatus:
        try:
            q = await self.get_realtime_quote("000001")
            return ProviderStatus.OK if q else ProviderStatus.DEGRADED
        except Exception:
            return ProviderStatus.FAILED
