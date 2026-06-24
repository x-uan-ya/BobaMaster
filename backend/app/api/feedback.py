"""Feedback API Router — Milestone 10.

Provides a daily feedback report endpoint that runs the FeedbackAgent
against historical logs and tuning settings.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.agents.feedback import FeedbackAgent
from app.models.feedback import FeedbackReportResponse

logger = logging.getLogger("BobaMaster.API.Feedback")
router = APIRouter()

_feedback_agent = FeedbackAgent()


@router.get(
    "/report/{shop_id}",
    response_model=FeedbackReportResponse,
    status_code=status.HTTP_200_OK,
    summary="Run daily feedback audit",
    description=(
        "Runs the feedback analytics pipeline for a shop and returns a daily "
        "audit report including forecast accuracy, waste ratios, and safety "
        "factor tuning recommendations."
    ),
)
async def get_feedback_report(
    shop_id: UUID,
    target_date: date | None = Query(
        default=None,
        description="Date to analyze in UTC. Defaults to yesterday.",
    ),
):
    try:
        if target_date is None:
            target_date = (datetime.now(timezone.utc) - timedelta(days=1)).date()

        report = _feedback_agent.run_for_date(str(shop_id), target_date)
        payload = report if isinstance(report, dict) else report.__dict__
        return FeedbackReportResponse.model_validate(payload)
    except Exception as e:
        logger.error(f"feedback report error shop={shop_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
