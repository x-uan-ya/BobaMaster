"""
RecommendationService — PostgreSQL persistence adapter for recommendation_logs.

Provides a write callable compatible with OpsDeciderAgent's RecommendationWriter
protocol.  Falls back gracefully if the DB is unavailable so the decision engine
never crashes due to a logging failure.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Optional

import psycopg2
import psycopg2.extras

from app.models.ops_decider import RecommendationLog

logger = logging.getLogger("BobaMaster.RecommendationService")

# Connection string read from environment (same vars used in init_db.py)
_DSN = (
    f"host={os.getenv('POSTGRES_HOST', 'localhost')} "
    f"port={os.getenv('POSTGRES_PORT', '5432')} "
    f"dbname={os.getenv('POSTGRES_DB', 'bobaflow')} "
    f"user={os.getenv('POSTGRES_USER', 'postgres')} "
    f"password={os.getenv('POSTGRES_PASSWORD', 'postgres')}"
)

_INSERT_SQL = """
INSERT INTO recommendation_logs
    (id, shop_id, created_at, ingredient_id, action_recommended,
     predicted_shortage_at, explanation_text, model_features_snapshot)
VALUES
    (%(id)s, %(shop_id)s, %(created_at)s, %(ingredient_id)s, %(action_recommended)s,
     %(predicted_shortage_at)s, %(explanation_text)s, %(model_features_snapshot)s)
ON CONFLICT (id) DO NOTHING;
"""

# Cooldown check — return the latest recommendation for a shop+ingredient within N minutes
_COOLDOWN_CHECK_SQL = """
SELECT created_at FROM recommendation_logs
WHERE shop_id = %(shop_id)s
  AND ingredient_id = %(ingredient_id)s
  AND action_recommended = %(action)s
  AND created_at >= NOW() - INTERVAL '10 minutes'
ORDER BY created_at DESC
LIMIT 1;
"""


class RecommendationService:
    """
    Thin psycopg2 adapter for recommendation_logs writes.

    Usage::

        svc = RecommendationService()
        ops_agent = OpsDeciderAgent(recommendation_writer=svc.write)
    """

    def __init__(self, dsn: Optional[str] = None):
        self._dsn = dsn or _DSN

    def write(self, log: RecommendationLog) -> None:
        """Write a RecommendationLog to PostgreSQL. Silently logs errors."""
        params = {
            "id": str(log.id),
            "shop_id": str(log.shop_id),
            "created_at": log.created_at,
            "ingredient_id": log.ingredient_id,
            "action_recommended": log.action_recommended.value,
            "predicted_shortage_at": log.predicted_shortage_at,
            "explanation_text": log.explanation_text,
            "model_features_snapshot": json.dumps(log.model_features_snapshot),
        }
        try:
            with psycopg2.connect(self._dsn) as conn:
                with conn.cursor() as cur:
                    cur.execute(_INSERT_SQL, params)
                conn.commit()
            logger.debug(f"RecommendationLog {log.id} written to PostgreSQL.")
        except Exception as e:
            logger.error(f"Failed to write recommendation log {log.id} to PostgreSQL: {e}")
