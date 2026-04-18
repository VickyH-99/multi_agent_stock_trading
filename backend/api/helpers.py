"""
Helper functions for building API response schemas from engine data.
"""
from datetime import datetime
from typing import Optional

from realtime_data_engine.providers.base import (
    DataFreshness, QuoteData, CapitalFlowData, MinuteData,
    NorthboundData, SectorData
)
from china_market_logic.market_hours import format_large_number, get_exchange, get_stock_type
from .schemas import DataStatusSchema, QuoteSchema, CapitalFlowSchema, MinuteDataSchema


_FRESHNESS_LABELS = {
    DataFreshness.REALTIME:       ("🟢 实时",   True),
    DataFreshness.NEAR_REALTIME:  ("🟢 准实时",  True),
    DataFreshness.DELAYED:        ("🟡 延迟",    False),
    DataFreshness.STALE:          ("🔴 过期数据", False),
    DataFreshness.UNKNOWN:        ("🟡 未知",    False),
}


def make_data_status(freshness: DataFreshness, source: str, ts: datetime) -> DataStatusSchema:
    label, is_live = _FRESHNESS_LABELS.get(freshness, ("🟡 未知", False))
    return DataStatusSchema(
        freshness=freshness.value,
        source=source,
        timestamp=ts.strftime("%H:%M:%S"),
        label=label,
        is_live=is_live,
    )


def build_quote_schema(quote: QuoteData) -> QuoteSchema:
    return QuoteSchema(
        symbol=quote.symbol,
        name=quote.name,
        price=round(quote.price, 3),
        change=round(quote.change, 3),
        change_pct=round(quote.change_pct, 2),
        volume=quote.volume,
        amount=quote.amount,
        high=round(quote.high, 3),
        low=round(quote.low, 3),
        open_price=round(quote.open_price, 3),
        prev_close=round(quote.prev_close, 3),
        turnover_rate=round(quote.turnover_rate, 2) if quote.turnover_rate else None,
        pe_ratio=round(quote.pe_ratio, 2) if quote.pe_ratio else None,
        total_market_cap=quote.total_market_cap,
        circulating_market_cap=quote.circulating_market_cap,
        bid_price=round(quote.bid_price, 3) if quote.bid_price else None,
        ask_price=round(quote.ask_price, 3) if quote.ask_price else None,
        limit_up=quote.limit_up,
        limit_down=quote.limit_down,
        data_status=make_data_status(quote.freshness, quote.source, quote.timestamp),
        exchange=get_exchange(quote.symbol),
        stock_type=get_stock_type(quote.symbol),
    )


def build_flow_schema(flow: CapitalFlowData) -> CapitalFlowSchema:
    return CapitalFlowSchema(
        symbol=flow.symbol,
        main_net_inflow=flow.main_net_inflow,
        super_large_inflow=flow.super_large_inflow,
        super_large_outflow=flow.super_large_outflow,
        large_inflow=flow.large_inflow,
        large_outflow=flow.large_outflow,
        medium_inflow=flow.medium_inflow,
        medium_outflow=flow.medium_outflow,
        small_inflow=flow.small_inflow,
        small_outflow=flow.small_outflow,
        main_net_inflow_fmt=format_large_number(flow.main_net_inflow),
        data_status=make_data_status(DataFreshness.NEAR_REALTIME, flow.source, flow.timestamp),
    )


def build_minute_schema(minute: MinuteData) -> MinuteDataSchema:
    return MinuteDataSchema(
        symbol=minute.symbol,
        times=minute.times,
        prices=minute.prices,
        volumes=minute.volumes,
        avg_prices=minute.avg_prices,
        data_status=make_data_status(DataFreshness.NEAR_REALTIME, minute.source, minute.timestamp),
    )
