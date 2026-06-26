"""
Weather MCP Server Implementation

Provides weather data for demand correlation analysis.
Helps predict surge in demand based on temperature, humidity, and events.

Can be run standalone:
  python -m app.mcp_servers.weather_server
"""

from __future__ import annotations

import logging
import json
from datetime import datetime, timedelta
from typing import Any
import asyncio

logger = logging.getLogger("BobaMaster.WeatherServer")


class WeatherDataProvider:
    """Simulates weather API calls with realistic data."""

    @staticmethod
    def get_forecast(
        latitude: float, longitude: float, days: int = 7
    ) -> dict[str, Any]:
        """
        Get weather forecast data.

        In production, this would call a real weather API (OpenWeather, WeatherAPI, etc.)
        """
        now = datetime.utcnow()
        forecast = []

        for day in range(days):
            date = now + timedelta(days=day)
            # Simulate realistic weather patterns
            # Hot days = higher bubble tea demand
            temp = 72 + (day * 2) % 15  # Varying temperatures
            humidity = 60 + (day * 5) % 30
            chance_rain = (day * 10) % 100

            forecast.append(
                {
                    "date": date.isoformat(),
                    "temp_high_f": temp,
                    "temp_low_f": temp - 15,
                    "humidity_percent": humidity,
                    "rain_probability": chance_rain,
                    "conditions": "Partly Cloudy"
                    if chance_rain < 30
                    else "Rainy",
                    "demand_multiplier": 1.2 if temp > 85 else 1.0
                    if temp > 70 else 0.8,  # Hot = more demand
                }
            )

        return {
            "location": {"lat": latitude, "lon": longitude},
            "generated_at": now.isoformat(),
            "forecast": forecast,
            "insights": [
                f"Temperature will reach {max(f['temp_high_f'] for f in forecast)}F in next {days} days",
                f"Best sales days: {', '.join([f['date'] for f in forecast if f['demand_multiplier'] > 1.0])}",
            ],
        }

    @staticmethod
    def get_hourly_forecast(
        latitude: float, longitude: float, hours: int = 24
    ) -> dict[str, Any]:
        """Get hourly weather forecast for intra-day demand prediction."""
        now = datetime.utcnow()
        forecast = []

        for hour in range(hours):
            time = now + timedelta(hours=hour)
            # Peak demand typically 11-1pm and 5-7pm
            hour_of_day = time.hour
            is_peak = (11 <= hour_of_day < 13) or (17 <= hour_of_day < 19)

            temp = 72 + (8 * (hour_of_day - 12) / 12)  # Warmer mid-day
            demand_factor = 1.3 if is_peak else 0.9

            forecast.append(
                {
                    "time": time.isoformat(),
                    "temp_f": temp,
                    "humidity_percent": 60,
                    "is_peak_hour": is_peak,
                    "expected_demand_multiplier": demand_factor,
                }
            )

        return {
            "location": {"lat": latitude, "lon": longitude},
            "forecast": forecast,
        }

    @staticmethod
    def get_seasonal_adjustment(
        date: str,
    ) -> dict[str, Any]:
        """Get seasonal demand adjustments (summer hot = more sales)."""
        month = int(date.split("-")[1])

        # Summer (6-8) = high demand, Winter (12-2) = low demand
        if month in [6, 7, 8]:
            multiplier = 1.4
            season = "Summer"
        elif month in [12, 1, 2]:
            multiplier = 0.7
            season = "Winter"
        else:
            multiplier = 1.0
            season = "Spring/Fall"

        return {
            "season": season,
            "month": month,
            "demand_multiplier": multiplier,
            "recommendation": f"{season} demand pattern: multiply baseline by {multiplier}x",
        }


class WeatherMCPServer:
    """MCP server exposing weather tools."""

    def __init__(self):
        self.provider = WeatherDataProvider()

    def get_tools_schema(self) -> list[dict[str, Any]]:
        """Return tool schemas for MCP discovery."""
        return [
            {
                "name": "weather_forecast",
                "description": "Get weather forecast for demand correlation",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "latitude": {
                            "type": "number",
                            "description": "Latitude",
                        },
                        "longitude": {
                            "type": "number",
                            "description": "Longitude",
                        },
                        "days": {
                            "type": "integer",
                            "description": "Number of days (default 7)",
                            "default": 7,
                        },
                    },
                    "required": ["latitude", "longitude"],
                },
            },
            {
                "name": "weather_hourly",
                "description": "Get hourly weather forecast for intra-day prediction",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "latitude": {
                            "type": "number",
                            "description": "Latitude",
                        },
                        "longitude": {
                            "type": "number",
                            "description": "Longitude",
                        },
                        "hours": {
                            "type": "integer",
                            "description": "Number of hours (default 24)",
                            "default": 24,
                        },
                    },
                    "required": ["latitude", "longitude"],
                },
            },
            {
                "name": "weather_seasonal",
                "description": "Get seasonal demand adjustments",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "date": {
                            "type": "string",
                            "description": "Date in YYYY-MM-DD format",
                        },
                    },
                    "required": ["date"],
                },
            },
        ]

    async def process_tool_call(
        self, tool_name: str, **kwargs
    ) -> dict[str, Any]:
        """Process tool calls."""
        if tool_name == "weather_forecast":
            return self.provider.get_forecast(
                kwargs["latitude"],
                kwargs["longitude"],
                kwargs.get("days", 7),
            )
        elif tool_name == "weather_hourly":
            return self.provider.get_hourly_forecast(
                kwargs["latitude"],
                kwargs["longitude"],
                kwargs.get("hours", 24),
            )
        elif tool_name == "weather_seasonal":
            return self.provider.get_seasonal_adjustment(kwargs["date"])
        else:
            raise ValueError(f"Unknown tool: {tool_name}")


# Standalone server mode
if __name__ == "__main__":

    async def run_server():
        """Run MCP server for development/testing."""
        import uvicorn
        from fastapi import FastAPI, HTTPException

        app = FastAPI(title="Weather MCP Server")
        server = WeatherMCPServer()

        @app.post("/mcp/call_tool")
        async def call_tool(tool_name: str, **kwargs):
            try:
                result = await server.process_tool_call(tool_name, **kwargs)
                return result
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

        @app.get("/mcp/tools")
        async def list_tools():
            return {"tools": server.get_tools_schema()}

        uvicorn.run(app, host="0.0.0.0", port=8081)

    asyncio.run(run_server())
