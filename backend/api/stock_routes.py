"""
Stock analysis routes.
"""
from datetime import datetime

import akshare as ak
import pandas as pd
from fastapi import APIRouter, HTTPException, Query
from loguru import logger

from akshare_runtime import run_akshare_in_executor
from realtime_data_engine import data_engine
from indicators.technical import compute_technical_signals
from indicators.capital_flow_signals import analyze_capital_flow
from scoring.scorer import score_stock
from .schemas import FullAnalysisSchema, QuoteSchema, TechnicalSignalsSchema, StockScoreSchema
from .helpers import build_quote_schema, build_flow_schema, build_minute_schema

router = APIRouter(prefix="/api/stock", tags=["stock"])


def _format_stock_symbol_for_history(symbol: str) -> str:
    if symbol.startswith("6"):
        return f"sh{symbol}"
    if symbol.startswith(("0", "3")):
        return f"sz{symbol}"
    if symbol.startswith(("4", "8")):
        return f"bj{symbol}"
    return symbol


def _resample_history(df: pd.DataFrame, period: str) -> pd.DataFrame:
    if period == "daily":
        return df.copy()

    if period not in {"weekly", "monthly"}:
        raise HTTPException(status_code=400, detail="Unsupported period. Use daily/weekly/monthly.")

    rule = "W-FRI" if period == "weekly" else "M"
    grouped = (
        df.set_index("date")
        .resample(rule)
        .agg(
            {
                "open": "first",
                "high": "max",
                "low": "min",
                "close": "last",
                "volume": "sum",
                "amount": "sum",
            }
        )
        .dropna(subset=["open", "close"])
    )
    grouped = grouped.reset_index()
    return grouped


def _prepare_history_records(df: pd.DataFrame, count: int) -> list[dict]:
    frame = df.sort_values("date").copy()
    frame["change_pct"] = frame["close"].pct_change().fillna(0).mul(100)
    frame = frame.tail(count)

    records: list[dict] = []
    for _, row in frame.iterrows():
        records.append(
            {
                "date": pd.Timestamp(row["date"]).strftime("%Y-%m-%d"),
                "open": round(float(row["open"]), 3),
                "high": round(float(row["high"]), 3),
                "low": round(float(row["low"]), 3),
                "close": round(float(row["close"]), 3),
                "volume": float(row["volume"]),
                "amount": float(row["amount"]),
                "change_pct": round(float(row["change_pct"]), 2),
            }
        )
    return records


def _fetch_history_frame(symbol: str, start_date: str) -> pd.DataFrame:
    history_symbol = _format_stock_symbol_for_history(symbol)
    end_date = datetime.now().strftime("%Y%m%d")
    df = ak.stock_zh_a_daily(
        symbol=history_symbol,
        start_date=start_date,
        end_date=end_date,
        adjust="qfq",
    )
    if df is None or df.empty:
        raise HTTPException(status_code=404, detail="No history data found")

    frame = df.rename(
        columns={
            "date": "date",
            "open": "open",
            "high": "high",
            "low": "low",
            "close": "close",
            "volume": "volume",
            "amount": "amount",
        }
    )
    frame = frame[["date", "open", "high", "low", "close", "volume", "amount"]].copy()
    frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
    frame = frame.dropna(subset=["date", "open", "high", "low", "close"])
    frame = frame[frame["date"] >= pd.Timestamp(start_date)]
    if frame.empty:
        raise HTTPException(status_code=404, detail="No history data found")
    return frame


