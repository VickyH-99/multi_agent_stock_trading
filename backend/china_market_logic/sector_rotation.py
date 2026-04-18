"""
Sector rotation analysis (板块轮动分析).
Identifies hot sectors and rotation patterns.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from realtime_data_engine.providers.base import SectorData


@dataclass
class SectorRotationSignal:
    top_sectors: List[Dict]       # Top gaining sectors
    bottom_sectors: List[Dict]    # Worst performing sectors
    hot_money_sectors: List[Dict] # Sectors with high capital inflow
    rotation_strength: float      # 0-1 how strong the rotation is
    timestamp: datetime = field(default_factory=datetime.now)


def analyze_sector_rotation(sectors: List[SectorData]) -> SectorRotationSignal:
    """Analyze sector rotation from current sector data."""
    if not sectors:
        return SectorRotationSignal(
            top_sectors=[], bottom_sectors=[],
            hot_money_sectors=[], rotation_strength=0.0
        )

    # Sort by change
    sorted_by_change = sorted(sectors, key=lambda s: s.change_pct, reverse=True)
    sorted_by_inflow = sorted(sectors, key=lambda s: s.net_inflow, reverse=True)

    top = [
        {
            "name": s.name,
            "change_pct": s.change_pct,
            "leading_stock": s.leading_stock,
            "leading_change": s.leading_stock_change,
            "net_inflow": s.net_inflow,
        }
        for s in sorted_by_change[:10]
    ]

    bottom = [
        {
            "name": s.name,
            "change_pct": s.change_pct,
            "net_inflow": s.net_inflow,
        }
        for s in sorted_by_change[-5:]
    ]

    hot_money = [
        {
            "name": s.name,
            "net_inflow": s.net_inflow,
            "change_pct": s.change_pct,
        }
        for s in sorted_by_inflow[:10]
        if s.net_inflow > 0
    ]

    # Rotation strength = variance in sector returns
    if len(sectors) > 1:
        changes = [s.change_pct for s in sectors]
        avg = sum(changes) / len(changes)
        variance = sum((x - avg) ** 2 for x in changes) / len(changes)
        strength = min(variance / 25.0, 1.0)  # normalize, 5% std dev = full strength
    else:
        strength = 0.0

    return SectorRotationSignal(
        top_sectors=top,
        bottom_sectors=bottom,
        hot_money_sectors=hot_money,
        rotation_strength=round(strength, 3),
        timestamp=datetime.now(),
    )
