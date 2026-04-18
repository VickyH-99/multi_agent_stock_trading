"""
Market sentiment engine.
Tracks 涨停家数, 跌停家数, 连板高度, 情绪周期.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

from loguru import logger


@dataclass
class MarketSentiment:
    date: str
    limit_up_count: int = 0           # 涨停家数
    limit_down_count: int = 0         # 跌停家数
    continuous_limit_up_max: int = 0  # 最高连板数
    continuous_limit_up_stocks: List[Dict] = field(default_factory=list)  # 连板股列表
    breaking_limit_up: int = 0        # 炸板家数
    sentiment_score: float = 0.0      # 0-100, higher = more bullish
    sentiment_label: str = "中性"     # 极度悲观/悲观/中性/偏多/极度乐观
    up_count: int = 0                 # 上涨家数
    down_count: int = 0               # 下跌家数
    flat_count: int = 0               # 平盘家数
    market_breadth: float = 0.0       # (up - down) / total
    timestamp: datetime = field(default_factory=datetime.now)


def compute_sentiment(
    limit_up_count: int,
    limit_down_count: int,
    up_count: int,
    down_count: int,
    flat_count: int,
    max_continuous: int,
) -> MarketSentiment:
    """Compute overall market sentiment score and label."""
    today = datetime.now().strftime("%Y-%m-%d")
    total = up_count + down_count + flat_count

    # Breadth
    breadth = (up_count - down_count) / total if total > 0 else 0

    # Sentiment score (0-100)
    score = 50.0  # Start neutral

    # Limit up/down ratio
    if limit_down_count > 0:
        zt_zd_ratio = limit_up_count / limit_down_count
    else:
        zt_zd_ratio = limit_up_count if limit_up_count > 0 else 1

    score += min(zt_zd_ratio * 3, 25)  # max +25 from ratio
    score += breadth * 20               # max +/-20 from breadth
    score += min(max_continuous * 2, 10)  # max +10 from streak height

    # Clamp
    score = max(0, min(100, score))

    # Label
    if score >= 80:
        label = "极度乐观"
    elif score >= 65:
        label = "偏多"
    elif score >= 45:
        label = "中性"
    elif score >= 30:
        label = "偏空"
    else:
        label = "极度悲观"

    return MarketSentiment(
        date=today,
        limit_up_count=limit_up_count,
        limit_down_count=limit_down_count,
        continuous_limit_up_max=max_continuous,
        sentiment_score=round(score, 1),
        sentiment_label=label,
        up_count=up_count,
        down_count=down_count,
        flat_count=flat_count,
        market_breadth=round(breadth, 3),
        timestamp=datetime.now(),
    )
