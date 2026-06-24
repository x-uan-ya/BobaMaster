"""Feedback API endpoint test suite."""

import sys
import os
from uuid import uuid4
from datetime import date
from unittest.mock import patch

from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))

from app.main import app

SHOP_ID = str(uuid4())


@patch("app.api.feedback._feedback_agent.run_for_date")
def test_feedback_report_endpoint_returns_report(mock_run_for_date):
    mock_run_for_date.return_value = {
        "shop_id": SHOP_ID,
        "date": date(2026, 6, 22),
        "total_transactions": 10,
        "total_waste_grams": 400.0,
        "total_prepared_grams": 2000.0,
        "mape": 0.12,
        "acceptance_rate": 0.6,
        "ignored_rate": 0.3,
        "delayed_rate": 0.1,
        "pearl_waste_ratio": 0.2,
        "stockout_minutes": 5,
        "pearl_safety_factor_before": 1.2,
        "pearl_safety_factor_after": 1.25,
        "updated": True,
        "generated_at": "2026-06-23T00:00:00+00:00",
    }

    client = TestClient(app)
    response = client.get(f"/api/v1/feedback/report/{SHOP_ID}?target_date=2026-06-22")

    assert response.status_code == 200
    payload = response.json()
    assert payload["shop_id"] == SHOP_ID
    assert payload["date"] == "2026-06-22"
    assert payload["total_transactions"] == 10
    assert payload["pearl_safety_factor_after"] == 1.25
    assert payload["updated"] is True
