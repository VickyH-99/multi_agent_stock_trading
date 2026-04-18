"""
China market session logic.
Handles trading hours, market status, limit-up/down rules, etc.
"""
from datetime import datetime, time, date
from enum import Enum
from typing import Optional
import pytz

CHINA_TZ = pytz.timezone("Asia/Shanghai")

# Trading sessions
MORNING_OPEN = time(9, 30)
MORNING_CLOSE = time(11, 30)
AFTERNOON_OPEN = time(13, 0)
AFTERNOON_CLOSE = time(15, 0)
PRE_OPEN = time(9, 15)   # call auction start
POST_CLOSE = time(15, 30)  # after-hours data


class MarketStatus(str, Enum):
    PRE_OPEN = "pre_open"          # 集合竞价 9:15-9:25
    CALL_AUCTION = "call_auction"  # 竞价 9:25-9:30
    MORNING = "morning"            # 上午交易 9:30-11:30
    LUNCH = "lunch"                # 午盘休市 11:30-13:00
    AFTERNOON = "afternoon"        # 下午交易 13:00-15:00
    CLOSED = "closed"              # 收盘后
    WEEKEND = "weekend"            # 周末


def get_market_status(dt: Optional[datetime] = None) -> MarketStatus:
    """Return current Shanghai market status."""
    if dt is None:
        dt = datetime.now(CHINA_TZ)
    elif dt.tzinfo is None:
        dt = CHINA_TZ.localize(dt)

    # Weekend
    if dt.weekday() >= 5:
        return MarketStatus.WEEKEND

    t = dt.time()

    if time(9, 15) <= t < time(9, 25):
        return MarketStatus.PRE_OPEN
    elif time(9, 25) <= t < time(9, 30):
        return MarketStatus.CALL_AUCTION
    elif MORNING_OPEN <= t < MORNING_CLOSE:
        return MarketStatus.MORNING
    elif MORNING_CLOSE <= t < AFTERNOON_OPEN:
        return MarketStatus.LUNCH
    elif AFTERNOON_OPEN <= t <= AFTERNOON_CLOSE:
        return MarketStatus.AFTERNOON
    else:
        return MarketStatus.CLOSED


def is_trading_session(dt: Optional[datetime] = None) -> bool:
    status = get_market_status(dt)
    return status in (MarketStatus.MORNING, MarketStatus.AFTERNOON, MarketStatus.CALL_AUCTION)


def get_limit_pct(symbol: str) -> float:
    """
    Return the daily limit percentage for a stock.
    - STAR (科创板 688xxx): ±20%
    - ChiNext registered (创业板 registered reform): ±20%
    - Beijing Exchange (8xxxxx, 4xxxxx): ±30%
    - Normal: ±10%
    """
    if symbol.startswith("688"):
        return 20.0
    elif symbol.startswith("300") or symbol.startswith("301"):
        # ChiNext: ±20% since Aug 2020 for registered reform
        return 20.0
    elif symbol.startswith(("8", "4")):
        return 30.0
    elif symbol.startswith("689"):
        return 20.0
    return 10.0


def detect_limit_status(symbol: str, change_pct: float) -> dict:
    """Detect whether a stock is at limit-up or limit-down."""
    limit = get_limit_pct(symbol)
    tolerance = 0.15  # 0.15% tolerance for float rounding

    is_limit_up = change_pct >= (limit - tolerance)
    is_limit_down = change_pct <= -(limit - tolerance)

    return {
        "limit_up": is_limit_up,
        "limit_down": is_limit_down,
        "limit_pct": limit,
        "change_pct": change_pct,
    }


def format_large_number(value: float) -> str:
    """Format large numbers for Chinese financial display (万/亿)."""
    abs_val = abs(value)
    sign = "-" if value < 0 else ""
    if abs_val >= 1e8:
        return f"{sign}{abs_val/1e8:.2f}亿"
    elif abs_val >= 1e4:
        return f"{sign}{abs_val/1e4:.2f}万"
    else:
        return f"{sign}{abs_val:.0f}"


def get_exchange(symbol: str) -> str:
    """Get exchange name for a symbol."""
    if symbol.startswith("6"):
        return "SH"
    elif symbol.startswith(("0", "3")):
        return "SZ"
    elif symbol.startswith(("4", "8")):
        return "BJ"
    return "UNKNOWN"


def get_stock_type(symbol: str) -> str:
    """Return human-readable stock type."""
    if symbol.startswith("60"):
        return "沪市主板"
    elif symbol.startswith("688"):
        return "科创板"
    elif symbol.startswith("00"):
        return "深市主板"
    elif symbol.startswith("300") or symbol.startswith("301"):
        return "创业板"
    elif symbol.startswith("83") or symbol.startswith("87"):
        return "北交所"
    return "其他"
