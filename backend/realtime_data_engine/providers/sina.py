"""
Sina Finance (新浪财经) real-time quote provider.
Sina provides near-real-time quotes very quickly.
"""
import re
from datetime import datetime
from typing import List, Optional

import httpx
from loguru import logger

from .base import BaseProvider, DataFreshness, MinuteData, ProviderStatus, QuoteData
from config import get_settings

settings = get_settings()


def _symbol_to_sina(symbol: str) -> str:
    """Convert 6-digit symbol to Sina format (sh600000, sz000001)."""
    if symbol.startswith("6"):
        return f"sh{symbol}"
    elif symbol.startswith(("0", "3")):
        return f"sz{symbol}"
    elif symbol.startswith(("4", "8")):
        return f"bj{symbol}"
    return f"sh{symbol}"


def _parse_sina_quote(raw: str, symbol: str) -> Optional[QuoteData]:
    """Parse Sina quote string format."""
    # Format: var hq_str_sh600000="name,open,prev_close,price,high,low,...,time,date,..."
    try:
        match = re.search(r'"([^"]+)"', raw)
        if not match:
            return None
        content = match.group(1).strip()
        if not content or content == "0":
            return None

        parts = content.split(",")
        if len(parts) < 32:
            return None

        name = parts[0]
        open_p = float(parts[1])
        prev_close = float(parts[2])
        price = float(parts[3])
        high = float(parts[4])
        low = float(parts[5])
        # parts[6] = buy price, parts[7] = sell price
        volume = float(parts[8])     # shares
        amount = float(parts[9])     # yuan
        time_str = parts[31]         # HH:MM:SS
        date_str = parts[30]         # YYYY-MM-DD

        if price <= 0:
            return None

        change = price - prev_close
        change_pct = (change / prev_close * 100) if prev_close > 0 else 0.0

        # Parse timestamp
        try:
            ts = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
        except Exception:
            ts = datetime.now()

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
            bid_price=float(parts[6]) if parts[6] else None,
            ask_price=float(parts[7]) if parts[7] else None,
            limit_up=limit_up,
            limit_down=limit_down,
            timestamp=ts,
            source="sina",
            freshness=DataFreshness.NEAR_REALTIME,
        )
    except Exception as e:
        logger.debug(f"[Sina] Parse error for {symbol}: {e}")
        return None


class SinaProvider(BaseProvider):
    name = "sina"
    priority = 2

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
                    "Referer": "https://finance.sina.com.cn/",
                },
                follow_redirects=True,
            )
        return self._client

    async def get_realtime_quote(self, symbol: str) -> Optional[QuoteData]:
        sina_sym = _symbol_to_sina(symbol)
        url = f"https://hq.sinajs.cn/list={sina_sym}"
        try:
            client = await self._get_client()
            resp = await client.get(url)
            resp.raise_for_status()
            return _parse_sina_quote(resp.text, symbol)
        except Exception as e:
            logger.warning(f"[Sina] Quote fetch failed for {symbol}: {e}")
            return None

    async def get_batch_quotes(self, symbols: List[str]) -> List[QuoteData]:
        sina_syms = ",".join(_symbol_to_sina(s) for s in symbols)
        url = f"https://hq.sinajs.cn/list={sina_syms}"
        try:
            client = await self._get_client()
            resp = await client.get(url)
            resp.raise_for_status()
            lines = resp.text.strip().split("\n")
            results = []
            for i, line in enumerate(lines):
                if i < len(symbols) and line.strip():
                    q = _parse_sina_quote(line, symbols[i])
                    if q:
                        results.append(q)
            return results
        except Exception as e:
            logger.warning(f"[Sina] Batch quote failed: {e}")
            return []

    async def get_minute_data(self, symbol: str) -> Optional[MinuteData]:
        """Sina intraday chart data."""
        sina_sym = _symbol_to_sina(symbol)
        url = f"https://image.sinajs.cn/newchart/min/n/{sina_sym}.gif"
        # Use the data API instead
        url2 = f"https://finance.sina.com.cn/realstock/company/{sina_sym}/jsvar.js"
        try:
            client = await self._get_client()
            resp = await client.get(url2)
            resp.raise_for_status()
            # Parse the JS variable
            text = resp.text
            match = re.search(r'var\s+\w+\s*=\s*"([^"]+)"', text)
            if not match:
                return None
            # The format is complex — return minimal structure
            return None  # Fall through to AkShare for minute data
        except Exception:
            return None

    async def health_check(self) -> ProviderStatus:
        try:
            q = await self.get_realtime_quote("000001")
            return ProviderStatus.OK if q else ProviderStatus.DEGRADED
        except Exception:
            return ProviderStatus.FAILED
