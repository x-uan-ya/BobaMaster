"""
WebSocket Connection Manager & Dispatcher Router (Milestone 7)

Routes
──────
WS   /ws/shop/{shop_id}
    Long-lived WebSocket connection for a KDS tablet.
    Receives broadcast messages whenever the DispatcherAgent fires an alert.

POST /api/v1/operations/trigger-test-alert  (defined in operations.py)
    Already wired — calls dispatcher internally.

POST /api/v1/dispatcher/broadcast
    Internal endpoint used by background tasks to push a pre-built
    AlertPayload through the full Gemini → WebSocket pipeline.
"""

from __future__ import annotations

import logging
import os
import json
import redis
from datetime import datetime, timezone, timedelta
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, status, Query
from fastapi.encoders import jsonable_encoder
from typing import Optional

from app.models.dispatcher import AlertPayload, DispatchMessage
from app.models.inventory import InventoryStateResponse
from app.models.ops_decider import DecisionAction
from app.agents.dispatcher_agent import DispatcherAgent

logger = logging.getLogger("BobaMaster.WebSocket")

# ──────────────────────────────────────────────────────────────────────────────
# WebSocket Connection Manager
# ──────────────────────────────────────────────────────────────────────────────

class WebSocketManager:
    """
    Manages all active WebSocket connections, grouped by shop_id.
    Thread-safety note: FastAPI runs in a single async event loop per worker,
    so dict mutations here are safe without locks in a single-process deployment.
    """

    def __init__(self):
        # shop_id (str) → list of active WebSocket connections
        self._connections: dict[str, list[WebSocket]] = {}

    async def connect(self, shop_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.setdefault(shop_id, []).append(websocket)
        logger.info(
            f"WS connected: shop={shop_id} "
            f"total_for_shop={len(self._connections[shop_id])}"
        )

    def disconnect(self, shop_id: str, websocket: WebSocket) -> None:
        if shop_id in self._connections:
            try:
                self._connections[shop_id].remove(websocket)
            except ValueError:
                pass
            if not self._connections[shop_id]:
                del self._connections[shop_id]
        logger.info(f"WS disconnected: shop={shop_id}")

    async def broadcast(self, shop_id: str, message: str) -> None:
        """Send a text message to every client connected to a shop channel."""
        dead: list[WebSocket] = []
        for ws in self._connections.get(shop_id, []):
            try:
                await ws.send_text(message)
            except Exception as e:
                logger.warning(f"WS send failed for shop={shop_id}: {e}. Marking for removal.")
                dead.append(ws)
        for ws in dead:
            self.disconnect(shop_id, ws)

    def connection_count(self, shop_id: str) -> int:
        return len(self._connections.get(shop_id, []))

    def all_shop_ids(self) -> list[str]:
        return list(self._connections.keys())


async def broadcast_inventory_update(
    shop_id: str,
    inventory_state: InventoryStateResponse,
) -> None:
    payload = {
        "event_type": "inventory_update",
        "shop_id": shop_id,
        "ingredients": [jsonable_encoder(inventory_state)],
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    await ws_manager.broadcast(shop_id=shop_id, message=json.dumps(payload))


# ──────────────────────────────────────────────────────────────────────────────
# Singletons
# ──────────────────────────────────────────────────────────────────────────────

# Shared manager — imported by other modules that need to broadcast
ws_manager = WebSocketManager()

# DispatcherAgent — lazy singleton; initialized on first request so no import-time crash
# when GEMINI_API_KEY is absent.
_dispatcher: Optional[DispatcherAgent] = None


def _get_dispatcher() -> DispatcherAgent:
    global _dispatcher
    if _dispatcher is None:
        _dispatcher = DispatcherAgent(broadcaster=ws_manager)
    return _dispatcher

# ──────────────────────────────────────────────────────────────────────────────
# Routers
# ──────────────────────────────────────────────────────────────────────────────

ws_router = APIRouter()        # WebSocket endpoint (no prefix — FastAPI handles it at app level)
dispatcher_router = APIRouter()  # REST endpoints for the dispatcher


# ── WebSocket endpoint ────────────────────────────────────────────────────────

@ws_router.websocket("/ws/shop/{shop_id}")
async def websocket_endpoint(websocket: WebSocket, shop_id: str):
    """
    Persistent WebSocket channel for a shop's KDS tablet.
    Clients connect here and receive DispatchMessage JSON payloads whenever
    the DispatcherAgent fires an alert.
    """
    await ws_manager.connect(shop_id, websocket)
    try:
        # Keep connection alive; handle any incoming client messages (ping/ack)
        while True:
            data = await websocket.receive_text()
            # Clients can send a ping; we echo an ack
            if data.strip().lower() in ("ping", "{}"):
                await websocket.send_text('{"type":"pong"}')
    except WebSocketDisconnect:
        ws_manager.disconnect(shop_id, websocket)


# ── REST dispatcher endpoints ─────────────────────────────────────────────────

@dispatcher_router.post(
    "/broadcast",
    response_model=DispatchMessage,
    status_code=status.HTTP_200_OK,
    summary="Broadcast an alert through the full Gemini → WebSocket pipeline",
    description=(
        "Accepts an AlertPayload, calls Gemini 1.5 Flash for a natural language "
        "explanation, composes a DispatchMessage, and broadcasts it to all "
        "WebSocket clients connected to the shop channel."
    ),
)
async def broadcast_alert(payload: AlertPayload) -> DispatchMessage:
    try:
        return await _get_dispatcher().dispatch(payload)
    except Exception as e:
        logger.error(f"broadcast_alert error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@dispatcher_router.post(
    "/trigger-test-alert",
    response_model=DispatchMessage,
    status_code=status.HTTP_200_OK,
    summary="Trigger a test BREW_NOW alert through the full pipeline",
    description=(
        "Injects a deterministic low-stock scenario for tapioca_pearls and runs "
        "it through the Gemini explanation + WebSocket broadcast pipeline. "
        "Useful for end-to-end testing without real sales data."
    ),
)
async def trigger_test_alert(
    shop_id: UUID = Query(..., description="Target shop UUID"),
) -> DispatchMessage:
    try:
        now = datetime.now(timezone.utc)
        payload = AlertPayload(
            shop_id=shop_id,
            ingredient_id="tapioca_pearls",
            action=DecisionAction.BREW_NOW,
            current_stock_grams=400.0,
            active_brewing_grams=0.0,
            predicted_consumption_grams=2000.0,
            target_runway_grams=-1600.0,
            cook_time_minutes=50,
            temp_c=31.0,
            rain_prob=0.1,
            school_in_session=True,
            predicted_shortage_at=now + timedelta(minutes=12),
        )
        return await _get_dispatcher().dispatch(payload)
    except Exception as e:
        logger.error(f"trigger-test-alert error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@dispatcher_router.get(
    "/connections",
    status_code=status.HTTP_200_OK,
    summary="List active WebSocket connections",
)
async def list_connections():
    return {
        "connected_shops": ws_manager.all_shop_ids(),
        "counts": {
            sid: ws_manager.connection_count(sid)
            for sid in ws_manager.all_shop_ids()
        },
    }
