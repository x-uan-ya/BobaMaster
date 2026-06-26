"""
Events MCP Server Implementation

Provides local events calendar for peak demand prediction.
Correlates events with demand surges (concerts, sports games, etc.).

Can be run standalone:
  python -m app.mcp_servers.events_server
"""

from __future__ import annotations

import logging
import json
from datetime import datetime, timedelta
from typing import Any
import asyncio

logger = logging.getLogger("BobaMaster.EventsServer")


class EventsDataProvider:
    """Simulates local events API calls."""

    # Mock events database
    MOCK_EVENTS = [
        {
            "id": "evt_001",
            "name": "Downtown Street Fair",
            "date": (datetime.utcnow() + timedelta(days=3)).isoformat(),
            "time": "10:00-18:00",
            "location": "Main Street",
            "expected_attendance": 5000,
            "category": "community_event",
            "demand_impact": 2.5,  # 250% increase in demand
        },
        {
            "id": "evt_002",
            "name": "Local High School Graduation",
            "date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "time": "14:00-20:00",
            "location": "School Grounds (5 blocks away)",
            "expected_attendance": 2000,
            "category": "graduation",
            "demand_impact": 2.0,
        },
        {
            "id": "evt_003",
            "name": "Weekend Concert Series",
            "date": (datetime.utcnow() + timedelta(days=2)).isoformat(),
            "time": "19:00-23:00",
            "location": "Park Amphitheater",
            "expected_attendance": 8000,
            "category": "concert",
            "demand_impact": 3.0,
        },
        {
            "id": "evt_004",
            "name": "Local Sports Game",
            "date": (datetime.utcnow() + timedelta(days=1)).isoformat(),
            "time": "18:00-21:00",
            "location": "City Stadium",
            "expected_attendance": 10000,
            "category": "sports",
            "demand_impact": 1.8,
        },
    ]

    @staticmethod
    def list_events(
        city: str = "Downtown", date_range_days: int = 7
    ) -> dict[str, Any]:
        """List local events within date range."""
        now = datetime.utcnow()
        cutoff_date = now + timedelta(days=date_range_days)

        events = []
        for event in EventsDataProvider.MOCK_EVENTS:
            event_date = datetime.fromisoformat(event["date"])
            if now <= event_date <= cutoff_date:
                events.append(event)

        # Sort by date
        events = sorted(
            events, key=lambda e: datetime.fromisoformat(e["date"])
        )

        return {
            "city": city,
            "date_range_days": date_range_days,
            "query_time": now.isoformat(),
            "events_found": len(events),
            "events": events,
            "summary": f"{len(events)} events found in next {date_range_days} days",
        }

    @staticmethod
    def get_event_details(event_id: str) -> dict[str, Any]:
        """Get detailed information about a specific event."""
        event = next(
            (e for e in EventsDataProvider.MOCK_EVENTS if e["id"] == event_id),
            None,
        )

        if not event:
            return {"error": f"Event {event_id} not found"}

        return {
            "event": event,
            "preparation_recommendations": [
                f"Prepare extra {int(event['demand_impact'] * 50)} cups worth of base ingredients",
                f"Schedule extra staff {int((event['demand_impact'] - 1) * 2)} hours before event",
                f"Check tapioca pearls and ice levels - expect {int(event['demand_impact'] * 100 - 100)}% higher usage",
            ],
            "peak_hour": event["time"],
        }

    @staticmethod
    def get_demand_forecast_from_events(
        city: str, days: int = 7
    ) -> dict[str, Any]:
        """Get aggregated demand forecast based on upcoming events."""
        events_response = EventsDataProvider.list_events(city, days)
        events = events_response["events"]

        # Group by date and calculate demand impact
        demand_by_date = {}
        for event in events:
            event_date = event["date"].split("T")[0]  # Date only
            if event_date not in demand_by_date:
                demand_by_date[event_date] = {
                    "base_multiplier": 1.0,
                    "events": [],
                }
            demand_by_date[event_date]["base_multiplier"] *= event[
                "demand_impact"
            ]
            demand_by_date[event_date]["events"].append(event["name"])

        forecast = []
        for date_str, data in sorted(demand_by_date.items()):
            forecast.append(
                {
                    "date": date_str,
                    "demand_multiplier": round(
                        min(data["base_multiplier"], 5.0), 2
                    ),  # Cap at 5x
                    "events": data["events"],
                    "recommendation": "HIGH DEMAND - prepare extra stock"
                    if data["base_multiplier"] > 2
                    else "Normal demand",
                }
            )

        return {
            "city": city,
            "forecast_days": days,
            "demand_forecast": forecast,
            "summary": f"Peak days: {', '.join([d['date'] for d in forecast if d['demand_multiplier'] > 2])}",
        }

    @staticmethod
    def get_nearby_events(
        latitude: float, longitude: float, radius_miles: float = 5
    ) -> dict[str, Any]:
        """Get events within a geographic radius."""
        # In production, would use geolocation service
        # For now, return all events as "nearby"

        return {
            "location": {"latitude": latitude, "longitude": longitude},
            "search_radius_miles": radius_miles,
            "events": EventsDataProvider.MOCK_EVENTS,
            "note": "Geolocation filtering not available in demo mode",
        }


