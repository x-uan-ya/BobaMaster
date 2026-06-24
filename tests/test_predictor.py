"""
Milestone 5 — PredictorAgent Test Suite
========================================
All tests are deterministic and require no external services.
"""

import sys
import os
import math
from uuid import uuid4

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))

from app.models.predictor import VelocityWindow, ForecastVector
from app.agents.predictor_agent import (
    PredictorAgent,
    _SCHOOL_MULTIPLIER,
    _HOT_WEATHER_MULTIPLIER,
    _RAIN_MULTIPLIER,
)

SHOP_ID = uuid4()
INGREDIENT = "tapioca_pearls"

# A fixed velocity window: ~10 g/min average across all windows
BASE_VELOCITY = VelocityWindow(
    ingredient_id=INGREDIENT,
    grams_per_min_10m=10.0,
    grams_per_min_30m=10.0,
    grams_per_min_60m=10.0,
)


def _agent() -> PredictorAgent:
    return PredictorAgent()


# ---------------------------------------------------------------------------
# 1. Schema validation
# ---------------------------------------------------------------------------

def test_forecast_returns_forecast_vector():
    """PredictorAgent.forecast() must return a ForecastVector instance."""
    agent = _agent()
    result = agent.forecast(
        shop_id=SHOP_ID,
        ingredient_id=INGREDIENT,
        velocity=BASE_VELOCITY,
        temp_c=24.0,
        rain_prob=0.1,
        school_in_session=False,
    )
    assert isinstance(result, ForecastVector)
    assert result.shop_id == SHOP_ID
    assert result.ingredient_id == INGREDIENT


# ---------------------------------------------------------------------------
# 2. Baseline — no multipliers active
# ---------------------------------------------------------------------------

def test_baseline_no_multipliers():
    """
    With school=False, temp 24°C, rain 0.1, no multipliers should apply.
    Expected: base_rate=10 g/min → t30=300, t60=600, t120=1200
    """
    agent = _agent()
    result = agent.forecast(
        shop_id=SHOP_ID,
        ingredient_id=INGREDIENT,
        velocity=BASE_VELOCITY,
        temp_c=24.0,
        rain_prob=0.1,
        school_in_session=False,
        is_cold_drink_ingredient=True,
    )
    assert result.t30_grams == pytest_approx(300.0)
    assert result.t60_grams == pytest_approx(600.0)
    assert result.t120_grams == pytest_approx(1200.0)
    assert result.school_multiplier == 1.0
    assert result.temp_multiplier == 1.0
    assert result.rain_multiplier == 1.0


# ---------------------------------------------------------------------------
# 3. School session multiplier
# ---------------------------------------------------------------------------

def test_school_in_session_boosts_forecast():
    """school_in_session=True must multiply demand by _SCHOOL_MULTIPLIER."""
    agent = _agent()
    result = agent.forecast(
        shop_id=SHOP_ID,
        ingredient_id=INGREDIENT,
        velocity=BASE_VELOCITY,
        temp_c=20.0,
        rain_prob=0.1,
        school_in_session=True,
        is_cold_drink_ingredient=False,   # suppress other multipliers
    )
    expected_t60 = 10.0 * 60 * _SCHOOL_MULTIPLIER
    assert result.school_multiplier == _SCHOOL_MULTIPLIER
    assert math.isclose(result.t60_grams, expected_t60, rel_tol=1e-6)


def test_no_school_multiplier_outside_term():
    """school_in_session=False must leave school_multiplier at 1.0."""
    agent = _agent()
    result = agent.forecast(
        shop_id=SHOP_ID,
        ingredient_id=INGREDIENT,
        velocity=BASE_VELOCITY,
        temp_c=20.0,
        rain_prob=0.1,
        school_in_session=False,
    )
    assert result.school_multiplier == 1.0


# ---------------------------------------------------------------------------
# 4. Hot weather multiplier (cold drink ingredients)
# ---------------------------------------------------------------------------

def test_hot_weather_boosts_cold_drink_ingredient():
    """temp_c > 28 on a cold drink ingredient must apply hot-weather multiplier."""
    agent = _agent()
    result = agent.forecast(
        shop_id=SHOP_ID,
        ingredient_id=INGREDIENT,
        velocity=BASE_VELOCITY,
        temp_c=32.0,
        rain_prob=0.1,
        school_in_session=False,
        is_cold_drink_ingredient=True,
    )
    assert result.temp_multiplier == _HOT_WEATHER_MULTIPLIER
    expected_t60 = 10.0 * 60 * _HOT_WEATHER_MULTIPLIER
    assert math.isclose(result.t60_grams, expected_t60, rel_tol=1e-6)


def test_hot_weather_does_not_boost_hot_drink_ingredient():
    """temp_c > 28 must NOT apply multiplier to hot drink ingredients."""
    agent = _agent()
    result = agent.forecast(
        shop_id=SHOP_ID,
        ingredient_id="black_tea_hot",
        velocity=BASE_VELOCITY,
        temp_c=35.0,
        rain_prob=0.1,
        school_in_session=False,
        is_cold_drink_ingredient=False,
        is_hot_drink_ingredient=True,
    )
    assert result.temp_multiplier == 1.0


def test_mild_temp_no_boost():
    """temp_c <= 28 must NOT apply the hot-weather multiplier."""
    agent = _agent()
    result = agent.forecast(
        shop_id=SHOP_ID,
        ingredient_id=INGREDIENT,
        velocity=BASE_VELOCITY,
        temp_c=28.0,    # exactly at threshold — should NOT trigger (strict >)
        rain_prob=0.1,
        school_in_session=False,
        is_cold_drink_ingredient=True,
    )
    assert result.temp_multiplier == 1.0


