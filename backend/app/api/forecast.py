"""
Forecast API Router — GET /api/v1/forecast/{shop_id}/{ingredient_id}

Returns a predicted demand vector for the requested ingredient.
Velocity data is supplied in query parameters for simplicity; a production
deployment would read it directly from TimescaleDB.
"""

import os
import logging
import redis
from uuid import UUID
from fastapi import APIRouter, HTTPException, Query, status

from app.models.predictor import ForecastVector, VelocityWindow
from app.agents.predictor_agent import PredictorAgent
from app.agents.context_agent import ContextAgent
from app.services.redis_client import get_redis_client

logger = logging.getLogger("BobaMaster.API.Forecast")
router = APIRouter()

_redis_client = get_redis_client()
_context_agent = ContextAgent(redis_client=_redis_client)
_predictor = PredictorAgent()


@router.get(
    "/{shop_id}/{ingredient_id}",
    response_model=ForecastVector,
    status_code=status.HTTP_200_OK,
    summary="Forecast ingredient demand",
    description=(
        "Generates a demand forecast (30m / 60m / 120m) for a specific ingredient "
        "at a given shop. Velocity rates (grams/min) must be supplied as query "
        "parameters; context is resolved automatically from the ContextAgent."
    ),
)
async def get_forecast(
    shop_id: UUID,
    ingredient_id: str,
    grams_per_min_10m: float = Query(..., ge=0.0, description="Avg consumption rate over last 10 minutes (g/min)"),
    grams_per_min_30m: float = Query(..., ge=0.0, description="Avg consumption rate over last 30 minutes (g/min)"),
    grams_per_min_60m: float = Query(..., ge=0.0, description="Avg consumption rate over last 60 minutes (g/min)"),
    lat: float = Query(1.3521, description="Shop latitude (used for context lookup)"),
    lon: float = Query(103.8198, description="Shop longitude (used for context lookup)"),
    is_cold_drink_ingredient: bool = Query(True, description="Apply hot-weather demand boost"),
    is_hot_drink_ingredient: bool = Query(False, description="Apply rain demand boost"),
):
    try:
        velocity = VelocityWindow(
            ingredient_id=ingredient_id,
            grams_per_min_10m=grams_per_min_10m,
            grams_per_min_30m=grams_per_min_30m,
            grams_per_min_60m=grams_per_min_60m,
        )
        context = _context_agent.get_context(shop_id, lat=lat, lon=lon)
        return _predictor.forecast(
            shop_id=shop_id,
            ingredient_id=ingredient_id,
            velocity=velocity,
            context=context,
            is_cold_drink_ingredient=is_cold_drink_ingredient,
            is_hot_drink_ingredient=is_hot_drink_ingredient,
        )
    except Exception as e:
        logger.error(f"forecast error shop={shop_id} ingredient={ingredient_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/compute",
    response_model=ForecastVector,
    status_code=status.HTTP_200_OK,
    summary="Compute forecast from explicit request body",
    description=(
        "Alternative endpoint accepting a full ForecastRequest body with "
        "optional context overrides. Useful for testing or batch scheduling."
    ),
)
async def compute_forecast(
    shop_id: UUID,
    ingredient_id: str,
    velocity: VelocityWindow,
    temp_c: float = Query(None, description="Override ambient temperature (°C)"),
    rain_prob: float = Query(None, ge=0.0, le=1.0, description="Override rain probability"),
    school_in_session: bool = Query(None, description="Override school session flag"),
    is_cold_drink_ingredient: bool = Query(True),
    is_hot_drink_ingredient: bool = Query(False),
):
    try:
        return _predictor.forecast(
            shop_id=shop_id,
            ingredient_id=ingredient_id,
            velocity=velocity,
            temp_c=temp_c,
            rain_prob=rain_prob,
            school_in_session=school_in_session,
            is_cold_drink_ingredient=is_cold_drink_ingredient,
            is_hot_drink_ingredient=is_hot_drink_ingredient,
        )
    except Exception as e:
        logger.error(f"compute_forecast error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
