"""
Pydantic schemas for the PredictorAgent demand forecasting engine.
"""
from pydantic import BaseModel, Field
from uuid import UUID
from typing import Optional


class VelocityWindow(BaseModel):
    """
    Recent sales velocity readings for an ingredient, measured in grams/minute
    over three look-back windows.
    """
    ingredient_id: str = Field(..., description="Ingredient identifier (e.g. 'tapioca_pearls')")
    grams_per_min_10m: float = Field(..., ge=0.0, description="Average consumption rate over the last 10 minutes")
    grams_per_min_30m: float = Field(..., ge=0.0, description="Average consumption rate over the last 30 minutes")
    grams_per_min_60m: float = Field(..., ge=0.0, description="Average consumption rate over the last 60 minutes")


class ForecastVector(BaseModel):
    """
    Projected ingredient demand over three forward-looking time horizons.
    All values are in grams (or ml for liquid ingredients).
    """
    shop_id: UUID
    ingredient_id: str
    # Multipliers that were applied (for auditability)
    school_multiplier: float = Field(1.0, description="Demand boost applied for school session")
    temp_multiplier: float = Field(1.0, description="Demand boost applied for high temperature")
    rain_multiplier: float = Field(1.0, description="Demand boost applied for rainy weather")
    # Core forecast output
    t30_grams: float = Field(..., ge=0.0, description="Projected demand in the next 30 minutes (grams/ml)")
    t60_grams: float = Field(..., ge=0.0, description="Projected demand in the next 60 minutes (grams/ml)")
    t120_grams: float = Field(..., ge=0.0, description="Projected demand in the next 120 minutes (grams/ml)")


class ForecastRequest(BaseModel):
    """Request body for a forecast computation."""
    shop_id: UUID
    ingredient_id: str
    velocity: VelocityWindow
    # Optional context overrides — if omitted, ContextAgent will be queried
    temp_c: Optional[float] = None
    rain_prob: Optional[float] = None
    school_in_session: Optional[bool] = None
    is_cold_drink_ingredient: bool = Field(
        True,
        description="True for cold drink ingredients (e.g. pearls, cold tea) to apply heat multiplier",
    )
    is_hot_drink_ingredient: bool = Field(
        False,
        description="True for hot drink ingredients (e.g. hot tea base) to apply rain multiplier",
    )
