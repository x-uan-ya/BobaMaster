"""
Operations API Router — Milestone 6

Endpoints
─────────
GET  /api/v1/operations/decisions/{shop_id}
    Evaluate safety stock for all tracked ingredients and return active alerts.

POST /api/v1/operations/trigger-test-alert
    Fire a deterministic test evaluation (used by the WebSocket pipe in M7).
"""

from __future__ import annotations

import os
import logging
import redis
from uuid import UUID
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, HTTPException, Query, status

from app.models.ops_decider import ActiveAlertsResponse, OpsDecision, DecisionAction
from app.models.predictor import ForecastVector, VelocityWindow
from app.models.inventory import InventoryStateResponse
from app.agents.ops_decider_agent import OpsDeciderAgent, DEFAULT_INGREDIENT_CONFIGS
from app.agents.predictor_agent import PredictorAgent
from app.agents.inventory_agent import InventoryAgent
from app.agents.context_agent import ContextAgent
from app.services.inventory_service import InventoryService
from app.services.recommendation_service import RecommendationService

logger = logging.getLogger("BobaMaster.API.Operations")
router = APIRouter()

# ──────────────────────────────────────────────────────────────────────────────
# Shared singletons (Redis + agents)
# ──────────────────────────────────────────────────────────────────────────────
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
_redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=False)

_inv_service  = InventoryService(_redis_client)
_inv_agent    = InventoryAgent(_inv_service)
_ctx_agent    = ContextAgent(redis_client=_redis_client)
_predictor    = PredictorAgent()
_rec_service  = RecommendationService()

# Shared cooldown store — persists across request lifecycle
_cooldown_store: dict[str, datetime] = {}
_ops_agent = OpsDeciderAgent(
    recommendation_writer=_rec_service.write,
    cooldown_store=_cooldown_store,
)

# Ingredients tracked by the decision loop
_TRACKED_INGREDIENTS = list(DEFAULT_INGREDIENT_CONFIGS.keys())


# ──────────────────────────────────────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────────────────────────────────────

@router.get(
    "/decisions/{shop_id}",
    response_model=ActiveAlertsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get active operational decisions",
    description=(
        "Evaluates safety stock for all tracked ingredients at a shop and returns "
        "a list of decisions (BREW_NOW / WARN / WAIT). Uses cached context and "
        "a flat velocity estimate derived from current inventory levels."
    ),
)
async def get_decisions(
    shop_id: UUID,
    lat: float = Query(1.3521, description="Shop latitude"),
    lon: float = Query(103.8198, description="Shop longitude"),
):
    try:
        context = _ctx_agent.get_context(shop_id, lat=lat, lon=lon)
        decisions: list[OpsDecision] = []
        now = datetime.now(timezone.utc)

        for ingredient_id in _TRACKED_INGREDIENTS:
            inv = _inv_agent.get_inventory_state(shop_id, ingredient_id)
            cfg = DEFAULT_INGREDIENT_CONFIGS[ingredient_id]

            # Derive a conservative velocity from current stock ÷ typical shelf life
            # (a real deployment reads from TimescaleDB transaction history)
            implied_rate = _estimate_velocity(inv.total_remaining_grams, cfg.cook_time_minutes)

            velocity = VelocityWindow(
                ingredient_id=ingredient_id,
                grams_per_min_10m=implied_rate,
                grams_per_min_30m=implied_rate,
                grams_per_min_60m=implied_rate,
            )
            forecast = _predictor.forecast(
                shop_id=shop_id,
                ingredient_id=ingredient_id,
                velocity=velocity,
                context=context,
            )
            decision = _ops_agent.evaluate(inv, forecast)
            decisions.append(decision)

        return ActiveAlertsResponse(
            shop_id=shop_id,
            evaluated_at=now,
            decisions=decisions,
        )
    except Exception as e:
        logger.error(f"get_decisions error shop={shop_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/trigger-test-alert",
    response_model=OpsDecision,
    status_code=status.HTTP_200_OK,
    summary="Trigger a deterministic test BREW_NOW alert",
    description=(
        "Injects a low-stock + high-forecast scenario for tapioca_pearls and "
        "runs the decision engine. Used to test the WebSocket broadcast pipeline "
        "in Milestone 7 without needing real sales data."
    ),
)
async def trigger_test_alert(
    shop_id: UUID = Query(..., description="Target shop UUID"),
):
    try:
        now = datetime.now(timezone.utc)
        expires = now + timedelta(hours=3)

        # Synthetic low-stock inventory snapshot (400g — well below safety floor)
        inv = InventoryStateResponse(
            shop_id=shop_id,
            ingredient_id="tapioca_pearls",
            total_remaining_grams=400.0,
            active_batches=[],
            active_brewing_qty_grams=0.0,
            nearest_expiry=expires,
        )
        # High-demand forecast (matches milestone spec: 2000g over 60m window)
        forecast = ForecastVector(
            shop_id=shop_id,
            ingredient_id="tapioca_pearls",
            school_multiplier=1.35,
            temp_multiplier=1.0,
            rain_multiplier=1.0,
            t30_grams=1000.0,
            t60_grams=2000.0,
            t120_grams=4000.0,
        )
        # Use a fresh agent instance with no cooldown so test always fires
        test_agent = OpsDeciderAgent(recommendation_writer=_rec_service.write)
        decision = test_agent.evaluate(inv, forecast)
        return decision
    except Exception as e:
        logger.error(f"trigger-test-alert error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ──────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ──────────────────────────────────────────────────────────────────────────────

def _estimate_velocity(total_grams: float, cook_time_minutes: int) -> float:
    """
    Conservative velocity estimate: assume current stock will sustain sales
    for 2× the cook window before needing a new batch.  Returns grams/min.
    """
    if total_grams <= 0 or cook_time_minutes <= 0:
        return 0.0
    return total_grams / (cook_time_minutes * 2)
