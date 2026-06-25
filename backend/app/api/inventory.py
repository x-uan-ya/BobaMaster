import os
import json
import logging
import redis
from fastapi import APIRouter, HTTPException, status
from fastapi.encoders import jsonable_encoder
from uuid import UUID
from datetime import datetime, timezone

from app.models.inventory import (
    BrewStartRequest, BrewStartResponse,
    BrewCompleteRequest, BrewCompleteResponse,
    RecalibrateRequest, RecalibrateResponse,
    WasteLogRequest, WasteLogResponse,
    InventoryStateResponse,
)
from app.agents.inventory_agent import InventoryAgent
from app.services.inventory_service import InventoryService
from app.services.redis_client import get_redis_client
from app.api.websocket import broadcast_inventory_update

logger = logging.getLogger("BobaMaster.API.Inventory")
router = APIRouter()

# ---------------------------------------------------------------------------
# Dependency: shared Redis client and agent instances
# ---------------------------------------------------------------------------
_redis_client = get_redis_client()
_inventory_service = InventoryService(_redis_client)
_inventory_agent = InventoryAgent(_inventory_service)

TRACKED_INGREDIENTS = [
    "tapioca_pearls",
    "black_tea",
    "jasmine_tea",
    "oolong_tea",
    "matcha_powder",
]


async def _broadcast_inventory_update(shop_id: UUID, ingredient_id: str) -> None:
    try:
        state = _inventory_agent.get_inventory_state(shop_id, ingredient_id)
        await broadcast_inventory_update(str(shop_id), state)
    except Exception as e:
        logger.warning(
            f"Failed to broadcast inventory update for {ingredient_id} at shop {shop_id}: {e}"
        )


@router.post(
    "/brew/start",
    response_model=BrewStartResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start a brew batch",
    description="Register that staff have started cooking a new ingredient batch.",
)
async def start_brew(req: BrewStartRequest):
    try:
        batch = _inventory_agent.start_brew(req)
        await _broadcast_inventory_update(req.shop_id, req.ingredient_id)
        return BrewStartResponse(
            batch_id=batch.batch_id,
            shop_id=batch.shop_id,
            ingredient_id=batch.ingredient_id,
            initial_qty_grams=batch.initial_qty,
            started_at=batch.started_at,
        )
    except Exception as e:
        logger.error(f"start_brew error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/brew/complete",
    response_model=BrewCompleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Complete a brew batch",
    description="Mark a cooking batch as finished. Starts the shelf-life expiry countdown.",
)
async def complete_brew(req: BrewCompleteRequest):
    try:
        batch = _inventory_agent.complete_brew(req)
        await _broadcast_inventory_update(req.shop_id, req.ingredient_id)
        return BrewCompleteResponse(
            batch_id=batch.batch_id,
            ingredient_id=batch.ingredient_id,
            completed_at=batch.completed_at,
            expires_at=batch.expires_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"complete_brew error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/recalibrate",
    response_model=RecalibrateResponse,
    status_code=status.HTTP_200_OK,
    summary="Manual inventory recalibration",
    description="Override the system estimate with a physical audit weight.",
)
async def recalibrate(req: RecalibrateRequest):
    try:
        prev, new = _inventory_agent.recalibrate(req)
        await _broadcast_inventory_update(req.shop_id, req.ingredient_id)
        return RecalibrateResponse(
            shop_id=req.shop_id,
            ingredient_id=req.ingredient_id,
            previous_total_grams=prev,
            new_total_grams=new,
        )
    except Exception as e:
        logger.error(f"recalibrate error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/waste",
    response_model=WasteLogResponse,
    status_code=status.HTTP_200_OK,
    summary="Log ingredient waste",
    description="Log early discard of a batch (spillage, contamination, quality rejection).",
)
async def log_waste(req: WasteLogRequest):
    try:
        batch = _inventory_agent.log_waste(req)
        await _broadcast_inventory_update(req.shop_id, req.ingredient_id)
        return WasteLogResponse(
            batch_id=req.batch_id,
            ingredient_id=req.ingredient_id,
            waste_qty_grams=req.waste_qty_grams,
            remaining_qty_grams=batch.remaining_qty,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"log_waste error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{shop_id}/{ingredient_id}",
    response_model=InventoryStateResponse,
    status_code=status.HTTP_200_OK,
    summary="Get live inventory state",
    description="Returns active batch stack and remaining volumes for a given ingredient.",
)
async def get_inventory_state(shop_id: UUID, ingredient_id: str):
    try:
        return _inventory_agent.get_inventory_state(shop_id, ingredient_id)
    except Exception as e:
        logger.error(f"get_inventory_state error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/shop/{shop_id}",
    response_model=list[InventoryStateResponse],
    status_code=status.HTTP_200_OK,
    summary="Get shop inventory snapshot",
    description="Returns current inventory states for tracked ingredients at a shop.",
)
async def get_shop_inventory_state(shop_id: UUID):
    try:
        return [
            _inventory_agent.get_inventory_state(shop_id, ingredient_id)
            for ingredient_id in TRACKED_INGREDIENTS
        ]
    except Exception as e:
        logger.error(f"get_shop_inventory_state error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
