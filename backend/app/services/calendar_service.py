from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Tuple
from app.models.context import CalendarContext, LocalEventsContext


# ---------------------------------------------------------------------------
# Abstract Interfaces
# ---------------------------------------------------------------------------

class CalendarAdapterBase(ABC):
    """Abstract base for school calendar and public holiday data."""

    @abstractmethod
    def fetch(self, at: datetime) -> CalendarContext:
        """Return calendar context for the given timestamp."""
        ...


class LocalEventsAdapterBase(ABC):
    """Abstract base for local event detection (concerts, markets, sports)."""

    @abstractmethod
    def fetch(self, lat: float, lon: float, at: datetime) -> LocalEventsContext:
        """Return local events context for a given coordinate and timestamp."""
        ...


# ---------------------------------------------------------------------------
# Mock Calendar Adapter
# ---------------------------------------------------------------------------

class MockCalendarAdapter(CalendarAdapterBase):
    """
    Deterministic mock calendar. Uses date/time arithmetic only.
    School holidays: June, July, August.
    Public holidays: none in mock.
    """

    # School holiday months (no classes)
    _HOLIDAY_MONTHS = {6, 7, 8}

    def fetch(self, at: datetime) -> CalendarContext:
        is_school_day = at.month not in self._HOLIDAY_MONTHS and at.weekday() < 5
        return CalendarContext(
            is_school_day=is_school_day,
            is_public_holiday=False,
            day_of_week=at.weekday(),   # 0=Monday … 6=Sunday
            hour_of_day=at.hour,
        )


# ---------------------------------------------------------------------------
# Mock Local Events Adapter
# ---------------------------------------------------------------------------

class MockLocalEventsAdapter(LocalEventsAdapterBase):
    """
    Deterministic mock events adapter.
    Simulates an "evening rush" event window between 17:00 and 21:00 daily.
    """

    _EVENT_START_HOUR = 17
    _EVENT_END_HOUR = 21

    def fetch(self, lat: float, lon: float, at: datetime) -> LocalEventsContext:
        in_event_window = self._EVENT_START_HOUR <= at.hour < self._EVENT_END_HOUR
        return LocalEventsContext(
            has_nearby_event=in_event_window,
            event_type="evening_rush" if in_event_window else None,
            crowd_score=0.65 if in_event_window else 0.0,
        )


# ---------------------------------------------------------------------------
# Real Adapter Stubs (plug in when external APIs are available)
# ---------------------------------------------------------------------------

class GoogleCalendarAdapter(CalendarAdapterBase):
    """Production adapter reading public holiday and school term calendars."""

    def fetch(self, at: datetime) -> CalendarContext:
        raise NotImplementedError("GoogleCalendarAdapter is not yet implemented.")


class EventbriteAdapter(LocalEventsAdapterBase):
    """Production adapter reading nearby events from Eventbrite or similar API."""

    def fetch(self, lat: float, lon: float, at: datetime) -> LocalEventsContext:
        raise NotImplementedError("EventbriteAdapter is not yet implemented.")
