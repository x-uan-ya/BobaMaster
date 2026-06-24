"""
FeedbackAgent — Closed-loop daily audit and retraining utility.

Calculates end-of-day forecast accuracy, waste, and staff compliance metrics.
Produces a JSON audit report and optionally updates safety-buffer tuning
parameters in the database.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime, date, timedelta, timezone
from pathlib import Path
from typing import Callable, Optional

import psycopg2
from psycopg2.extras import RealDictCursor

from app.models.ops_decider import IngredientConfig

logger = logging.getLogger("BobaMaster.FeedbackAgent")

DEFAULT_REPORT_DIR = Path(__file__).resolve().parent.parent / "data" / "reports"
DEFAULT_MIN_SAFETY_FACTOR = 1.0
DEFAULT_MAX_SAFETY_FACTOR = 1.50
DEFAULT_PEARL_DECREASE_STEP = 0.05
DEFAULT_PEARL_INCREASE_STEP = 0.10
DEFAULT_PEARL_WASTE_THRESHOLD = 0.15


@dataclass
class FeedbackReport:
    shop_id: str
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
    generated_at: str


class FeedbackAgent:
    """Closed-loop analytics agent for daily store performance."""

    def __init__(
        self,
        dsn: Optional[str] = None,
        report_dir: Optional[Path] = None,
        now: Optional[datetime] = None,
    ):
        self._dsn = dsn or self._build_dsn()
        self._report_dir = report_dir or DEFAULT_REPORT_DIR
        self._now = now or datetime.now(timezone.utc)
        self._fs_writable = self._check_filesystem_writable()

    @staticmethod
    def _build_dsn() -> str:
        return (
            f"host={os.getenv('POSTGRES_HOST', 'localhost')} "
            f"port={os.getenv('POSTGRES_PORT', '5432')} "
            f"dbname={os.getenv('POSTGRES_DB', 'BobaMaster')} "
            f"user={os.getenv('POSTGRES_USER', 'postgres')} "
            f"password={os.getenv('POSTGRES_PASSWORD', 'postgres')}"
        )

    def _check_filesystem_writable(self) -> bool:
        """Check if the filesystem is writable (e.g., not Vercel serverless)."""
        try:
            test_dir = self._report_dir.parent
            test_dir.mkdir(parents=True, exist_ok=True)
            return True
        except OSError:
            return False

    @staticmethod
    def _normalize_ratio(value: float) -> float:
        if value != value or value == float("inf"):
            return 0.0
        return max(0.0, min(1.0, value))

    def run_for_date(self, shop_id: str, target_date: date) -> FeedbackReport:
        report = self._gather_metrics(shop_id, target_date)
        output = self._tune_pearl_safety_factor(report)
        self._save_report(output)
        return output

    def _gather_metrics(self, shop_id: str, target_date: date) -> FeedbackReport:
        start_ts = datetime(target_date.year, target_date.month, target_date.day, tzinfo=timezone.utc)
        end_ts = start_ts + timedelta(days=1)

        with psycopg2.connect(self._dsn) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                transaction_count = self._fetch_transaction_count(cur, shop_id, start_ts, end_ts)
                waste_total = self._fetch_waste_total(cur, shop_id, start_ts, end_ts)
                prepared_total = self._fetch_prepared_total(cur, shop_id, start_ts, end_ts)
                stockout_minutes = self._fetch_stockout_minutes(cur, shop_id, start_ts, end_ts)
                mape = self._fetch_mape(cur, shop_id, start_ts, end_ts)
                feedback_counts = self._fetch_feedback_counts(cur, shop_id, start_ts, end_ts)
                pearl_factor = self._fetch_pearl_safety_factor(cur)

        acceptance_rate = self._normalize_ratio(
            feedback_counts.get("ACCEPTED", 0) / max(1, transaction_count)
        )
        ignored_rate = self._normalize_ratio(
            feedback_counts.get("IGNORED", 0) / max(1, transaction_count)
        )
        delayed_rate = self._normalize_ratio(
            feedback_counts.get("DELAYED", 0) / max(1, transaction_count)
        )
        pearl_waste_ratio = self._normalize_ratio(waste_total / max(1.0, prepared_total))

        return FeedbackReport(
            shop_id=shop_id,
            date=target_date,
            total_transactions=transaction_count,
            total_waste_grams=round(waste_total, 2),
            total_prepared_grams=round(prepared_total, 2),
            mape=round(mape, 4),
            acceptance_rate=round(acceptance_rate, 4),
            ignored_rate=round(ignored_rate, 4),
            delayed_rate=round(delayed_rate, 4),
            pearl_waste_ratio=round(pearl_waste_ratio, 4),
            stockout_minutes=stockout_minutes,
            pearl_safety_factor_before=round(pearl_factor, 2),
            pearl_safety_factor_after=round(pearl_factor, 2),
            updated=False,
            generated_at=self._now.isoformat(),
        )

    def _tune_pearl_safety_factor(self, report: FeedbackReport) -> FeedbackReport:
        current_factor = report.pearl_safety_factor_before
        updated_factor = current_factor

        if report.pearl_waste_ratio > DEFAULT_PEARL_WASTE_THRESHOLD:
            updated_factor = max(
                DEFAULT_MIN_SAFETY_FACTOR,
                current_factor - DEFAULT_PEARL_DECREASE_STEP,
            )

        if report.stockout_minutes > 0:
            updated_factor = min(
                DEFAULT_MAX_SAFETY_FACTOR,
                updated_factor + DEFAULT_PEARL_INCREASE_STEP,
            )

        report.pearl_safety_factor_after = round(updated_factor, 2)
        report.updated = updated_factor != current_factor

        if report.updated:
            self._write_safety_factor(updated_factor)
            logger.info(
                "Updated pearl_safety_buffer_factor from %.2f to %.2f",
                current_factor,
                updated_factor,
            )
        else:
            logger.info("No safety factor update required.")

        return report

    def _save_report(self, report: FeedbackReport) -> None:
        if not self._fs_writable:
            logger.debug("Skipping report save - filesystem is read-only")
            return

        try:
            self._report_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            logger.warning("Cannot create report directory %s: %s", self._report_dir, e)
            return

        filename = f"feedback_{report.shop_id}_{report.date.isoformat()}.json"
        path = self._report_dir / filename
        payload = {
            **report.__dict__,
            "date": report.date.isoformat(),
        }
        try:
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(payload, fh, indent=2)
            logger.debug("Saved feedback report to %s", path)
        except OSError as e:
            logger.warning("Cannot save report to %s: %s", path, e)

    def _fetch_transaction_count(self, cur, shop_id: str, start_ts: datetime, end_ts: datetime) -> int:
        cur.execute(
            "SELECT COUNT(*) AS count FROM recommendation_logs WHERE shop_id = %s AND created_at >= %s AND created_at < %s;",
            (shop_id, start_ts, end_ts),
        )
        return int(cur.fetchone()["count"] or 0)

    def _fetch_waste_total(self, cur, shop_id: str, start_ts: datetime, end_ts: datetime) -> float:
        cur.execute(
            "SELECT COALESCE(SUM(wasted_qty_grams), 0) AS total FROM brew_logs "
            "WHERE shop_id = %s AND completed_at >= %s AND completed_at < %s;",
            (shop_id, start_ts, end_ts),
        )
        return float(cur.fetchone()["total"] or 0.0)

    def _fetch_prepared_total(self, cur, shop_id: str, start_ts: datetime, end_ts: datetime) -> float:
        cur.execute(
            "SELECT COALESCE(SUM(initial_qty_grams), 0) AS total FROM brew_logs "
            "WHERE shop_id = %s AND completed_at >= %s AND completed_at < %s;",
            (shop_id, start_ts, end_ts),
        )
        return float(cur.fetchone()["total"] or 0.0)

    def _fetch_stockout_minutes(self, cur, shop_id: str, start_ts: datetime, end_ts: datetime) -> int:
        cur.execute(
            "SELECT COALESCE(SUM(delay_minutes), 0) AS total FROM recommendation_feedback "
            "WHERE recommendation_id IN (SELECT id FROM recommendation_logs WHERE shop_id = %s AND created_at >= %s AND created_at < %s) "
            "AND action_taken = 'DELAYED';",
            (shop_id, start_ts, end_ts),
        )
        return int(cur.fetchone()["total"] or 0)

    def _fetch_mape(self, cur, shop_id: str, start_ts: datetime, end_ts: datetime) -> float:
        cur.execute(
            "SELECT COALESCE(AVG(ABS((actual_grams - forecast_grams) / NULLIF(actual_grams, 0))), 0) AS mape "
            "FROM ("
            "  SELECT s.ingredient_id, s.actual_grams, p.forecast_grams "
            "  FROM sales_forecasts p "
            "  JOIN sales_actuals s ON p.shop_id = s.shop_id "
            "  AND p.ingredient_id = s.ingredient_id "
            "  AND p.forecast_time = s.actual_time "
            "  WHERE p.shop_id = %s AND p.forecast_time >= %s AND p.forecast_time < %s"
            ") AS matched;",
            (shop_id, start_ts, end_ts),
        )
        return float(cur.fetchone()["mape"] or 0.0)

    def _fetch_feedback_counts(self, cur, shop_id: str, start_ts: datetime, end_ts: datetime) -> dict[str, int]:
        cur.execute(
            "SELECT action_taken, COUNT(*) AS count FROM recommendation_feedback "
            "WHERE recommendation_id IN (SELECT id FROM recommendation_logs WHERE shop_id = %s AND created_at >= %s AND created_at < %s) "
            "GROUP BY action_taken;",
            (shop_id, start_ts, end_ts),
        )
        rows = cur.fetchall()
        return {row["action_taken"]: int(row["count"]) for row in rows}

    def _fetch_pearl_safety_factor(self, cur) -> float:
        cur.execute(
            "SELECT value FROM system_settings WHERE key = 'pearl_safety_buffer_factor' LIMIT 1;"
        )
        row = cur.fetchone()
        if row is None:
            return 1.20
        return float(row["value"])

    def _write_safety_factor(self, factor: float) -> None:
        with psycopg2.connect(self._dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO system_settings (key, value) VALUES (%s, %s) "
                    "ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value;",
                    ("pearl_safety_buffer_factor", str(factor)),
                )
                conn.commit()
