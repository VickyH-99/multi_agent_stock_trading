"""
Composite stock scoring system.
Combines technical, capital flow, and sentiment signals into a final score.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from indicators.technical import TechnicalSignals
from indicators.capital_flow_signals import CapitalFlowSignal


@dataclass
class StockScore:
    symbol: str
    name: str

    technical_score: float = 0.0      # -100 to +100
    capital_flow_score: float = 0.0   # -100 to +100
    composite_score: float = 0.0      # Final weighted score

    grade: str = "C"                  # A+/A/B+/B/C/D/F
    recommendation: str = "观望"     # 强烈买入/买入/观望/减仓/出局

    risk_level: str = "medium"        # low/medium/high/extreme
    risk_warnings: list = field(default_factory=list)

    timestamp: datetime = field(default_factory=datetime.now)


def score_stock(
    symbol: str,
    name: str,
    tech: Optional[TechnicalSignals],
    flow: Optional[CapitalFlowSignal],
    change_pct: float = 0.0,
    limit_up: bool = False,
    limit_down: bool = False,
) -> StockScore:
    """Generate a composite score for a stock."""

    tech_score = tech.signal_score if tech else 0.0
    flow_score = flow.smart_money_score if flow else 0.0

    # Weights: technical 60%, capital flow 40%
    composite = tech_score * 0.6 + flow_score * 0.4

    # Adjust for limit signals
    if limit_up:
        composite = min(100, composite + 10)
    if limit_down:
        composite = max(-100, composite - 10)

    composite = round(composite, 1)

    # Grade
    if composite >= 75:   grade = "A+"
    elif composite >= 55: grade = "A"
    elif composite >= 35: grade = "B+"
    elif composite >= 15: grade = "B"
    elif composite >= -10: grade = "C"
    elif composite >= -35: grade = "D"
    else:                  grade = "F"

    # Recommendation
    if composite >= 60:    rec = "强烈买入"
    elif composite >= 30:  rec = "买入"
    elif composite >= -10: rec = "观望"
    elif composite >= -40: rec = "减仓"
    else:                  rec = "出局"

    # Risk level
    risk_warnings = []

    if tech:
        if tech.rsi_signal == "overbought":
            risk_warnings.append("RSI超买，注意回调风险")
        if tech.bb_position > 0.9:
            risk_warnings.append("价格触及布林带上轨")
        if not tech.volume_surge and tech.price_breakout:
            risk_warnings.append("突破无量，可靠性存疑")

    if limit_up:
        risk_warnings.append("涨停封板，次日开板风险")
    if limit_down:
        risk_warnings.append("跌停，注意连续下跌风险")

    if abs(change_pct) > 8:
        risk_warnings.append("当日大幅波动，注意仓位控制")

    if len(risk_warnings) >= 3:
        risk_level = "extreme"
    elif len(risk_warnings) >= 2:
        risk_level = "high"
    elif len(risk_warnings) >= 1:
        risk_level = "medium"
    else:
        risk_level = "low"

    return StockScore(
        symbol=symbol,
        name=name,
        technical_score=round(tech_score, 1),
        capital_flow_score=round(flow_score, 1),
        composite_score=composite,
        grade=grade,
        recommendation=rec,
        risk_level=risk_level,
        risk_warnings=risk_warnings,
        timestamp=datetime.now(),
    )
