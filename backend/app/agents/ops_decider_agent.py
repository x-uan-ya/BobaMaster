"""
OpsDeciderAgent — Operational Decision Model (Milestone 6)

Evaluates current inventory runway against demand forecasts and cook lead
times to produce discrete per-ingredient decisions:

    BREW_NOW  — Stock will be exhausted before a new batch finishes cooking.
    WARN      — Stock is above the critical floor but below the warn threshold.
    WAIT      — Runway is sufficient; no action needed this cycle.

Design principles
─────────────────
• Purely deterministic arithmetic — zero LLM calls here.
• Cooldown deduplication: will NOT emit a second BREW_NOW for the same
  ingredient within COOLDOWN_MINUTES of the previous recommendation, to
  prevent alert fatigue on the kitchen display.
• PostgreSQL writes are performed via an injected writer callable so the
  agent remains unit-testable without a live database.
"""

from __future__ import annotations

import json
import logging
from uuid import UUID, uuid4
from datetime import datetime, timezone, timedelta
from typing import Callable, Optional

from app.models.ops_decider import (
    DecisionAction,
    IngredientConfig,
    OpsDecision,
    RecommendationLog,
)
from app.models.predictor import ForecastVector
from app.models.inventory import InventoryStateResponse

logger = logging.getLogger("BobaMaster.OpsDeciderAgent")

# ──────────────────────────────────────────────────────────────────────────────
# Default ingredient configurations
# ──────────────────────────────────────────────────────────────────────────────

DEFAULT_INGREDIENT_CONFIGS: dict[str, IngredientConfig] = {
    "tapioca_pearls": IngredientConfig(
        ingredient_id="tapioca_pearls",
        cook_time_minutes=50,
        batch_size_grams=2000.0,
        safety_buffer_grams=200.0,
        warn_buffer_grams=600.0,
    ),
    "black_tea": IngredientConfig(
        ingredient_id="black_tea",
        cook_time_minutes=15,
        batch_size_grams=4000.0,
        safety_buffer_grams=300.0,
        warn_buffer_grams=800.0,
    ),
    "jasmine_tea": IngredientConfig(
        ingredient_id="jasmine_tea",
        cook_time_minutes=15,
        batch_size_grams=4000.0,
        safety_buffer_grams=300.0,
        warn_buffer_grams=800.0,
    ),
    "oolong_tea": IngredientConfig(
        ingredient_id="oolong_tea",
        cook_time_minutes=15,
        batch_size_grams=4000.0,
        safety_buffer_grams=300.0,
        warn_buffer_grams=800.0,
    ),
    "thai_tea": IngredientConfig(
        ingredient_id="thai_tea",
        cook_time_minutes=15,
        batch_size_grams=4000.0,
        safety_buffer_grams=300.0,
        warn_buffer_grams=800.0,
    ),
}

# Alert deduplication window — don't fire a second BREW_NOW within this many minutes
COOLDOWN_MINUTES = 10

# ──────────────────────────────────────────────────────────────────────────────
# RecommendationWriter protocol
# ──────────────────────────────────────────────────────────────────────────────

# Type alias for the DB write callable: accepts a RecommendationLog, returns None.
RecommendationWriter = Callable[[RecommendationLog], None]


def _noop_writer(log: RecommendationLog) -> None:
    """No-op writer used when no DB connection is available (e.g. unit tests)."""
    logger.debug(f"[noop writer] Would write recommendation {log.id} to DB.")


# ──────────────────────────────────────────────────────────────────────────────
# OpsDeciderAgent
# ──────────────────────────────────────────────────────────────────────────────

