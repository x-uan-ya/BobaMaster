from abc import ABC, abstractmethod
from datetime import datetime, timezone
from app.models.context import WeatherContext


# ---------------------------------------------------------------------------
# Abstract Interface
# ---------------------------------------------------------------------------

class WeatherAdapterBase(ABC):
    """
    Abstract base for weather data adapters.
    Swap implementations without touching ContextAgent.
    """

    @abstractmethod
    def fetch(self, lat: float, lon: float, at: datetime) -> WeatherContext:
        """Fetch weather context for a given coordinate and timestamp."""
        ...


# ---------------------------------------------------------------------------
# Mock Implementation (deterministic, no API key required)
# ---------------------------------------------------------------------------

class MockWeatherAdapter(WeatherAdapterBase):
    """
    Fully deterministic mock weather adapter for development and testing.
    All values are derived from the current timestamp — no randomness,
    no external network calls.
    """

    def fetch(self, lat: float, lon: float, at: datetime) -> WeatherContext:
        month = at.month
        minute = at.minute

        # Seasonal temperature approximation (Celsius)
        if month in (6, 7, 8):
            temp_c = 31.0   # Hot summer
        elif month in (12, 1, 2):
            temp_c = 14.0   # Cool winter
        else:
            temp_c = 24.0   # Mild shoulder season

        # Rain probability based on current minute (even=clear, odd=rainy)
        if minute % 2 == 0:
            rain_prob = 0.10
            rain_intensity_mm = 0.0
            sky_condition = "sunny"
        else:
            rain_prob = 0.75
            rain_intensity_mm = 3.5
            sky_condition = "rainy"

        return WeatherContext(
            temp_c=temp_c,
            rain_prob=rain_prob,
            rain_intensity_mm=rain_intensity_mm,
            sky_condition=sky_condition,
            humidity_pct=72.0,
        )


# ---------------------------------------------------------------------------
# Real Adapter Stub (to be implemented when OpenWeatherMap key is available)
# ---------------------------------------------------------------------------

class OpenWeatherMapAdapter(WeatherAdapterBase):
    """
    Production weather adapter using the OpenWeatherMap One Call API 3.0.
    Requires OPENWEATHER_API_KEY environment variable to be set.
    """

    def __init__(self, api_key: str):
        self._api_key = api_key

    def fetch(self, lat: float, lon: float, at: datetime) -> WeatherContext:
        # TODO: implement real API call using httpx
        raise NotImplementedError(
            "OpenWeatherMapAdapter is not yet implemented. "
            "Set OPENWEATHER_API_KEY and implement the httpx call."
        )
