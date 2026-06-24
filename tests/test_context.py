import sys
import os
import json
from uuid import uuid4, UUID
from datetime import datetime, timezone
from unittest.mock import MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))

from app.models.context import ContextVector, WeatherContext, CalendarContext, LocalEventsContext
from app.services.weather_service import MockWeatherAdapter
from app.services.calendar_service import MockCalendarAdapter, MockLocalEventsAdapter
from app.agents.context_agent import ContextAgent


SHOP_ID = uuid4()


# ---------------------------------------------------------------------------
# In-memory Redis mock (re-used from test_inventory.py pattern)
# ---------------------------------------------------------------------------

class InMemoryRedis:
    def __init__(self):
        self._store: dict[str, tuple[str, int]] = {}  # key → (value, ttl)

    def get(self, key: str):
        entry = self._store.get(key)
        return entry[0].encode() if entry else None

    def setex(self, key: str, ttl: int, value: str):
        self._store[key] = (value, ttl)

    def delete(self, key: str):
        self._store.pop(key, None)

    def exists(self, key: str) -> bool:
        return key in self._store


def _make_agent(redis_mock=None):
    r = redis_mock or InMemoryRedis()
    return ContextAgent(
        redis_client=r,
        weather_adapter=MockWeatherAdapter(),
        calendar_adapter=MockCalendarAdapter(),
        events_adapter=MockLocalEventsAdapter(),
    ), r


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_context_vector_schema():
    """Returned object must be a valid ContextVector Pydantic model."""
    agent, _ = _make_agent()
    ctx = agent.get_context(SHOP_ID)
    assert isinstance(ctx, ContextVector)
    assert ctx.shop_id == SHOP_ID
    assert isinstance(ctx.weather, WeatherContext)
    assert isinstance(ctx.calendar, CalendarContext)
    assert isinstance(ctx.local_events, LocalEventsContext)


def test_context_weather_mock_temperature():
    """Mock weather returns correct seasonal temperature."""
    adapter = MockWeatherAdapter()
    now = datetime.now(timezone.utc)
    weather = adapter.fetch(1.35, 103.8, now)

    month = now.month
    if month in (6, 7, 8):
        assert weather.temp_c == 31.0
    elif month in (12, 1, 2):
        assert weather.temp_c == 14.0
    else:
        assert weather.temp_c == 24.0


def test_context_school_mock_summer():
    """School flag must be False during June, July, August."""
    adapter = MockCalendarAdapter()

    # Simulate a weekday in July
    july_weekday = datetime(2026, 7, 14, 10, 0, tzinfo=timezone.utc)  # Tuesday
    cal = adapter.fetch(july_weekday)
    assert cal.is_school_day is False


def test_context_school_mock_term():
    """School flag must be True on a weekday outside holiday months."""
    adapter = MockCalendarAdapter()

    # Simulate a Wednesday in October
    oct_weekday = datetime(2026, 10, 7, 10, 0, tzinfo=timezone.utc)
    cal = adapter.fetch(oct_weekday)
    assert cal.is_school_day is True


def test_context_event_window():
    """Local events flag must be True between 17:00 and 20:59."""
    adapter = MockLocalEventsAdapter()

    # 18:30 → inside event window
    inside = datetime(2026, 6, 23, 18, 30, tzinfo=timezone.utc)
    ev_in = adapter.fetch(1.35, 103.8, inside)
    assert ev_in.has_nearby_event is True
    assert ev_in.crowd_score > 0.0

    # 14:00 → outside event window
    outside = datetime(2026, 6, 23, 14, 0, tzinfo=timezone.utc)
    ev_out = adapter.fetch(1.35, 103.8, outside)
    assert ev_out.has_nearby_event is False
    assert ev_out.crowd_score == 0.0


def test_context_cache_miss_populates_cache():
    """On a cache miss, agent fetches and writes to Redis."""
    redis_mock = InMemoryRedis()
    agent, r = _make_agent(redis_mock)

    cache_key = f"context:{SHOP_ID}"
    assert not r.exists(cache_key)

    agent.get_context(SHOP_ID)

    # After the call, the cache should now be populated
    assert r.exists(cache_key)


def test_context_cache_hit_skips_adapters():
    """On a cache hit, adapters must NOT be called again."""
    redis_mock = InMemoryRedis()

    # Manually seed cache with a valid ContextVector JSON
    seed_ctx = ContextVector(
        shop_id=SHOP_ID,
        captured_at=datetime.now(timezone.utc),
        weather=WeatherContext(temp_c=28.0, rain_prob=0.2, rain_intensity_mm=0.0, sky_condition="sunny", humidity_pct=60.0),
        calendar=CalendarContext(is_school_day=True, is_public_holiday=False, day_of_week=1, hour_of_day=14),
        local_events=LocalEventsContext(has_nearby_event=False, event_type=None, crowd_score=0.0),
    )
    redis_mock.setex(f"context:{SHOP_ID}", 900, seed_ctx.model_dump_json())

    # Use mock adapters that would raise if called
    weather_mock = MagicMock(spec=MockWeatherAdapter)
    weather_mock.fetch.side_effect = AssertionError("Weather adapter should NOT be called on cache hit!")

    agent = ContextAgent(
        redis_client=redis_mock,
        weather_adapter=weather_mock,
        calendar_adapter=MockCalendarAdapter(),
        events_adapter=MockLocalEventsAdapter(),
    )

    ctx = agent.get_context(SHOP_ID)
    # Should return cached value, not call the mock
    weather_mock.fetch.assert_not_called()
    assert ctx.weather.temp_c == 28.0


def test_context_cache_invalidation():
    """After cache invalidation, next call fetches fresh data."""
    redis_mock = InMemoryRedis()
    agent, r = _make_agent(redis_mock)

    agent.get_context(SHOP_ID)
    assert r.exists(f"context:{SHOP_ID}")

    agent.invalidate_cache(SHOP_ID)
    assert not r.exists(f"context:{SHOP_ID}")