class OpsDeciderAgent:
    """
    Stateless safety-stock evaluator.

    Parameters
    ----------
    recommendation_writer:
        Callable that persists a RecommendationLog to PostgreSQL (or any
        storage). Defaults to a no-op so the agent works without a live DB.
    ingredient_configs:
        Mapping of ingredient_id → IngredientConfig.  Defaults to the
        built-in operational parameters.
    cooldown_store:
        Mutable dict used as an in-process cooldown registry.  Inject a
        shared dict to persist cooldowns across agent instances.
    """

    def __init__(
        self,
        recommendation_writer: Optional[RecommendationWriter] = None,
        ingredient_configs: Optional[dict[str, IngredientConfig]] = None,
        cooldown_store: Optional[dict[str, datetime]] = None,
    ):
        self._write_recommendation = recommendation_writer or _noop_writer
        self._configs = ingredient_configs or DEFAULT_INGREDIENT_CONFIGS
        # cooldown_store: key = f"{shop_id}:{ingredient_id}", value = last alert time
        self._cooldown: dict[str, datetime] = cooldown_store if cooldown_store is not None else {}

    # ──────────────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────────────

    def evaluate(
        self,
        inventory: InventoryStateResponse,
        forecast: ForecastVector,
    ) -> OpsDecision:
        """
        Run the safety stock algorithm for a single ingredient and return
        an OpsDecision.  Call once per ingredient per evaluation cycle.
        """
        shop_id = inventory.shop_id
        ingredient_id = inventory.ingredient_id
        now = datetime.now(timezone.utc)

        cfg = self._get_config(ingredient_id)

        # ── 1. Gather inputs ──────────────────────────────────────────
        current_stock = inventory.total_remaining_grams
        brewing_qty   = inventory.active_brewing_qty_grams

        # Use the forecast window matching the cook time (pick closest horizon)
        predicted_consumption = self._select_forecast_window(forecast, cfg.cook_time_minutes)

        # ── 2. Safety stock calculation ───────────────────────────────
        # Runway = what we have right now + what's cooking - what we'll sell
        # before the cook finishes.  Brewing stock is NOT yet usable, so it
        # doesn't help with the current window, but shows we already reacted.
        target_runway = current_stock - predicted_consumption

        logger.debug(
            f"[{ingredient_id}] stock={current_stock}g brewing={brewing_qty}g "
            f"forecast={predicted_consumption}g runway={target_runway}g "
            f"safety={cfg.safety_buffer_grams}g warn={cfg.warn_buffer_grams}g"
        )

        # ── 3. Determine action ───────────────────────────────────────
        action = self._classify(target_runway, cfg)

        # ── 4. Estimate shortage time (for BREW_NOW) ──────────────────
        predicted_shortage_at: Optional[datetime] = None
        if action == DecisionAction.BREW_NOW and predicted_consumption > 0:
            # Linear extrapolation: how many minutes until stock = 0?
            rate_per_min = predicted_consumption / cfg.cook_time_minutes
            if rate_per_min > 0:
                minutes_to_zero = current_stock / rate_per_min
                predicted_shortage_at = now + timedelta(minutes=minutes_to_zero)

        # ── 5. Write recommendation log (with cooldown dedup) ─────────
        recommendation_id: Optional[UUID] = None
        if action in (DecisionAction.BREW_NOW, DecisionAction.WARN):
            if not self._is_in_cooldown(shop_id, ingredient_id, now):
                recommendation_id = self._log_recommendation(
                    shop_id=shop_id,
                    ingredient_id=ingredient_id,
                    action=action,
                    current_stock=current_stock,
                    brewing_qty=brewing_qty,
                    predicted_consumption=predicted_consumption,
                    target_runway=target_runway,
                    predicted_shortage_at=predicted_shortage_at,
                    cfg=cfg,
                    forecast=forecast,
                    now=now,
                )
                self._set_cooldown(shop_id, ingredient_id, now)
            else:
                logger.info(
                    f"[{ingredient_id}] {action.value} suppressed — within {COOLDOWN_MINUTES}m cooldown."
                )

        return OpsDecision(
            shop_id=shop_id,
            ingredient_id=ingredient_id,
            action=action,
            current_stock_grams=current_stock,
            active_brewing_grams=brewing_qty,
            predicted_consumption_grams=predicted_consumption,
            target_runway_grams=round(target_runway, 2),
            safety_buffer_grams=cfg.safety_buffer_grams,
            evaluated_at=now,
            predicted_shortage_at=predicted_shortage_at,
            recommendation_id=recommendation_id,
        )

    def evaluate_all(
        self,
        inventories: list[InventoryStateResponse],
        forecasts: list[ForecastVector],
    ) -> list[OpsDecision]:
        """
        Convenience method: evaluate a batch of ingredients for the same shop.
        Pairs inventories and forecasts by ingredient_id.
        """
        forecast_map = {f.ingredient_id: f for f in forecasts}
        decisions = []
        for inv in inventories:
            fc = forecast_map.get(inv.ingredient_id)
            if fc is None:
                logger.warning(
                    f"No forecast found for ingredient '{inv.ingredient_id}' — skipping."
                )
                continue
            decisions.append(self.evaluate(inv, fc))
        return decisions

    # ──────────────────────────────────────────────────────────────────
    # Internal helpers
    # ──────────────────────────────────────────────────────────────────

    def _get_config(self, ingredient_id: str) -> IngredientConfig:
        """Return config for ingredient, falling back to a generic default."""
        if ingredient_id in self._configs:
            return self._configs[ingredient_id]
        logger.warning(
            f"No IngredientConfig found for '{ingredient_id}'. Using generic defaults."
        )
        return IngredientConfig(
            ingredient_id=ingredient_id,
            cook_time_minutes=30,
            batch_size_grams=1000.0,
            safety_buffer_grams=100.0,
            warn_buffer_grams=300.0,
        )

    @staticmethod
    def _select_forecast_window(forecast: ForecastVector, cook_time_minutes: int) -> float:
        """
        Select the forecast horizon whose window best matches the cook time.
        • cook_time <= 30m  → use t30
        • cook_time <= 60m  → use t60
        • cook_time >  60m  → use t120
        """
        if cook_time_minutes <= 30:
            return forecast.t30_grams
        elif cook_time_minutes <= 60:
            return forecast.t60_grams
        else:
            return forecast.t120_grams

    @staticmethod
    def _classify(target_runway: float, cfg: IngredientConfig) -> DecisionAction:
        """
        Map runway value to a discrete action.

        runway < safety_buffer  → BREW_NOW  (critical)
        runway < warn_buffer    → WARN      (monitor)
        otherwise               → WAIT      (safe)
        """
        if target_runway < cfg.safety_buffer_grams:
            return DecisionAction.BREW_NOW
        elif target_runway < cfg.warn_buffer_grams:
            return DecisionAction.WARN
        return DecisionAction.WAIT

    def _is_in_cooldown(self, shop_id: UUID, ingredient_id: str, now: datetime) -> bool:
        key = f"{shop_id}:{ingredient_id}"
        last = self._cooldown.get(key)
        if last is None:
            return False
        return (now - last).total_seconds() < COOLDOWN_MINUTES * 60

    def _set_cooldown(self, shop_id: UUID, ingredient_id: str, now: datetime) -> None:
        self._cooldown[f"{shop_id}:{ingredient_id}"] = now

    def _log_recommendation(
        self,
        shop_id: UUID,
        ingredient_id: str,
        action: DecisionAction,
        current_stock: float,
        brewing_qty: float,
        predicted_consumption: float,
        target_runway: float,
        predicted_shortage_at: Optional[datetime],
        cfg: IngredientConfig,
        forecast: ForecastVector,
        now: datetime,
    ) -> UUID:
        rec_id = uuid4()
        snapshot = {
            "current_stock_grams": current_stock,
            "active_brewing_grams": brewing_qty,
            "predicted_consumption_grams": predicted_consumption,
            "target_runway_grams": round(target_runway, 2),
            "safety_buffer_grams": cfg.safety_buffer_grams,
            "warn_buffer_grams": cfg.warn_buffer_grams,
            "cook_time_minutes": cfg.cook_time_minutes,
            "forecast_t30": forecast.t30_grams,
            "forecast_t60": forecast.t60_grams,
            "forecast_t120": forecast.t120_grams,
            "school_multiplier": forecast.school_multiplier,
            "temp_multiplier": forecast.temp_multiplier,
            "rain_multiplier": forecast.rain_multiplier,
        }
        explanation = (
            f"{action.value} for {ingredient_id}: "
            f"runway {round(target_runway, 1)}g vs safety floor {cfg.safety_buffer_grams}g. "
            f"Current stock {current_stock}g, predicted demand {predicted_consumption}g "
            f"over the next {cfg.cook_time_minutes} minutes."
        )
        log = RecommendationLog(
            id=rec_id,
            shop_id=shop_id,
            created_at=now,
            ingredient_id=ingredient_id,
            action_recommended=action,
            predicted_shortage_at=predicted_shortage_at,
            explanation_text=explanation,
            model_features_snapshot=snapshot,
        )
        try:
            self._write_recommendation(log)
            logger.info(
                f"Recommendation logged: {rec_id} | {action.value} | {ingredient_id} @ shop {shop_id}"
            )
        except Exception as e:
            logger.error(f"Failed to write recommendation log: {e}", exc_info=True)
        return rec_id