class EventsMCPServer:
    """MCP server exposing events tools."""

    def __init__(self):
        self.provider = EventsDataProvider()

    def get_tools_schema(self) -> list[dict[str, Any]]:
        """Return tool schemas for MCP discovery."""
        return [
            {
                "name": "events_list",
                "description": "List local events within date range",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "city": {
                            "type": "string",
                            "description": "City name",
                        },
                        "date_range_days": {
                            "type": "integer",
                            "description": "Number of days to look ahead",
                            "default": 7,
                        },
                    },
                    "required": ["city"],
                },
            },
            {
                "name": "events_detail",
                "description": "Get detailed info about a specific event",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "event_id": {
                            "type": "string",
                            "description": "Event ID",
                        },
                    },
                    "required": ["event_id"],
                },
            },
            {
                "name": "events_demand_forecast",
                "description": "Get demand forecast based on upcoming events",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "city": {
                            "type": "string",
                            "description": "City name",
                        },
                        "days": {
                            "type": "integer",
                            "description": "Forecast period in days",
                            "default": 7,
                        },
                    },
                    "required": ["city"],
                },
            },
            {
                "name": "events_nearby",
                "description": "Get events near a geographic location",
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
                        "radius_miles": {
                            "type": "number",
                            "description": "Search radius in miles",
                            "default": 5,
                        },
                    },
                    "required": ["latitude", "longitude"],
                },
            },
        ]

    async def process_tool_call(
        self, tool_name: str, **kwargs
    ) -> dict[str, Any]:
        """Process tool calls."""
        if tool_name == "events_list":
            return self.provider.list_events(
                kwargs.get("city", "Downtown"),
                kwargs.get("date_range_days", 7),
            )
        elif tool_name == "events_detail":
            return self.provider.get_event_details(kwargs["event_id"])
        elif tool_name == "events_demand_forecast":
            return self.provider.get_demand_forecast_from_events(
                kwargs.get("city", "Downtown"),
                kwargs.get("days", 7),
            )
        elif tool_name == "events_nearby":
            return self.provider.get_nearby_events(
                kwargs["latitude"],
                kwargs["longitude"],
                kwargs.get("radius_miles", 5),
            )
        else:
            raise ValueError(f"Unknown tool: {tool_name}")


# Standalone server mode
if __name__ == "__main__":

    async def run_server():
        """Run MCP server for development/testing."""
        import uvicorn
        from fastapi import FastAPI, HTTPException

        app = FastAPI(title="Events MCP Server")
        server = EventsMCPServer()

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

        uvicorn.run(app, host="0.0.0.0", port=8083)

    asyncio.run(run_server())
