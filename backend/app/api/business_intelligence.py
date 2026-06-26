"""
Business Intelligence API Router — Milestone 10.5

Provides insights endpoints for the manager dashboard:
  - GET /api/v1/business/insights/{shop_id}
  - GET /api/v1/business/peak-windows/{shop_id}
  - GET /api/v1/business/revenue-forecast/{shop_id}
"""

from __future__ import annotations

import logging
from uuid import UUID
from datetime import date

from fastapi import APIRouter, HTTPException, status, Query

from app.agents.business_agent import get_business_agent, BusinessInsight

logger = logging.getLogger("BobaMaster.API.BusinessIntelligence")
router = APIRouter()


@router.get(
    "/insights/{shop_id}",
    response_model=BusinessInsight,
    status_code=status.HTTP_200_OK,
    summary="Get comprehensive business intelligence",
    description=(
        "Generates actionable insights for store managers: peak demand windows, "
        "revenue estimates, waste trends, drink popularity, and inventory optimization "
        "recommendations. Works in demo mode with synthetic data."
    ),
)
async def get_business_insights(shop_id: UUID):
    """Get comprehensive business intelligence for a shop."""
    try:
        agent = get_business_agent()
        insights = agent.get_insights(shop_id)
        return insights
    except Exception as e:
        logger.error(f"Error generating business insights for shop {shop_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate insights: {str(e)}",
        )


@router.get(
    "/revenue-forecast/{shop_id}",
    status_code=status.HTTP_200_OK,
    summary="Get daily revenue forecast",
    description="Forecasts today's revenue based on current sales pace and peak window projections.",
)
async def get_revenue_forecast(
    shop_id: UUID,
    target_date: date | None = Query(
        None, description="Date to forecast (defaults to today)"
    ),
):
    """Get revenue forecast for a specific date."""
    try:
        agent = get_business_agent()
        insights = agent.get_insights(shop_id)

        # Calculate projected revenue with current pace
        current_revenue = insights.today_revenue_estimate
        current_hour = insights.generated_at.hour

        # Estimate remaining hours until close (9 PM)
        hours_remaining = max(0, 21 - current_hour)
        avg_per_hour = current_revenue / max(1, current_hour)
        projected_total = current_revenue + (avg_per_hour * hours_remaining)

        return {
            "shop_id": str(shop_id),
            "date": target_date or insights.generated_at.date(),
            "current_revenue": current_revenue,
            "current_hour": current_hour,
            "hours_remaining": hours_remaining,
            "avg_revenue_per_hour": avg_per_hour,
            "projected_total_revenue": projected_total,
            "confidence": 0.85 if hours_remaining > 2 else 0.95,
        }
    except Exception as e:
        logger.error(f"Error forecasting revenue for shop {shop_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to forecast revenue: {str(e)}",
        )


@router.get(
    "/peak-windows/{shop_id}",
    status_code=status.HTTP_200_OK,
    summary="Get identified peak demand windows",
    description="Returns historical peak hours when demand is highest.",
)
async def get_peak_windows(shop_id: UUID):
    """Get peak demand windows for strategic planning."""
    try:
        agent = get_business_agent()
        insights = agent.get_insights(shop_id)

        return {
            "shop_id": str(shop_id),
            "peak_windows": [
                {
                    "start_hour": w.start_hour,
                    "end_hour": w.end_hour,
                    "avg_cups_per_minute": w.avg_cups_per_minute,
                    "confidence": w.confidence,
                    "label": f"{w.start_hour:02d}:00 - {w.end_hour:02d}:00",
                }
                for w in insights.peak_windows
            ],
            "generated_at": insights.generated_at,
        }
    except Exception as e:
        logger.error(f"Error fetching peak windows for shop {shop_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch peak windows: {str(e)}",
        )
