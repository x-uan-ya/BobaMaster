"""
MCP (Model Context Protocol) Configuration API — Feature Extension

Exposes MCP server status, available tools, and configuration.
Allows managers to connect external data sources for better insights.

Endpoints:
  - GET /api/v1/mcp/status - Check MCP initialization status
  - GET /api/v1/mcp/servers - List configured MCP servers
  - GET /api/v1/mcp/tools/{server_name} - Get available tools from a server
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, status

logger = logging.getLogger("BobaMaster.API.MCP")
router = APIRouter()


@router.get(
    "/status",
    status_code=status.HTTP_200_OK,
    summary="Check MCP client status",
    description="Returns whether MCP integration is available and initialized.",
)
async def get_mcp_status():
    """Get MCP client initialization status."""
    try:
        from app.services.mcp_client import get_mcp_client

        client = get_mcp_client()
        enabled_servers = client.get_enabled_servers()

        return {
            "mcp_available": True,
            "initialized": client.initialized,
            "enabled_servers": enabled_servers,
            "server_count": len(enabled_servers),
            "message": "MCP integration ready"
            if client.initialized
            else "MCP client not initialized. Ensure MCP servers are running.",
        }
    except ImportError:
        return {
            "mcp_available": False,
            "initialized": False,
            "enabled_servers": [],
            "server_count": 0,
            "message": "MCP support not installed. "
            "Install with: pip install langchain_mcp_adapters",
        }
    except Exception as e:
        logger.error(f"Error checking MCP status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check MCP status: {str(e)}",
        )


@router.get(
    "/servers",
    status_code=status.HTTP_200_OK,
    summary="List configured MCP servers",
    description="Returns all configured MCP servers and their status.",
)
async def list_mcp_servers():
    """Get list of configured MCP servers."""
    try:
        from app.services.mcp_client import get_mcp_client

        client = get_mcp_client()
        servers = []

        for name, config in client.servers.items():
            servers.append(
                {
                    "name": name,
                    "url": config.url,
                    "transport": config.transport,
                    "enabled": config.enabled,
                    "description": config.description,
                }
            )

        return {
            "servers": servers,
            "total": len(servers),
            "enabled_count": sum(1 for s in servers if s["enabled"]),
        }
    except ImportError:
        return {
            "servers": [],
            "total": 0,
            "enabled_count": 0,
            "message": "MCP support not installed",
        }
    except Exception as e:
        logger.error(f"Error listing MCP servers: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list MCP servers: {str(e)}",
        )


@router.get(
    "/tools/{server_name}",
    status_code=status.HTTP_200_OK,
    summary="Get tools from a specific MCP server",
    description="Returns available tools from a specific MCP server.",
)
async def get_mcp_tools(server_name: str):
    """Get tools available from a specific MCP server."""
    try:
        from app.services.mcp_client import get_mcp_client

        client = get_mcp_client()

        if server_name not in client.servers:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Server '{server_name}' not found",
            )

        if not client.initialized:
            return {
                "server": server_name,
                "tools": [],
                "message": "MCP client not initialized",
            }

        tools = await client.get_tools(server_name)

        return {
            "server": server_name,
            "tool_count": len(tools),
            "tools": [{"name": t.name, "description": t.description} for t in tools],
        }
    except ImportError:
        return {
            "server": server_name,
            "tools": [],
            "message": "MCP support not installed",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching tools from {server_name}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch tools: {str(e)}",
        )


@router.get(
    "/config",
    status_code=status.HTTP_200_OK,
    summary="Get MCP configuration",
    description="Returns the MCP configuration needed for mcp.json setup.",
)
async def get_mcp_config():
    """Get MCP configuration for manual setup."""
    try:
        from app.services.mcp_client import get_mcp_client

        client = get_mcp_client()
        config = client.get_server_config()

        return {
            "mcp_config": config,
            "note": "Add this to your .kiro/settings/mcp.json file "
            "to enable MCP integration",
            "instructions": [
                "1. Open .kiro/settings/mcp.json in your editor",
                "2. Copy the mcpServers section from mcp_config",
                "3. Ensure each server is running (weather on 8081, supplier on 8082, events on 8083)",
                "4. Restart Kiro to load the configuration",
            ],
        }
    except Exception as e:
        logger.error(f"Error getting MCP config: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get MCP config: {str(e)}",
        )
