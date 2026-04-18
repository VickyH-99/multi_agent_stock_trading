"""
Market overview routes: sectors, limit-up pool, northbound, sentiment.
"""
from datetime import datetime

from fastapi import APIRouter
from loguru import logger

from realtime_data_engine import data_engine
from china_market_logic.market_hours import (
    get_market_status, format_large_number, get_exchange, MarketStatus
)
from china_market_logic.sentiment import compute_sentiment
from china_market_logic.sector_rotation import analyze_sector_rotation
from .schemas import (
    MarketOverviewSchema, SectorRankingSchema, SectorSchema, LimitUpPoolSchema,
    LimitStockSchema, NorthboundSchema, SentimentSchema, ProviderStatusSchema,
    DataStatusSchema
)
from .helpers import make_data_status
from realtime_data_engine.providers.base import DataFreshness

router = APIRouter(prefix="/api/market", tags=["market"])


_MARKET_STATUS_LABELS = {
    MarketStatus.PRE_OPEN: "集合竞价",
    MarketStatus.CALL_AUCTION: "竞价",
    MarketStatus.MORNING: "上午交易",
    MarketStatus.LUNCH: "午盘休市",
    MarketStatus.AFTERNOON: "下午交易",
    MarketStatus.CLOSED: "已收盘",
    MarketStatus.WEEKEND: "休市（周末）",
}


