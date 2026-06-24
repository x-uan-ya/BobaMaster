"""FeedbackAgent — Closed-loop daily audit test suite."""

import sys
import os
from uuid import uuid4
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))

from app.agents.feedback import FeedbackAgent, FeedbackReport

SHOP_ID = str(uuid4())


def _fake_cursor_factory(responses):
    class FakeCursor:
        def __init__(self, responses):
            self._responses = responses
            self._current_response = []
            self._execute_count = 0
            self._row_index = 0

        def execute(self, *_args, **_kwargs):
            self._current_response = self._responses[self._execute_count]
            self._execute_count += 1
            self._row_index = 0

        def fetchone(self):
            if self._row_index < len(self._current_response):
                row = self._current_response[self._row_index]
                self._row_index += 1
                return row
            return {"count": 0, "total": 0, "mape": 0.0}

        def fetchall(self):
            return self._current_response

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    return FakeCursor(responses)


@patch("app.agents.feedback.psycopg2.connect")
def test_feedback_agent_generates_report_and_updates_factor(mock_connect, tmp_path):
    fake_rows = [
        [{"count": 10}],
        [{"total": 400.0}],
        [{"total": 2000.0}],
        [{"total": 5}],
        [{"mape": 0.12}],
        [
            {"action_taken": "ACCEPTED", "count": 6},
            {"action_taken": "IGNORED", "count": 3},
            {"action_taken": "DELAYED", "count": 1},
        ],
        [{"value": 1.20}],
        [{}],
    ]

    fake_cursor = _fake_cursor_factory(fake_rows)
    fake_conn = MagicMock()
    fake_conn.cursor.return_value = fake_cursor
    mock_connect.return_value.__enter__.return_value = fake_conn

    agent = FeedbackAgent(dsn="dbname=test", report_dir=tmp_path, now=datetime(2026, 6, 23, tzinfo=timezone.utc))
    report = agent.run_for_date(SHOP_ID, date(2026, 6, 22))

    assert isinstance(report, FeedbackReport)
    assert report.total_transactions == 10
    assert report.total_waste_grams == 400.0
    assert report.total_prepared_grams == 2000.0
    assert report.mape == 0.12
    assert report.pearl_waste_ratio == 0.2
    assert report.stockout_minutes == 5
    assert report.pearl_safety_factor_after == 1.25
    assert report.updated is True

    report_path = tmp_path / f"feedback_{SHOP_ID}_2026-06-22.json"
    assert report_path.exists()


@patch("app.agents.feedback.psycopg2.connect")
def test_feedback_agent_no_update_when_within_threshold(mock_connect, tmp_path):
    fake_rows = [
        [{"count": 10}],
        [{"total": 200.0}],
        [{"total": 2000.0}],
        [{"total": 0}],
        [{"mape": 0.05}],
        [
            {"action_taken": "ACCEPTED", "count": 9},
            {"action_taken": "IGNORED", "count": 1},
        ],
        [{"value": 1.20}],
    ]

    fake_cursor = _fake_cursor_factory(fake_rows)
    fake_conn = MagicMock()
    fake_conn.cursor.return_value = fake_cursor
    mock_connect.return_value.__enter__.return_value = fake_conn

    agent = FeedbackAgent(dsn="dbname=test", report_dir=tmp_path, now=datetime(2026, 6, 23, tzinfo=timezone.utc))
    report = agent.run_for_date(SHOP_ID, date(2026, 6, 22))

    assert report.pearl_safety_factor_after == 1.20
    assert report.updated is False
