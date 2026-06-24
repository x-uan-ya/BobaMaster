# Implementation Plan: Milestone 4 — Context Enrichment Service

This document outlines the implementation plan for Milestone 4. Code will begin only after approval.

---

## 1. Objectives
*   Build a `ContextAgent` that assembles an operational context snapshot for a given store at any point in time.
*   Abstract external data sources (weather, school calendar, local events) behind clean adapter interfaces so they can be swapped from mock → real API with zero agent code changes.
*   Cache context vectors in Redis to avoid redundant API calls during high-frequency evaluation cycles.
*   Expose a REST endpoint so the `OpsDeciderAgent` (Milestone 6) and the frontend can request the current context.

---

## 2. Core Architectural Rules
> [!IMPORTANT]
> *   **No arithmetic or business decisions here.** The `ContextAgent` only fetches, normalizes, and packages context data. It does not compute demand forecasts or brew decisions.
> *   **Adapter pattern:** Every external data source is wrapped behind a Python abstract interface. The default implementation uses deterministic mock data. A real `OpenWeatherMapAdapter` can be plugged in later by changing one config line.
> *   **No LLM calls in this milestone.** Context vectors are structured data only.

---

## 3. Deliverables
| File | Status |
| :--- | :--- |
| `backend/app/models/context.py` | [NEW] Pydantic V2 context vector schemas |
| `backend/app/services/weather_service.py` | [NEW] Abstract weather adapter + mock implementation |
| `backend/app/services/calendar_service.py` | [NEW] Abstract calendar adapter + mock implementation |
| `backend/app/agents/context_agent.py` | [NEW] Assembles context vector from adapters + Redis cache |
| `backend/app/api/context.py` | [NEW] REST endpoint exposing current context |
| `backend/app/main.py` | [MODIFY] Attach context router |
| `tests/test_context.py` | [NEW] pytest suite using mock adapters |

---

## 4. Context Vector Schema (`models/context.py`)

The context vector is a normalized, strongly-typed snapshot delivered to the forecasting engine and the LLM explainer.

```python
class WeatherContext(BaseModel):
    temp_c: float                    # Ambient temperature in Celsius
    rain_prob: float                 # 0.0 – 1.0 probability of rain
    rain_intensity_mm: float         # mm/hr (0 if none)
    sky_condition: Literal["sunny", "cloudy", "rainy", "stormy"]
    humidity_pct: float              # 0–100%

class CalendarContext(BaseModel):
    is_school_day: bool              # True if schools are in session
    is_public_holiday: bool          # True if national/public holiday
    day_of_week: int                 # 0=Monday … 6=Sunday
    hour_of_day: int                 # 0–23 local hour

class LocalEventsContext(BaseModel):
    has_nearby_event: bool           # Concert, market, school event nearby
    event_type: Optional[str]        # e.g. "concert", "market", "sports"
    crowd_score: float               # 0.0–1.0 estimated foot traffic impact

class ContextVector(BaseModel):
    shop_id: UUID
    captured_at: datetime
    weather: WeatherContext
    calendar: CalendarContext
    local_events: LocalEventsContext
    ttl_seconds: int = 900           # Context is valid for 15 minutes (cached)
```

---

## 5. Adapter Architecture

Two abstract base classes define the interface. Mock implementations are used by default:

```
WeatherAdapterBase (ABC)
    └── MockWeatherAdapter      ← default for dev/test
    └── OpenWeatherMapAdapter   ← plug in for production (future)

CalendarAdapterBase (ABC)
    └── MockCalendarAdapter     ← default for dev/test
    └── GoogleCalendarAdapter   ← plug in for production (future)
```

### Mock Logic (deterministic, no API keys required)
**MockWeatherAdapter:**
*   `temp_c`: derived from current month. June–Aug = 31°C, Dec–Feb = 14°C, otherwise 24°C.
*   `rain_prob`: if current minute is even → `0.1` (clear), if odd → `0.75` (rainy).
*   `sky_condition`: derived from `rain_prob` threshold.
*   `humidity_pct`: fixed at `72.0` for mock.

**MockCalendarAdapter:**
*   `is_school_day`: `False` if month is June, July, or August, else `True`.
*   `is_public_holiday`: `False` always in mock.
*   `day_of_week` / `hour_of_day`: derived from `datetime.now()`.

**MockLocalEventsAdapter:**
*   `has_nearby_event`: `True` if `hour_of_day` is between 17 and 21 (evening event window).
*   `event_type`: `"evening_rush"` during event window, else `None`.
*   `crowd_score`: `0.65` during event window, else `0.0`.

---

## 6. Redis Caching Strategy
*   Context vector is serialized to JSON and stored in Redis under key:
    ```
    context:{shop_id}
    ```
*   TTL: 900 seconds (15 minutes). After expiry, next call fetches fresh data from adapters.
*   On cache hit: return deserialized `ContextVector` immediately.
*   On cache miss: fetch → normalize → cache → return.

---

## 7. API Endpoint (`api/context.py`)

| Method | Route | Purpose |
| :--- | :--- | :--- |
| `GET` | `/api/v1/context/{shop_id}` | Returns current context vector for a shop. Uses Redis cache. |
| `DELETE` | `/api/v1/context/{shop_id}/cache` | Force-invalidates the context cache (useful after a manual event override). |

---

## 8. Testing Strategy (`tests/test_context.py`)

*   `test_context_weather_mock`: Verify mock weather adapter produces correct temperature per season.
*   `test_context_school_mock`: Verify school flag is `False` during June–August.
*   `test_context_event_window`: Verify `has_nearby_event=True` during the 17–21 hour window.
*   `test_context_cache_hit`: Populate Redis cache manually, verify `ContextAgent` returns cached value without calling adapters a second time.
*   `test_context_cache_miss_and_populate`: Clear cache, call agent, verify Redis key is written with correct TTL structure.
*   `test_context_vector_schema`: Verify returned object is a valid `ContextVector` Pydantic model.

---

## 9. Acceptance Criteria
*   All 6 unit tests pass with no warnings.
*   `GET /api/v1/context/{shop_id}` returns a valid `ContextVector` JSON payload.
*   Adapter swap is achievable by changing a single constructor argument — no changes to `ContextAgent` logic.
*   Context is cached for 15 minutes and re-fetched automatically on expiry.