# ---------------------------------------------------------------------------
# 5. Rain multiplier (hot drink ingredients)
# ---------------------------------------------------------------------------

def test_rain_boosts_hot_drink_ingredient():
    """rain_prob > 0.6 on a hot drink ingredient must apply rain multiplier."""
    agent = _agent()
    result = agent.forecast(
        shop_id=SHOP_ID,
        ingredient_id="hot_tea_base",
        velocity=BASE_VELOCITY,
        temp_c=20.0,
        rain_prob=0.75,
        school_in_session=False,
        is_cold_drink_ingredient=False,
        is_hot_drink_ingredient=True,
    )
    assert result.rain_multiplier == _RAIN_MULTIPLIER
    expected_t60 = 10.0 * 60 * _RAIN_MULTIPLIER
    assert math.isclose(result.t60_grams, expected_t60, rel_tol=1e-6)


def test_rain_does_not_boost_cold_drink_ingredient():
    """rain_prob > 0.6 must NOT apply rain multiplier to cold drink ingredients."""
    agent = _agent()
    result = agent.forecast(
        shop_id=SHOP_ID,
        ingredient_id=INGREDIENT,
        velocity=BASE_VELOCITY,
        temp_c=20.0,
        rain_prob=0.9,
        school_in_session=False,
        is_cold_drink_ingredient=True,
        is_hot_drink_ingredient=False,
    )
    assert result.rain_multiplier == 1.0


# ---------------------------------------------------------------------------
# 6. Combined multipliers stack multiplicatively
# ---------------------------------------------------------------------------

def test_combined_multipliers_stack():
    """
    school=True + temp=32°C on a cold drink ingredient should stack:
    combined = _SCHOOL_MULTIPLIER * _HOT_WEATHER_MULTIPLIER
    """
    agent = _agent()
    result = agent.forecast(
        shop_id=SHOP_ID,
        ingredient_id=INGREDIENT,
        velocity=BASE_VELOCITY,
        temp_c=32.0,
        rain_prob=0.1,
        school_in_session=True,
        is_cold_drink_ingredient=True,
    )
    combined = _SCHOOL_MULTIPLIER * _HOT_WEATHER_MULTIPLIER
    expected_t30 = 10.0 * 30 * combined
    assert math.isclose(result.t30_grams, expected_t30, rel_tol=1e-6)
    assert result.school_multiplier == _SCHOOL_MULTIPLIER
    assert result.temp_multiplier == _HOT_WEATHER_MULTIPLIER


# ---------------------------------------------------------------------------
# 7. Horizon scaling — t120 = 4× t30 at steady rate
# ---------------------------------------------------------------------------

def test_horizon_scaling():
    """t120 must equal 4× t30 when rate is constant."""
    agent = _agent()
    result = agent.forecast(
        shop_id=SHOP_ID,
        ingredient_id=INGREDIENT,
        velocity=BASE_VELOCITY,
        temp_c=20.0,
        rain_prob=0.1,
        school_in_session=False,
    )
    assert math.isclose(result.t120_grams, result.t30_grams * 4, rel_tol=1e-6)


# ---------------------------------------------------------------------------
# 8. Non-uniform velocity windows are averaged correctly
# ---------------------------------------------------------------------------

def test_non_uniform_velocity_averaging():
    """
    Base rate must be the simple average of the three velocity windows.
    Velocity: 6, 9, 12 → avg = 9 g/min
    Expected t60 = 9 × 60 = 540g (no multipliers)
    """
    velocity = VelocityWindow(
        ingredient_id=INGREDIENT,
        grams_per_min_10m=6.0,
        grams_per_min_30m=9.0,
        grams_per_min_60m=12.0,
    )
    agent = _agent()
    result = agent.forecast(
        shop_id=SHOP_ID,
        ingredient_id=INGREDIENT,
        velocity=velocity,
        temp_c=20.0,
        rain_prob=0.1,
        school_in_session=False,
        is_cold_drink_ingredient=False,
    )
    assert math.isclose(result.t60_grams, 540.0, rel_tol=1e-6)


# ---------------------------------------------------------------------------
# 9. Zero velocity returns zero forecast
# ---------------------------------------------------------------------------

def test_zero_velocity_zero_forecast():
    """Zero velocity across all windows must produce a zero forecast."""
    zero_velocity = VelocityWindow(
        ingredient_id=INGREDIENT,
        grams_per_min_10m=0.0,
        grams_per_min_30m=0.0,
        grams_per_min_60m=0.0,
    )
    agent = _agent()
    result = agent.forecast(
        shop_id=SHOP_ID,
        ingredient_id=INGREDIENT,
        velocity=zero_velocity,
        school_in_session=True,  # multipliers present but rate is 0
        temp_c=35.0,
        rain_prob=0.9,
        is_cold_drink_ingredient=True,
        is_hot_drink_ingredient=True,
    )
    assert result.t30_grams == 0.0
    assert result.t60_grams == 0.0
    assert result.t120_grams == 0.0


# ---------------------------------------------------------------------------
# Helpers — mimic pytest.approx without importing it explicitly
# (pytest is available, so we use it properly below)
# ---------------------------------------------------------------------------

def pytest_approx(value, rel=1e-6):
    """Thin wrapper so test assertions read cleanly."""
    import pytest
    return pytest.approx(value, rel=rel)
