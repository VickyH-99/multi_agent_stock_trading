"""
Technical analysis indicators for A-share stocks.
Uses the 'ta' library + custom implementations for China-specific signals.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import numpy as np


@dataclass
class TechnicalSignals:
    symbol: str

    # Price signals
    above_ma5: bool = False
    above_ma10: bool = False
    above_ma20: bool = False
    above_ma60: bool = False
    golden_cross: bool = False      # MA5 crosses above MA20
    death_cross: bool = False       # MA5 crosses below MA20

    # Volume signals
    volume_surge: bool = False       # Volume > 2× MA volume
    volume_ratio: float = 1.0        # Current vol / avg vol

    # Momentum
    rsi_14: float = 50.0
    rsi_signal: str = "neutral"      # overbought/oversold/neutral

    # Breakout
    price_breakout: bool = False     # Break above recent high
    near_support: bool = False       # Near key support level

    # MACD
    macd: float = 0.0
    macd_signal: float = 0.0
    macd_hist: float = 0.0
    macd_golden_cross: bool = False

    # Bollinger Bands
    bb_upper: float = 0.0
    bb_middle: float = 0.0
    bb_lower: float = 0.0
    bb_position: float = 0.5   # 0 = at lower, 1 = at upper

    # Overall signal
    signal_score: float = 0.0   # -100 to +100
    signal_label: str = "中性"

    timestamp: datetime = field(default_factory=datetime.now)


def _sma(prices: List[float], period: int) -> Optional[float]:
    if len(prices) < period:
        return None
    return float(np.mean(prices[-period:]))


def _ema(prices: List[float], period: int) -> List[float]:
    if len(prices) < period:
        return []
    result = []
    k = 2.0 / (period + 1)
    result.append(float(np.mean(prices[:period])))
    for p in prices[period:]:
        result.append(p * k + result[-1] * (1 - k))
    return result


def _rsi(prices: List[float], period: int = 14) -> Optional[float]:
    if len(prices) < period + 1:
        return None
    deltas = [prices[i+1] - prices[i] for i in range(len(prices)-1)]
    gains = [d if d > 0 else 0.0 for d in deltas]
    losses = [-d if d < 0 else 0.0 for d in deltas]

    avg_gain = float(np.mean(gains[-period:]))
    avg_loss = float(np.mean(losses[-period:]))

    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 2)


def _bollinger(prices: List[float], period: int = 20, k: float = 2.0) -> Tuple[float, float, float]:
    if len(prices) < period:
        p = prices[-1] if prices else 0
        return p * 1.05, p, p * 0.95
    segment = prices[-period:]
    middle = float(np.mean(segment))
    std = float(np.std(segment))
    return middle + k * std, middle, middle - k * std


def _macd(prices: List[float]) -> Tuple[float, float, float]:
    """Returns (MACD, Signal, Histogram)."""
    if len(prices) < 26:
        return 0.0, 0.0, 0.0
    ema12 = _ema(prices, 12)
    ema26 = _ema(prices, 26)
    if not ema12 or not ema26:
        return 0.0, 0.0, 0.0

    # Align lengths
    min_len = min(len(ema12), len(ema26))
    macd_line = [ema12[i + len(ema12) - min_len] - ema26[i + len(ema26) - min_len]
                 for i in range(min_len)]

    if len(macd_line) < 9:
        return macd_line[-1], macd_line[-1], 0.0

    signal_line = _ema(macd_line, 9)
    if not signal_line:
        return macd_line[-1], macd_line[-1], 0.0

    macd_val = macd_line[-1]
    sig_val = signal_line[-1]
    hist = macd_val - sig_val

    return round(macd_val, 4), round(sig_val, 4), round(hist, 4)


def compute_technical_signals(
    symbol: str,
    prices: List[float],
    volumes: List[float],
) -> TechnicalSignals:
    """Compute a full set of technical signals for a stock."""
    sig = TechnicalSignals(symbol=symbol)

    if len(prices) < 5:
        return sig

    current = prices[-1]

    # Moving averages
    ma5 = _sma(prices, 5)
    ma10 = _sma(prices, 10)
    ma20 = _sma(prices, 20)
    ma60 = _sma(prices, 60)

    if ma5:
        sig.above_ma5 = current > ma5
    if ma10:
        sig.above_ma10 = current > ma10
    if ma20:
        sig.above_ma20 = current > ma20
    if ma60:
        sig.above_ma60 = current > ma60

    # Golden/death cross (MA5 vs MA20)
    if len(prices) >= 21 and ma5 and ma20:
        prev_ma5 = _sma(prices[:-1], 5)
        prev_ma20 = _sma(prices[:-1], 20)
        if prev_ma5 and prev_ma20:
            sig.golden_cross = (prev_ma5 <= prev_ma20) and (ma5 > ma20)
            sig.death_cross = (prev_ma5 >= prev_ma20) and (ma5 < ma20)

    # Volume
    if len(volumes) >= 5:
        avg_vol = float(np.mean(volumes[-20:])) if len(volumes) >= 20 else float(np.mean(volumes))
        curr_vol = volumes[-1]
        sig.volume_ratio = round(curr_vol / avg_vol, 2) if avg_vol > 0 else 1.0
        sig.volume_surge = sig.volume_ratio >= 2.0

    # RSI
    rsi = _rsi(prices)
    if rsi is not None:
        sig.rsi_14 = rsi
        if rsi >= 70:
            sig.rsi_signal = "overbought"
        elif rsi <= 30:
            sig.rsi_signal = "oversold"
        else:
            sig.rsi_signal = "neutral"

    # Breakout: price > max of last 20 days (excluding today)
    if len(prices) >= 20:
        recent_high = max(prices[-21:-1])
        sig.price_breakout = current > recent_high
        recent_low = min(prices[-21:-1])
        sig.near_support = current <= recent_low * 1.02

    # MACD
    sig.macd, sig.macd_signal, sig.macd_hist = _macd(prices)
    if len(prices) >= 27:
        prev_macd, prev_sig, _ = _macd(prices[:-1])
        sig.macd_golden_cross = (prev_macd <= prev_sig) and (sig.macd > sig.macd_signal)

    # Bollinger Bands
    sig.bb_upper, sig.bb_middle, sig.bb_lower = _bollinger(prices)
    bb_range = sig.bb_upper - sig.bb_lower
    if bb_range > 0:
        sig.bb_position = round((current - sig.bb_lower) / bb_range, 3)

    # Signal score (-100 to +100)
    score = 0.0
    if sig.above_ma5: score += 10
    if sig.above_ma10: score += 10
    if sig.above_ma20: score += 15
    if sig.above_ma60: score += 15
    if sig.golden_cross: score += 20
    if sig.death_cross: score -= 20
    if sig.price_breakout: score += 20
    if sig.near_support: score += 5
    if sig.volume_surge and current > (prices[-2] if len(prices) >= 2 else current):
        score += 15
    if sig.rsi_signal == "oversold": score += 10
    if sig.rsi_signal == "overbought": score -= 10
    if sig.macd_golden_cross: score += 15
    if sig.macd_hist > 0: score += 5
    else: score -= 5

    sig.signal_score = round(max(-100, min(100, score)), 1)

    if sig.signal_score >= 60:
        sig.signal_label = "强烈看多"
    elif sig.signal_score >= 30:
        sig.signal_label = "看多"
    elif sig.signal_score >= -10:
        sig.signal_label = "中性"
    elif sig.signal_score >= -40:
        sig.signal_label = "看空"
    else:
        sig.signal_label = "强烈看空"

    return sig
