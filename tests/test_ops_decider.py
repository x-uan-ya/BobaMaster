"""
Milestone 6 — OpsDeciderAgent Test Suite
=========================================
All tests are deterministic and require no external services (no Redis, no DB).
PostgreSQL writes are intercepted by an in-memory capture list.
"""

import sys
import os
import math
from uuid import uuid4
from datetime import datetime, timezone, timedelta
from typing import Optional

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))

from app.models.ops_decider import (
    DecisionAction,
    IngredientConfig,
    OpsDecision,
    RecommendationLog,
)
from app.models.predictor import ForecastVector
from app.models.inventory import InventoryStateResponse
from app.agents.ops_decider_agent import OpsDeciderAgent, COOLDOWN_MINUTES

# ──────────────────────────────────────────────────────────────────────────────
# Test fixtures / factories
# ──────────────────────────────────────────────────────────────────────────────

SHOP_ID = uuid4()
INGREDIENT = "tapioca_pearls"

# Operational config matching the default pearls parameters
PEARLS_CFG = IngredientConfig(
    ingredient_id=INGREDIENT,
    cook_time_minutes=50,
    batch_size_grams=2000.0,
    safety_buffer_grams=200.0,
    warn_buffer_grams=600.0,
)

INGREDIENT_CONFIGS = {INGREDIENT: PEARLS_CFG}


def _inventory(
    total_grams: float,
    brewing_grams: float = 0.0,
    ingredient_id: str = INGREDIENT,
) -> InventoryStateResponse:
    """Build a minimal InventoryStateResponse for testing."""
    now = datetime.now(timezone.utc)
    return InventoryStateResponse(
        shop_id=SHOP_ID,
        ingredient_id=ingredient_id,
        total_remaining_grams=total_grams,
        active_batches=[],
        active_brewing_qty_grams=brewing_grams,
        nearest_expiry=now + timedelta(hours=3),
    )


def _forecast(
    t30: float = 100.0,
    t60: float = 200.0,
    t120: float = 400.0,
    ingredient_id: str = INGREDIENT,
) -> ForecastVector:
    return ForecastVector(
        shop_id=SHOP_ID,
        ingredient_id=ingredient_id,
        school_multiplier=1.0,
        temp_multiplier=1.0,
        rain_multiplier=1.0,
        t30_grams=t30,
        t60_grams=t60,
        t120_grams=t120,
    )


def _make_agent(capture: Optional[list] = None) -> OpsDeciderAgent:
    """Create an OpsDeciderAgent that writes logs to a list instead of PostgreSQL."""
    captured = capture if capture is not None else []

    def _writer(log: RecommendationLog) -> None:
        captured.append(log)

    return OpsDeciderAgent(
        recommendation_writer=_writer,
        ingredient_configs=INGREDIENT_CONFIGS,
    )


# ──────────────────────────────────────────────────────────────────────────────
# 1. Decision action classification
# ──────────────────────────────────────────────────────────────────────────────

def test_brew_now_when_stock_below_safety_buffer():
    """
    Milestone spec: stock=400g, forecast=1000g over 60m window.
    Pearls cook time = 50m → agent uses t60 horizon.
    runway = 400 - 2000 = -1600 < safety_buffer(200) → BREW_NOW
    """
    agent = _make_agent()
    inv = _inventory(400.0)
    fc  = _forecast(t60=2000.0)

    decision = agent.evaluate(inv, fc)

    assert decision.action == DecisionAction.BREW_NOW
    assert decision.current_stock_grams == 400.0
    assert decision.predicted_consumption_grams == 2000.0


def test_warn_when_stock_between_safety_and_warn_buffer():
    """
    runway = 800 - 500 = 300 → between safety(200) and warn(600) → WARN
    """
    agent = _make_agent()
    inv = _inventory(800.0)
    fc  = _forecast(t60=500.0)

    decision = agent.evaluate(inv, fc)

    assert decision.action == DecisionAction.WARN


def test_wait_when_stock_above_warn_buffer():
    """
    runway = 3000 - 100 = 2900 > warn(600) → WAIT
    """
    agent = _make_agent()
    inv = _inventory(3000.0)
    fc  = _forecast(t60=100.0)

    decision = agent.evaluate(inv, fc)

    assert decision.action == DecisionAction.WAIT


# ──────────────────────────────────────────────────────────────────────────────
# 2. Return type & field integrity
# ──────────────────────────────────────────────────────────────────────────────

def test_decision_returns_ops_decision_model():
    """evaluate() must return an OpsDecision Pydantic instance."""
    agent = _make_agent()
    decision = agent.evaluate(_inventory(1000.0), _forecast())

    assert isinstance(decision, OpsDecision)
    assert decision.shop_id == SHOP_ID
    assert decision.ingredient_id == INGREDIENT


def test_target_runway_calculated_correctly():
    """target_runway = current_stock - predicted_consumption (cook window = t60 for 50m cook)."""
    agent = _make_agent()
    inv = _inventory(1500.0)
    fc  = _forecast(t60=800.0)

    decision = agent.evaluate(inv, fc)

    assert math.isclose(decision.target_runway_grams, 1500.0 - 800.0, rel_tol=1e-6)