@router.get("/{symbol}", response_model=FullAnalysisSchema)
async def analyze_stock(symbol: str):
    """
    Full analysis for a single stock.
    Returns quote, capital flow, minute data, technical signals, and composite score.
    """
    symbol = symbol.strip()
    if not symbol.isdigit() or len(symbol) != 6:
        raise HTTPException(status_code=400, detail="Invalid symbol format. Use 6-digit code.")

    # Fetch all data in parallel
    all_data = await data_engine.get_all_market_data(symbol)
    quote = all_data.get("quote")
    minute = all_data.get("minute_data")
    flow = all_data.get("capital_flow")

    is_fallback = quote is None
    fallback_msg = None

    if is_fallback:
        fallback_msg = "Live data unavailable, showing latest cached data"
        logger.warning(f"[API] Fallback mode for {symbol}")

    # Technical signals from minute data
    tech = None
    if minute and minute.prices and len(minute.prices) >= 5:
        tech = compute_technical_signals(symbol, minute.prices, minute.volumes)

    # Capital flow signal
    flow_signal = analyze_capital_flow(flow)

    # Score
    score = None
    if quote:
        score = score_stock(
            symbol=symbol,
            name=quote.name,
            tech=tech,
            flow=flow_signal,
            change_pct=quote.change_pct,
            limit_up=quote.limit_up,
            limit_down=quote.limit_down,
        )

    return FullAnalysisSchema(
        quote=build_quote_schema(quote) if quote else None,
        capital_flow=build_flow_schema(flow) if flow else None,
        minute_data=build_minute_schema(minute) if minute else None,
        technical=TechnicalSignalsSchema(
            symbol=tech.symbol,
            above_ma5=tech.above_ma5, above_ma10=tech.above_ma10,
            above_ma20=tech.above_ma20, above_ma60=tech.above_ma60,
            golden_cross=tech.golden_cross, death_cross=tech.death_cross,
            volume_surge=tech.volume_surge, volume_ratio=tech.volume_ratio,
            rsi_14=tech.rsi_14, rsi_signal=tech.rsi_signal,
            price_breakout=tech.price_breakout, near_support=tech.near_support,
            macd=tech.macd, macd_signal=tech.macd_signal, macd_hist=tech.macd_hist,
            macd_golden_cross=tech.macd_golden_cross,
            bb_upper=tech.bb_upper, bb_middle=tech.bb_middle, bb_lower=tech.bb_lower,
            bb_position=tech.bb_position,
            signal_score=tech.signal_score, signal_label=tech.signal_label,
        ) if tech else None,
        score=StockScoreSchema(
            symbol=score.symbol, name=score.name,
            technical_score=score.technical_score,
            capital_flow_score=score.capital_flow_score,
            composite_score=score.composite_score,
            grade=score.grade, recommendation=score.recommendation,
            risk_level=score.risk_level, risk_warnings=score.risk_warnings,
        ) if score else None,
        is_fallback=is_fallback,
        fallback_message=fallback_msg,
    )


@router.get("/{symbol}/quote", response_model=QuoteSchema)
async def get_quote(symbol: str):
    """Get real-time quote for a symbol."""
    symbol = symbol.strip()
    quote = await data_engine.get_quote(symbol)
    if not quote:
        raise HTTPException(status_code=503, detail="Unable to fetch quote data")
    return build_quote_schema(quote)


@router.get("/batch/quotes")
async def get_batch_quotes(symbols: str = Query(..., description="Comma-separated symbols")):
    """Get real-time quotes for multiple symbols."""
    sym_list = [s.strip() for s in symbols.split(",") if s.strip() and s.strip().isdigit()]
    if not sym_list:
        raise HTTPException(status_code=400, detail="No valid symbols provided")
    if len(sym_list) > 50:
        raise HTTPException(status_code=400, detail="Max 50 symbols per batch")

    quotes = await data_engine.get_batch_quotes(sym_list)
    return [build_quote_schema(q) for q in quotes]


@router.get("/{symbol}/history")
async def get_history(
    symbol: str,
    period: str = Query("daily", description="daily/weekly/monthly"),
    count: int = Query(120, ge=10, le=500),
):
    """Get historical OHLCV data with proxy-safe AkShare access."""
    symbol = symbol.strip()
    try:
        period = period.lower().strip()
        daily_frame = await run_akshare_in_executor(
            _fetch_history_frame,
            symbol,
            "20200101",
        )
        period_frame = _resample_history(daily_frame, period)
        records = _prepare_history_records(period_frame, count)
        return {"symbol": symbol, "period": period, "count": len(records), "data": records}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] History error for {symbol}: {e}")
        raise HTTPException(status_code=503, detail=f"History data error: {str(e)}")
