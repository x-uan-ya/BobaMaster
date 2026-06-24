from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Literal, Optional


class WeatherContext(BaseModel):
    temp_c: float = Field(..., description="Ambient temperature in Celsius")
    rain_prob: float = Field(..., ge=0.0, le=1.0, description="Probability of rain 0.0–1.0")
    rain_intensity_mm: float = Field(..., ge=0.0, description="Rain intensity in mm/hr")
    sky_condition: Literal["sunny", "cloudy", "rainy", "stormy"]
    humidity_pct: float = Field(..., ge=0.0, le=100.0, description="Relative humidity percentage")


class CalendarContext(BaseModel):
    is_school_day: bool = Field(..., description="True if schools are in session today")
    is_public_holiday: bool = Field(..., description="True if today is a public holiday")
    day_of_week: int = Field(..., ge=0, le=6, description="0=Monday … 6=Sunday")
    hour_of_day: int = Field(..., ge=0, le=23, description="Local hour of day")


class LocalEventsContext(BaseModel):
    has_nearby_event: bool = Field(..., description="True if a nearby event is expected to drive foot traffic")
    event_type: Optional[str] = Field(None, description="e.g. 'concert', 'market', 'sports'")
    crowd_score: float = Field(..., ge=0.0, le=1.0, description="Estimated foot traffic impact score 0.0–1.0")


class ContextVector(BaseModel):
    shop_id: UUID
    captured_at: datetime
    weather: WeatherContext
    calendar: CalendarContext
    local_events: LocalEventsContext
    ttl_seconds: int = Field(900, description="How many seconds this context snapshot is valid for")
