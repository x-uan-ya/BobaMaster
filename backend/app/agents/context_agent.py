import json
import logging
from uuid import UUID
from datetime import datetime, timezone
from typing import Optional

import redis

from app.models.context import ContextVector
from app.services.weather_service import WeatherAdapterBase, MockWeatherAdapter
from app.services.calendar_service import (
    CalendarAdapterBase, MockCalendarAdapter,
    LocalEventsAdapterBase, MockLocalEventsAdapter,
)

logger = logging.getLogger("BobaMaster.ContextAgent")

# Default store coordinates (used when no specific lat/lon is registered per shop)
DEFAULT_LAT = 1.3521    # Singapore latitude
DEFAULT_LON = 103.8198  # Singapore longitude

_CONTEXT_TTL_SECONDS = 900  # 15 minutes


def _cache_key(shop_id: UUID) -> str:
    return f"context:{shop_id}"


class ContextAgent:
    """
    Assembles a normalized ContextVector from weather, calendar, and local
    events adapters. Caches the result in Redis for TTL_SECONDS to prevent
    redundant external API calls.

    All adapters are injected via constructor — swap mock ↔ real with zero
    changes to this class.
    """

    def __init__(
        self,
        redis_client: redis.Redis,
        weather_adapter: Optional[WeatherAdapterBase] = None,
        calendar_adapter: Optional[CalendarAdapterBase] = None,
        events_adapter: Optional[LocalEventsAdapterBase] = None,
    ):
        self._r = redis_client
        self._weather = weather_adapter or MockWeatherAdapter()
        self._calendar = calendar_adapter or MockCalendarAdapter()
        self._events = events_adapter or MockLocalEventsAdapter()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_context(
        self,
        shop_id: UUID,
        lat: float = DEFAULT_LAT,
        lon: float = DEFAULT_LON,
    ) -> ContextVector:
        """
        Returns the current ContextVector for a shop.
        Checks Redis cache first; fetches fresh data on cache miss.
        """
        cached = self._get_from_cache(shop_id)
        if cached:
            logger.debug(f"Context cache HIT for shop {shop_id}.")
            return cached

        logger.info(f"Context cache MISS for shop {shop_id}. Fetching fresh context.")
        vector = self._fetch_fresh(shop_id, lat, lon)
        self._write_to_cache(shop_id, vector)
        return vector

    def invalidate_cache(self, shop_id: UUID) -> None:
        """Force-clear the cached context for a shop (e.g. after a manual event override)."""
        key = _cache_key(shop_id)
        self._r.delete(key)
        logger.info(f"Context cache invalidated for shop {shop_id}.")

    # ------------------------------------------------------------------
    # Internal Helpers
    # ------------------------------------------------------------------

    def _fetch_fresh(self, shop_id: UUID, lat: float, lon: float) -> ContextVector:
        now = datetime.now(timezone.utc)

        # Fetch all three context dimensions independently
        # If any adapter fails, log the error and use a safe fallback value
        try:
            weather = self._weather.fetch(lat, lon, now)
        except Exception as e:
            logger.error(f"WeatherAdapter failed: {e}. Using fallback values.")
            from app.models.context import WeatherContext
            weather = WeatherContext(
                temp_c=24.0, rain_prob=0.1, rain_intensity_mm=0.0,
                sky_condition="cloudy", humidity_pct=65.0
            )

        try:
            calendar = self._calendar.fetch(now)
        except Exception as e:
            logger.error(f"CalendarAdapter failed: {e}. Using fallback values.")
            from app.models.context import CalendarContext
            calendar = CalendarContext(
                is_school_day=True, is_public_holiday=False,
                day_of_week=now.weekday(), hour_of_day=now.hour
            )

        try:
            events = self._events.fetch(lat, lon, now)
        except Exception as e:
            logger.error(f"EventsAdapter failed: {e}. Using fallback values.")
            from app.models.context import LocalEventsContext
            events = LocalEventsContext(
                has_nearby_event=False, event_type=None, crowd_score=0.0
            )

        return ContextVector(
            shop_id=shop_id,
            captured_at=now,
            weather=weather,
            calendar=calendar,
            local_events=events,
            ttl_seconds=_CONTEXT_TTL_SECONDS,
        )

    def _get_from_cache(self, shop_id: UUID) -> Optional[ContextVector]:
        key = _cache_key(shop_id)
        raw = self._r.get(key)
        if not raw:
            return None
        try:
            data = json.loads(raw.decode() if isinstance(raw, bytes) else raw)
            return ContextVector.model_validate(data)
        except Exception as e:
            logger.warning(f"Failed to deserialize cached context for {shop_id}: {e}")
            return None

    def _write_to_cache(self, shop_id: UUID, vector: ContextVector) -> None:
        key = _cache_key(shop_id)
        try:
            payload = vector.model_dump_json()
            self._r.setex(key, _CONTEXT_TTL_SECONDS, payload)
            logger.debug(f"Context cached for shop {shop_id} (TTL: {_CONTEXT_TTL_SECONDS}s).")
        except Exception as e:
            logger.error(f"Failed to cache context for {shop_id}: {e}")
