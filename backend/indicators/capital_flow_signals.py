"""
Capital flow signal analysis.
Detects smart money patterns from flow data.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from realtime_data_engine.providers.base import CapitalFlowData


@dataclass
class CapitalFlowSignal:
    symbol: str
    main_flow_label: str = "中性"      # 主力大幅流入/小幅流入/中性/小幅流出/大幅流出
    main_net_inflow: float = 0.0
    main_net_inflow_fmt: str = "0"
    smart_money_score: float = 0.0     # -100 to +100
    big_order_ratio: float = 0.0       # (super_large + large) / total
    signal: str = "neutral"            # bullish/bearish/neutral
    strength: str = "weak"             # strong/medium/weak
    timestamp: datetime = field(default_factory=datetime.now)


def analyze_capital_flow(flow: Optional[CapitalFlowData]) -> Optional[CapitalFlowSignal]:
    """Analyze capital flow data and generate trading signal."""
    if not flow:
        return None

    total_buy = (flow.super_large_inflow + flow.large_inflow +
                 flow.medium_inflow + flow.small_inflow)
    total_sell = (flow.super_large_outflow + flow.large_outflow +
                  flow.medium_outflow + flow.small_outflow)
    total_vol = total_buy + total_sell

    # Big order ratio
    big_orders = flow.super_large_inflow + flow.large_inflow
    big_order_ratio = big_orders / total_buy if total_buy > 0 else 0.5

    # Score based on main (super_large + large) net flow
    main_net = flow.main_net_inflow
    total_amount = total_vol if total_vol > 0 else 1

    # Normalize: net as % of total
    net_ratio = main_net / total_amount

    score = net_ratio * 100  # -100 to +100
    score = max(-100, min(100, score))

    # Label
    if main_net > 5e7:     label = "主力大幅流入"
    elif main_net > 1e7:   label = "主力小幅流入"
    elif main_net > -1e7:  label = "中性"
    elif main_net > -5e7:  label = "主力小幅流出"
    else:                  label = "主力大幅流出"

    signal = "bullish" if score > 20 else ("bearish" if score < -20 else "neutral")
    strength = "strong" if abs(score) > 60 else ("medium" if abs(score) > 30 else "weak")

    # Format main net inflow
    abs_v = abs(main_net)
    sign = "+" if main_net >= 0 else "-"
    if abs_v >= 1e8:
        fmt = f"{sign}{abs_v/1e8:.2f}亿"
    elif abs_v >= 1e4:
        fmt = f"{sign}{abs_v/1e4:.2f}万"
    else:
        fmt = f"{sign}{abs_v:.0f}"

    return CapitalFlowSignal(
        symbol=flow.symbol,
        main_flow_label=label,
        main_net_inflow=main_net,
        main_net_inflow_fmt=fmt,
        smart_money_score=round(score, 1),
        big_order_ratio=round(big_order_ratio, 3),
        signal=signal,
        strength=strength,
        timestamp=datetime.now(),
    )
