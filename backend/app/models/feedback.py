"""
Pydantic schemas for the FeedbackAgent audit reports.
"""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class FeedbackReportResponse(BaseModel):
    """Response model for daily feedback audit reports."""

    shop_id: UUID
    date: date
    total_transactions: int
    total_waste_grams: float
    total_prepared_grams: float
    mape: float
    acceptance_rate: float
    ignored_rate: float
    delayed_rate: float
    pearl_waste_ratio: float
    stockout_minutes: int
    pearl_safety_factor_before: float
    pearl_safety_factor_after: float
    updated: bool
    generated_at: datetime
    demo_mode: bool = False   # True when PostgreSQL was unavailable
