"""
Pydantic schemas for the OpsDeciderAgent (Milestone 6).
"""
from __future__ import annotations

from enum import Enum
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional


# ──────────────────────────────────────────────────────────────────────────────
# Enums
# ──────────────────────────────────────────────────────────────────────────────

class DecisionAction(str, Enum):
    BREW_NOW = "BREW_NOW"   # Stock will run out within the cook window → start now
    WARN     = "WARN"       # Stock is healthy but trending low — monitor closely
    WAIT     = "WAIT"       # Runway is sufficient — no action required


# ──────────────────────────────────────────────────────────────────────────────
# Per-Ingredient Configuration
# ──────────────────────────────────────────────────────────────────────────────

class IngredientConfig(BaseModel):
    """Operational parameters for a single ingredient."""
    ingredient_id: str
    cook_time_minutes: int = Field(..., gt=0, description="Minutes from start to ready-to-use")
    batch_size_grams: float = Field(..., gt=0, description="Standard batch weight produced per cook")
    safety_buffer_grams: float = Field(..., ge=0, description="Minimum target stock above zero-point")
    warn_buffer_grams: float = Field(..., ge=0, description="Stock level that triggers a WARN (above safety_buffer)")


# ──────────────────────────────────────────────────────────────────────────────
# Decision Output
# ──────────────────────────────────────────────────────────────────────────────

class OpsDecision(BaseModel):
    """A single operational decision for one ingredient at one shop."""
    shop_id: UUID
    ingredient_id: str
    action: DecisionAction
    current_stock_grams: float = Field(..., description="Total available stock right now")
    active_brewing_grams: float = Field(0.0, description="Stock currently being cooked (not yet usable)")
    predicted_consumption_grams: float = Field(..., description="Expected demand during cook window")
    target_runway_grams: float = Field(..., description="current_stock + brewing - predicted_consumption")
    safety_buffer_grams: float
    evaluated_at: datetime
    predicted_shortage_at: Optional[datetime] = Field(
        None, description="Estimated time stock will hit zero (set when BREW_NOW)"
    )
    recommendation_id: Optional[UUID] = Field(
        None, description="ID written to recommendation_logs table (if BREW_NOW/WARN)"
    )


class ActiveAlertsResponse(BaseModel):
    """Response payload for GET /api/v1/operations/decisions/{shop_id}."""
    shop_id: UUID
    evaluated_at: datetime
    decisions: list[OpsDecision]


# ──────────────────────────────────────────────────────────────────────────────
# Recommendation Log (mirrors DB schema for in-memory testing)
# ──────────────────────────────────────────────────────────────────────────────

class RecommendationLog(BaseModel):
    """In-memory representation of a recommendation_logs row."""
    id: UUID
    shop_id: UUID
    created_at: datetime
    ingredient_id: str
    action_recommended: DecisionAction
    predicted_shortage_at: Optional[datetime]
    explanation_text: str
    model_features_snapshot: dict
