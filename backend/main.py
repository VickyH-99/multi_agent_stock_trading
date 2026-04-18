"""
Main FastAPI application entry point.
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from loguru import logger

from config import get_settings
from realtime_data_engine import data_engine
from api import stock_router, market_router, ws_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    logger.info("🚀 Starting Stock Analysis Platform...")
    await data_engine.initialize()
    logger.info("✅ Data engine ready")
    yield
    logger.info("🛑 Shutting down...")


app = FastAPI(
    title="A-Share Real-Time Analysis Platform",
    description="Professional China A-share stock analysis with real-time market data",
    version="1.0.0",
    lifespan=lifespan,
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Routers
app.include_router(stock_router)
app.include_router(market_router)
app.include_router(ws_router)


@app.get("/health")
async def health():
    from datetime import datetime
    return {
        "status": "ok",
        "providers": data_engine.get_provider_status(),
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/")
async def root():
    return {
        "name": "A-Share Real-Time Analysis API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
