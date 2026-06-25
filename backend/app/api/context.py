import os
import logging
import redis
from fastapi import APIRouter, HTTPException, status
from uuid import UUID

from app.models.context import ContextVector
from app.agents.context_agent import ContextAgent
from app.services.redis_client import get_redis_client

logger = logging.getLogger("BobaMaster.API.Context")
router = APIRouter()

_redis_client = get_redis_client()
_context_agent = ContextAgent(redis_client=_redis_client)


@router.get(
    "/{shop_id}",
    response_model=ContextVector,
    status_code=status.HTTP_200_OK,
    summary="Get current operational context",
    description=(
        "Returns the current ContextVector for a shop including weather, "
        "school calendar status, and local event indicators. "
        "Results are cached for 15 minutes."
    ),
)
async def get_context(shop_id: UUID):
    try:
        return _context_agent.get_context(shop_id)
    except Exception as e:
        logger.error(f"get_context error for shop {shop_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/{shop_id}/cache",
    status_code=status.HTTP_200_OK,
    summary="Invalidate context cache",
    description="Force-clears the cached context snapshot for a shop. Useful after a manual event override.",
)
async def invalidate_context_cache(shop_id: UUID):
    try:
        _context_agent.invalidate_cache(shop_id)
        return {"status": "ok", "message": f"Context cache cleared for shop {shop_id}."}
    except Exception as e:
        logger.error(f"invalidate_context_cache error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
