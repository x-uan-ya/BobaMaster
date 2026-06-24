"""
Pydantic schemas for the DispatcherAgent (Milestone 7).
"""
from __future__ import annotations

from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional

from app.models.ops_decider import DecisionAction


# ──────────────────────────────────────────────────────────────────────────────
# LLM output schema
# ──────────────────────────────────────────────────────────────────────────────

class LLMExplanation(BaseModel):
    """Structured output requested from Gemini."""
    action_string: str = Field(
        ...,
        description="Short imperative phrase for the KDS button label, e.g. 'Start Cooking Pearls Now'",
    )
    explanation_text: str = Field(
        ...,
        description=(
            "Concise 1–3 sentence operational justification staff can read at a glance. "
            "Must reference specific numbers (stock level, forecast, time window)."
        ),
    )


# ──────────────────────────────────────────────────────────────────────────────
# WebSocket broadcast payload
# ──────────────────────────────────────────────────────────────────────────────

class AlertPayload(BaseModel):
    """Input data fed to the DispatcherAgent for a single decision event."""
    shop_id: UUID
    ingredient_id: str
    action: DecisionAction
    current_stock_grams: float
    active_brewing_grams: float
    predicted_consumption_grams: float
    target_runway_grams: float
    cook_time_minutes: int
    temp_c: float = 24.0
    rain_prob: float = 0.1
    school_in_session: bool = True
    predicted_shortage_at: Optional[datetime] = None
    recommendation_id: Optional[UUID] = None


class DispatchMessage(BaseModel):
    """
    Broadcast payload pushed over WebSocket to all connected KDS clients.
    Contains both the machine-readable decision fields and the LLM explanation.
    """
    event_type: str = "recommendation_alert"
    shop_id: UUID
    ingredient_id: str
    action: DecisionAction
    action_string: str
    explanation_text: str
    current_stock_grams: float
    predicted_consumption_grams: float
    target_runway_grams: float
    recommendation_id: Optional[UUID] = None
    predicted_shortage_at: Optional[datetime] = None
    dispatched_at: datetime
    llm_used: bool = Field(True, description="False when fallback explanation was used")
