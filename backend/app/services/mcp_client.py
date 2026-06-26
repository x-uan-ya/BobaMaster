"""
MCP (Model Context Protocol) Client Integration

Provides a unified interface to connect external data sources:
  - Weather forecasting for demand correlation
  - Supplier pricing APIs for cost optimization
  - Demand forecasting services
  - Social media sentiment analysis
  - Local events calendar for peak prediction

Uses langchain_mcp_adapters to manage connections to multiple MCP servers.
Falls back gracefully if servers are unavailable.
"""

from __future__ import annotations

import logging
from typing import Optional, Any, dict
import os
import json
from datetime import datetime, timedelta

logger = logging.getLogger("BobaMaster.MCPClient")


class MCPServerConfig:
    """Configuration for a single MCP server."""

    def __init__(
        self,
        name: str,
        transport: str,
        url: str,
        description: str = "",
        enabled: bool = True,
    ):
        self.name = name
        self.transport = transport
        self.url = url
        self.description = description
        self.enabled = enabled

    def to_dict(self) -> dict:
        return {
            self.name: {
                "transport": self.transport,
                "url": self.url,
                "disabled": not self.enabled,
            }
        }


class MCPClient:
    """
    Unified MCP client for connecting to external data sources.

    Supports:
      - HTTP transport to external services
      - Tool discovery and invocation
      - Graceful fallback when services unavailable
    """

    def __init__(self):
        """Initialize MCP client with configured servers."""
        self.servers: dict[str, MCPServerConfig] = {}
        self.client = None
        self.initialized = False
        self._load_config()

    def _load_config(self) -> None:
        """Load MCP server configuration from environment or defaults."""
        # Default server configurations
        default_servers = [
            MCPServerConfig(
                name="weather",
                transport="http",
                url=os.getenv(
                    "MCP_WEATHER_URL", "http://localhost:8081/mcp"
                ),
                description="Weather data and forecasts for demand correlation",
                enabled=os.getenv("MCP_WEATHER_ENABLED", "false").lower() == "true",
            ),
            MCPServerConfig(
                name="supplier",
                transport="http",
                url=os.getenv(
                    "MCP_SUPPLIER_URL", "http://localhost:8082/mcp"
                ),
                description="Supplier APIs for pricing and inventory",
                enabled=os.getenv("MCP_SUPPLIER_ENABLED", "false").lower() == "true",
            ),
            MCPServerConfig(
                name="events",
                transport="http",
                url=os.getenv(
                    "MCP_EVENTS_URL", "http://localhost:8083/mcp"
                ),
                description="Local events calendar for peak prediction",
                enabled=os.getenv("MCP_EVENTS_ENABLED", "false").lower() == "true",
            ),
        ]

        for server in default_servers:
            self.servers[server.name] = server

    async def initialize(self) -> bool:
        """
        Initialize MCP client connections.

        Returns True if at least one server connected, False otherwise.
        """
        try:
            # Only attempt initialization if langchain_mcp_adapters is available
            from langchain_mcp_adapters.client import MultiServerMCPClient

            enabled_servers = {
                name: config.to_dict()[name]
                for name, config in self.servers.items()
                if config.enabled
            }

            if not enabled_servers:
                logger.info("No MCP servers enabled")
                self.initialized = False
                return False

            logger.info(f"Initializing {len(enabled_servers)} MCP servers...")
            self.client = MultiServerMCPClient(enabled_servers)
            self.initialized = True
            logger.info("MCP client initialized successfully")
            return True

        except ImportError:
            logger.warning(
                "langchain_mcp_adapters not installed. MCP features disabled. "
                "Install with: pip install langchain_mcp_adapters"
            )
            self.initialized = False
            return False
        except Exception as e:
            logger.error(f"Failed to initialize MCP client: {e}")
            self.initialized = False
            return False

    async def get_tools(self, server_name: str) -> list[Any]:
        """
        Get available tools from a specific MCP server.

        Args:
            server_name: Name of the server (e.g., "weather", "supplier")

        Returns:
            List of tool objects, or empty list if server unavailable
        """
        if not self.initialized or not self.client:
            logger.debug(f"MCP client not initialized, cannot fetch tools from {server_name}")
            return []

        try:
            tools = await self.client.get_tools()
            return [t for t in tools if t.name.startswith(f"{server_name}_")]
        except Exception as e:
            logger.error(f"Error fetching tools from {server_name}: {e}")
            return []

    async def call_tool(
        self, server_name: str, tool_name: str, **kwargs
    ) -> Optional[Any]:
        """
        Call a specific tool on an MCP server.

        Args:
            server_name: Name of the server
            tool_name: Name of the tool to call
            **kwargs: Tool parameters

        Returns:
            Tool result, or None if failed
        """
        if not self.initialized or not self.client:
            logger.debug(f"MCP client not initialized, cannot call {tool_name}")
            return None

        try:
            # Construct full tool name
            full_tool_name = f"{server_name}_{tool_name}"
            result = await self.client.invoke(full_tool_name, kwargs)
            logger.debug(f"Tool {full_tool_name} executed successfully")
            return result
        except Exception as e:
            logger.error(f"Error calling tool {server_name}.{tool_name}: {e}")
            return None

    async def get_weather_forecast(
        self, lat: float, lon: float, days: int = 7
    ) -> Optional[dict]:
        """
        Get weather forecast for demand correlation.

        Args:
            lat: Latitude
            lon: Longitude
            days: Number of days to forecast

        Returns:
            Weather forecast data, or None if unavailable
        """
        return await self.call_tool(
            "weather", "forecast", latitude=lat, longitude=lon, days=days
        )

    async def get_supplier_pricing(
        self, ingredient_name: str
    ) -> Optional[dict]:
        """
        Get current supplier pricing for ingredient cost optimization.

        Args:
            ingredient_name: Name of ingredient

        Returns:
            Pricing data from suppliers, or None if unavailable
        """
        return await self.call_tool(
            "supplier", "get_pricing", ingredient=ingredient_name
        )

    async def get_local_events(
        self, city: str, date_range_days: int = 7
    ) -> Optional[list[dict]]:
        """
        Get local events that might impact demand.

        Args:
            city: City name
            date_range_days: Number of days to check

        Returns:
            List of events, or None if unavailable
        """
        return await self.call_tool(
            "events",
            "list_events",
            city=city,
            date_range_days=date_range_days,
        )

    def get_enabled_servers(self) -> list[str]:
        """Get list of enabled MCP server names."""
        return [name for name, config in self.servers.items() if config.enabled]

    def get_server_config(self) -> dict:
        """Get full MCP configuration suitable for mcp.json format."""
        config = {"mcpServers": {}}
        for name, server in self.servers.items():
            if server.enabled:
                config["mcpServers"].update(server.to_dict())
        return config


# Singleton instance
_mcp_client: Optional[MCPClient] = None


def get_mcp_client() -> MCPClient:
    """Get or create MCP client singleton."""
    global _mcp_client
    if _mcp_client is None:
        _mcp_client = MCPClient()
    return _mcp_client


async def initialize_mcp() -> bool:
    """
    Initialize the MCP client.

    Should be called on application startup.
    """
    client = get_mcp_client()
    return await client.initialize()
