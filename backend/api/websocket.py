"""
WebSocket endpoint for real-time push updates.
Clients subscribe to symbols and receive price updates every N seconds.
"""
import asyncio
import json
from datetime import datetime
from typing import Dict, List, Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger

from realtime_data_engine import data_engine
from china_market_logic.market_hours import get_market_status, MarketStatus, format_large_number
from .helpers import build_quote_schema

router = APIRouter(tags=["websocket"])


class ConnectionManager:
    """Manages WebSocket connections and subscriptions."""

    def __init__(self):
        # ws -> set of subscribed symbols
        self._connections: Dict[WebSocket, Set[str]] = {}

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self._connections[ws] = set()
        logger.info(f"[WS] Client connected. Total: {len(self._connections)}")

    def disconnect(self, ws: WebSocket):
        self._connections.pop(ws, None)
        logger.info(f"[WS] Client disconnected. Total: {len(self._connections)}")

    def subscribe(self, ws: WebSocket, symbols: List[str]):
        if ws in self._connections:
            self._connections[ws].update(symbols)

    def unsubscribe(self, ws: WebSocket, symbols: List[str]):
        if ws in self._connections:
            self._connections[ws].difference_update(symbols)

    async def broadcast_to_subscriber(self, ws: WebSocket, message: dict):
        try:
            await ws.send_json(message)
        except Exception:
            self.disconnect(ws)

    def get_all_subscribed_symbols(self) -> Set[str]:
        all_syms: Set[str] = set()
        for syms in self._connections.values():
            all_syms.update(syms)
        return all_syms

    def get_subscribers_for(self, symbol: str) -> List[WebSocket]:
        return [ws for ws, syms in self._connections.items() if symbol in syms]


manager = ConnectionManager()


async def _push_quote(symbol: str):
    """Fetch latest quote and push to all subscribers."""
    subscribers = manager.get_subscribers_for(symbol)
    if not subscribers:
        return

    quote = await data_engine.get_quote(symbol)
    if not quote:
        return

    quote_schema = build_quote_schema(quote)
    message = {
        "type": "quote",
        "symbol": symbol,
        "data": quote_schema.model_dump(),
        "timestamp": datetime.now().isoformat(),
    }

    for ws in subscribers:
        await manager.broadcast_to_subscriber(ws, message)


async def _push_market_pulse():
    """Push market status pulse to all connected clients."""
    if not manager._connections:
        return
    status = get_market_status()
    message = {
        "type": "market_pulse",
        "status": status.value,
        "timestamp": datetime.now().isoformat(),
    }
    for ws in list(manager._connections.keys()):
        await manager.broadcast_to_subscriber(ws, message)


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time updates.
    
    Client sends JSON commands:
    {"action": "subscribe", "symbols": ["000001", "600036"]}
    {"action": "unsubscribe", "symbols": ["000001"]}
    {"action": "set_interval", "interval": 5}  // seconds
    
    Server pushes:
    {"type": "quote", "symbol": "...", "data": {...}}
    {"type": "market_pulse", "status": "..."}
    {"type": "error", "message": "..."}
    """
    await manager.connect(websocket)
    refresh_interval = 10  # default
    refresh_task: asyncio.Task = None

    async def push_loop():
        while True:
            try:
                all_symbols = list(manager._connections.get(websocket, set()))
                if all_symbols:
                    tasks = [_push_quote(sym) for sym in all_symbols]
                    await asyncio.gather(*tasks, return_exceptions=True)
                await asyncio.sleep(refresh_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.debug(f"[WS] Push loop error: {e}")
                await asyncio.sleep(refresh_interval)

    refresh_task = asyncio.create_task(push_loop())

    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                action = msg.get("action")

                if action == "subscribe":
                    symbols = [s for s in msg.get("symbols", []) if isinstance(s, str)]
                    manager.subscribe(websocket, symbols)
                    await websocket.send_json({
                        "type": "subscribed",
                        "symbols": list(manager._connections.get(websocket, set())),
                    })
                    # Immediate push on subscribe
                    tasks = [_push_quote(sym) for sym in symbols]
                    await asyncio.gather(*tasks, return_exceptions=True)

                elif action == "unsubscribe":
                    symbols = msg.get("symbols", [])
                    manager.unsubscribe(websocket, symbols)

                elif action == "set_interval":
                    interval = int(msg.get("interval", 10))
                    refresh_interval = max(3, min(60, interval))
                    await websocket.send_json({"type": "interval_set", "interval": refresh_interval})

                elif action == "ping":
                    await websocket.send_json({"type": "pong", "timestamp": datetime.now().isoformat()})

            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "message": "Invalid JSON"})

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.warning(f"[WS] Connection error: {e}")
    finally:
        if refresh_task:
            refresh_task.cancel()
        manager.disconnect(websocket)