@router.get("/overview", response_model=MarketOverviewSchema)
async def market_overview():
    """Full market overview: sectors, limit-up pool, northbound, sentiment."""
    import asyncio
    sectors_data, limit_up_data, northbound_data = await asyncio.gather(
        data_engine.get_sector_data(),
        data_engine.get_limit_up_stocks(),
        data_engine.get_northbound_flow(),
    )

    # Sectors
    rotation = analyze_sector_rotation(sectors_data)
    sector_status = make_data_status(
        DataFreshness.NEAR_REALTIME if sectors_data else DataFreshness.STALE,
        "eastmoney", datetime.now()
    )
    sector_schemas = [
        SectorSchema(
            name=s.name,
            change_pct=round(s.change_pct, 2),
            leading_stock=s.leading_stock,
            leading_stock_change=round(s.leading_stock_change, 2),
            net_inflow=s.net_inflow,
            net_inflow_fmt=format_large_number(s.net_inflow),
        )
        for s in sectors_data
    ]
    top_inflow = sorted(sector_schemas, key=lambda x: x.net_inflow, reverse=True)[:10]

    sectors_schema = SectorRankingSchema(
        sectors=sector_schemas,
        top_inflow=top_inflow,
        rotation_strength=rotation.rotation_strength,
        data_status=sector_status,
    )

    # Limit-up pool
    limit_up_schemas = [
        LimitStockSchema(
            symbol=s.symbol,
            name=s.name,
            price=round(s.price, 2),
            change_pct=round(s.change_pct, 2),
            volume=s.volume,
            amount=s.amount,
            exchange=get_exchange(s.symbol),
        )
        for s in limit_up_data
        if s.symbol
    ]
    limit_schema = LimitUpPoolSchema(
        stocks=limit_up_schemas[:100],
        count=len(limit_up_schemas),
        data_status=make_data_status(
            DataFreshness.NEAR_REALTIME if limit_up_data else DataFreshness.STALE,
            "eastmoney", datetime.now()
        ),
    )

    # Northbound
    north_schema = None
    if northbound_data:
        north_schema = NorthboundSchema(
            date=northbound_data.date,
            sh_net_inflow=northbound_data.sh_net_inflow,
            sz_net_inflow=northbound_data.sz_net_inflow,
            total_net_inflow=northbound_data.total_net_inflow,
            sh_buy=northbound_data.sh_buy, sh_sell=northbound_data.sh_sell,
            sz_buy=northbound_data.sz_buy, sz_sell=northbound_data.sz_sell,
            total_net_inflow_fmt=format_large_number(northbound_data.total_net_inflow),
            data_status=make_data_status(
                DataFreshness.NEAR_REALTIME, "eastmoney", northbound_data.timestamp
            ),
        )

    # Sentiment
    limit_count = len(limit_up_data)
    # Approximate limit-down and up/down counts from sector data
    up_count = sum(1 for s in sectors_data if s.change_pct > 0)
    down_count = sum(1 for s in sectors_data if s.change_pct < 0)
    flat_count = max(0, len(sectors_data) - up_count - down_count)

    sentiment = compute_sentiment(
        limit_up_count=limit_count,
        limit_down_count=max(1, limit_count // 5),  # estimate
        up_count=up_count * 20,  # estimate board -> stocks
        down_count=down_count * 20,
        flat_count=flat_count * 10,
        max_continuous=3,
    )
    market_status = get_market_status()
    sentiment_schema = SentimentSchema(
        date=sentiment.date,
        limit_up_count=sentiment.limit_up_count,
        limit_down_count=sentiment.limit_down_count,
        continuous_limit_up_max=sentiment.continuous_limit_up_max,
        sentiment_score=sentiment.sentiment_score,
        sentiment_label=sentiment.sentiment_label,
        up_count=sentiment.up_count,
        down_count=sentiment.down_count,
        flat_count=sentiment.flat_count,
        market_breadth=sentiment.market_breadth,
        market_status=market_status.value,
        market_status_label=_MARKET_STATUS_LABELS.get(market_status, "未知"),
    )

    # Provider status
    provider_schema = ProviderStatusSchema(
        providers=data_engine.get_provider_status(),
        last_updated=datetime.now().strftime("%H:%M:%S"),
    )

    return MarketOverviewSchema(
        sectors=sectors_schema,
        limit_up_pool=limit_schema,
        northbound=north_schema,
        sentiment=sentiment_schema,
        provider_status=provider_schema,
    )


@router.get("/sectors")
async def get_sectors():
    """Get sector/concept board data."""
    sectors = await data_engine.get_sector_data()
    rotation = analyze_sector_rotation(sectors)
    return {
        "sectors": [
            {
                "name": s.name,
                "change_pct": round(s.change_pct, 2),
                "leading_stock": s.leading_stock,
                "net_inflow": s.net_inflow,
                "net_inflow_fmt": format_large_number(s.net_inflow),
            }
            for s in sectors
        ],
        "rotation_strength": rotation.rotation_strength,
        "top_sectors": rotation.top_sectors[:10],
        "hot_money_sectors": rotation.hot_money_sectors[:10],
        "timestamp": datetime.now().strftime("%H:%M:%S"),
    }


@router.get("/limit-up")
async def get_limit_up():
    """Get real-time limit-up pool (涨停板)."""
    stocks = await data_engine.get_limit_up_stocks()
    return {
        "count": len(stocks),
        "stocks": [
            {
                "symbol": s.symbol,
                "name": s.name,
                "price": round(s.price, 2),
                "change_pct": round(s.change_pct, 2),
                "volume": s.volume,
                "amount": s.amount,
                "exchange": get_exchange(s.symbol),
            }
            for s in stocks
        ],
        "timestamp": datetime.now().strftime("%H:%M:%S"),
    }


@router.get("/northbound")
async def get_northbound():
    """Get northbound capital flow (北向资金)."""
    data = await data_engine.get_northbound_flow()
    if not data:
        return {"error": "Northbound data unavailable", "timestamp": datetime.now().isoformat()}
    return {
        "date": data.date,
        "sh_net_inflow": data.sh_net_inflow,
        "sz_net_inflow": data.sz_net_inflow,
        "total_net_inflow": data.total_net_inflow,
        "total_net_inflow_fmt": format_large_number(data.total_net_inflow),
        "sh_buy": data.sh_buy, "sh_sell": data.sh_sell,
        "sz_buy": data.sz_buy, "sz_sell": data.sz_sell,
        "timestamp": data.timestamp.strftime("%H:%M:%S"),
    }


@router.get("/status")
async def market_status():
    """Get current market session status."""
    status = get_market_status()
    return {
        "status": status.value,
        "label": _MARKET_STATUS_LABELS.get(status, "未知"),
        "is_trading": status in (MarketStatus.MORNING, MarketStatus.AFTERNOON),
        "timestamp": datetime.now().isoformat(),
        "providers": data_engine.get_provider_status(),
    }