# ──────────────────────────────────────────────────────────────────────────────
# 3. Recommendation log capture
# ──────────────────────────────────────────────────────────────────────────────

def test_brew_now_writes_recommendation_log():
    """A BREW_NOW decision must write a RecommendationLog and return its ID."""
    captured: list[RecommendationLog] = []
    agent = _make_agent(captured)
    inv = _inventory(400.0)
    fc  = _forecast(t60=2000.0)

    decision = agent.evaluate(inv, fc)

    assert decision.action == DecisionAction.BREW_NOW
    assert decision.recommendation_id is not None
    assert len(captured) == 1
    assert captured[0].action_recommended == DecisionAction.BREW_NOW
    assert captured[0].shop_id == SHOP_ID


def test_wait_does_not_write_recommendation_log():
    """A WAIT decision must NOT write a recommendation log."""
    captured: list[RecommendationLog] = []
    agent = _make_agent(captured)
    inv = _inventory(5000.0)
    fc  = _forecast(t60=50.0)

    decision = agent.evaluate(inv, fc)

    assert decision.action == DecisionAction.WAIT
    assert decision.recommendation_id is None
    assert len(captured) == 0


# ──────────────────────────────────────────────────────────────────────────────
# 4. Cooldown deduplication
# ──────────────────────────────────────────────────────────────────────────────

def test_cooldown_prevents_duplicate_brew_now_within_window():
    """
    Two consecutive BREW_NOW evaluations within COOLDOWN_MINUTES must only
    produce ONE recommendation log entry.
    """
    captured: list[RecommendationLog] = []
    shared_cooldown: dict = {}

    def _writer(log: RecommendationLog) -> None:
        captured.append(log)

    agent = OpsDeciderAgent(
        recommendation_writer=_writer,
        ingredient_configs=INGREDIENT_CONFIGS,
        cooldown_store=shared_cooldown,
    )

    inv = _inventory(400.0)
    fc  = _forecast(t60=2000.0)

    d1 = agent.evaluate(inv, fc)
    d2 = agent.evaluate(inv, fc)   # within cooldown window

    assert d1.action == DecisionAction.BREW_NOW
    assert d2.action == DecisionAction.BREW_NOW     # still BREW_NOW action
    assert len(captured) == 1                        # but only ONE DB write
    assert d1.recommendation_id is not None
    assert d2.recommendation_id is None             # suppressed


def test_cooldown_resets_after_window_expires():
    """
    After the cooldown window, a new recommendation should be written.
    We simulate this by backdating the cooldown timestamp.
    """
    captured: list[RecommendationLog] = []
    shared_cooldown: dict = {}

    def _writer(log: RecommendationLog) -> None:
        captured.append(log)

    agent = OpsDeciderAgent(
        recommendation_writer=_writer,
        ingredient_configs=INGREDIENT_CONFIGS,
        cooldown_store=shared_cooldown,
    )

    inv = _inventory(400.0)
    fc  = _forecast(t60=2000.0)

    # First evaluation — fires normally
    agent.evaluate(inv, fc)
    assert len(captured) == 1

    # Backdate the cooldown entry past the window
    cooldown_key = f"{SHOP_ID}:{INGREDIENT}"
    shared_cooldown[cooldown_key] = (
        datetime.now(timezone.utc) - timedelta(minutes=COOLDOWN_MINUTES + 1)
    )

    # Second evaluation — cooldown expired, should fire again
    agent.evaluate(inv, fc)
    assert len(captured) == 2


# ──────────────────────────────────────────────────────────────────────────────
# 5. Forecast horizon selection
# ──────────────────────────────────────────────────────────────────────────────

def test_forecast_horizon_uses_t30_for_fast_cook():
    """Ingredients with cook_time <= 30 minutes must use the t30 forecast window."""
    fast_cfg = IngredientConfig(
        ingredient_id="matcha_powder",
        cook_time_minutes=10,
        batch_size_grams=500.0,
        safety_buffer_grams=50.0,
        warn_buffer_grams=150.0,
    )
    agent = OpsDeciderAgent(
        ingredient_configs={"matcha_powder": fast_cfg},
    )
    inv = InventoryStateResponse(
        shop_id=SHOP_ID,
        ingredient_id="matcha_powder",
        total_remaining_grams=200.0,
        active_batches=[],
        active_brewing_qty_grams=0.0,
        nearest_expiry=datetime.now(timezone.utc) + timedelta(hours=2),
    )
    # t30=300 > stock(200) → runway = -100 < safety(50) → BREW_NOW
    # t60=600 would give runway = -400, same action, but we verify via
    # predicted_consumption matching t30.
    fc = ForecastVector(
        shop_id=SHOP_ID, ingredient_id="matcha_powder",
        school_multiplier=1.0, temp_multiplier=1.0, rain_multiplier=1.0,
        t30_grams=300.0, t60_grams=600.0, t120_grams=1200.0,
    )
    decision = agent.evaluate(inv, fc)

    # predicted_consumption must equal t30 (10m cook → t30 window)
    assert decision.predicted_consumption_grams == 300.0
