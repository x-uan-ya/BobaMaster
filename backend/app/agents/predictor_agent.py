"""
PredictorAgent — Numerical Demand Forecasting Engine (Milestone 5)

Generates ingredient demand projections for 30m, 60m, and 120m horizons using
a linear-regression heuristic adjusted by contextual multipliers:

  - school_in_session  → +35% (school rush)
  - temp_c > 28°C      → +25% on cold drink ingredients
  - rain_prob > 0.6    → +20% on hot drink ingredients

The class is intentionally modular: the _base_forecast() method can later be
replaced by a LightGBM or other ML model without touching the multiplier logic
or the public interface.
"""

import logging
from uuid import UUID
from typing import Optional

from app.models.predictor import ForecastVector, VelocityWindow
from app.models.context import ContextVector

logger = logging.getLogger("BobaMaster.PredictorAgent")

# ──────────────────────────────────────────────────────────────────────────────
# Tunable constants
# ──────────────────────────────────────────────────────────────────────────────
_SCHOOL_MULTIPLIER = 1.35
_HOT_WEATHER_MULTIPLIER = 1.25   # applied to cold drinks when temp_c > 28°C
_RAIN_MULTIPLIER = 1.20           # applied to hot drinks when rain_prob > 0.6

_HOT_WEATHER_THRESHOLD_C = 28.0
_RAIN_PROBABILITY_THRESHOLD = 0.60


class PredictorAgent:
    """
    Stateless demand forecasting agent.

    Usage::

        agent = PredictorAgent()
        forecast = agent.forecast(
            shop_id=shop_id,
            velocity=velocity_window,
            context=context_vector,
            ingredient_id="tapioca_pearls",
            is_cold_drink_ingredient=True,
        )
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def forecast(
        self,
        shop_id: UUID,
        ingredient_id: str,
        velocity: VelocityWindow,
        context: Optional[ContextVector] = None,
        # Allow callers to pass scalar context values directly (no ContextVector needed)
        temp_c: Optional[float] = None,
        rain_prob: Optional[float] = None,
        school_in_session: Optional[bool] = None,
        is_cold_drink_ingredient: bool = True,
        is_hot_drink_ingredient: bool = False,
    ) -> ForecastVector:
        """
        Compute a demand forecast vector for a single ingredient.

        Context values can be supplied either via a ``ContextVector`` instance
        or as scalar keyword arguments.  Scalar kwargs take precedence over the
        ContextVector if both are provided.

        Returns a :class:`ForecastVector` with projected demand in grams/ml for
        the 30m, 60m, and 120m horizons.
        """
        # Resolve context scalars (kwargs override ContextVector)
        resolved_temp_c = temp_c if temp_c is not None else (
            context.weather.temp_c if context else 24.0
        )
        resolved_rain_prob = rain_prob if rain_prob is not None else (
            context.weather.rain_prob if context else 0.1
        )
        resolved_school = school_in_session if school_in_session is not None else (
            context.calendar.is_school_day if context else True
        )

        # ── 1. Base forecast (grams/min) ──────────────────────────────
        base_rate = self._base_forecast(velocity)  # grams per minute

        # ── 2. Determine multipliers ──────────────────────────────────
        school_mult = _SCHOOL_MULTIPLIER if resolved_school else 1.0

        temp_mult = (
            _HOT_WEATHER_MULTIPLIER
            if is_cold_drink_ingredient and resolved_temp_c > _HOT_WEATHER_THRESHOLD_C
            else 1.0
        )

        rain_mult = (
            _RAIN_MULTIPLIER
            if is_hot_drink_ingredient and resolved_rain_prob > _RAIN_PROBABILITY_THRESHOLD
            else 1.0
        )

        combined_mult = school_mult * temp_mult * rain_mult

        logger.debug(
            f"Forecast [{ingredient_id}]: base_rate={base_rate:.3f} g/min, "
            f"school_mult={school_mult}, temp_mult={temp_mult}, rain_mult={rain_mult}"
        )

        # ── 3. Project over horizons ──────────────────────────────────
        t30 = round(base_rate * 30 * combined_mult, 2)
        t60 = round(base_rate * 60 * combined_mult, 2)
        t120 = round(base_rate * 120 * combined_mult, 2)

        return ForecastVector(
            shop_id=shop_id,
            ingredient_id=ingredient_id,
            school_multiplier=school_mult,
            temp_multiplier=temp_mult,
            rain_multiplier=rain_mult,
            t30_grams=t30,
            t60_grams=t60,
            t120_grams=t120,
        )

    # ------------------------------------------------------------------
    # Internal — base rate calculation (swap this for ML model later)
    # ------------------------------------------------------------------

    @staticmethod
    def _base_forecast(velocity: VelocityWindow) -> float:
        """
        Heuristic base rate in grams-per-minute derived from the three
        velocity windows using an equally-weighted average.

        This is intentionally simple so it can be replaced by a LightGBM
        inference call without changing the surrounding code.
        """
        avg = (
            velocity.grams_per_min_10m
            + velocity.grams_per_min_30m
            + velocity.grams_per_min_60m
        ) / 3.0
        return max(avg, 0.0)  # safety: never negative
