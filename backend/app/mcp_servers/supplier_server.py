"""
Supplier MCP Server Implementation

Provides pricing and availability data for cost optimization.
Integrates with supplier APIs to track ingredient costs and bulk pricing.

Can be run standalone:
  python -m app.mcp_servers.supplier_server
"""

from __future__ import annotations

import logging
import json
from datetime import datetime, timedelta
from typing import Any
import asyncio

logger = logging.getLogger("BobaMaster.SupplierServer")


class SupplierDataProvider:
    """Simulates supplier API calls with realistic pricing."""

    # Mock supplier database
    SUPPLIERS = {
        "tapioca_pearls": [
            {
                "supplier": "BobaTech Wholesale",
                "unit": "lbs",
                "price_per_unit": 2.50,
                "min_order": 10,
                "lead_time_days": 2,
                "volume_discounts": [
                    {"quantity": 50, "discount_percent": 5},
                    {"quantity": 100, "discount_percent": 10},
                ],
            },
            {
                "supplier": "Pearl Paradise Inc",
                "unit": "lbs",
                "price_per_unit": 2.70,
                "min_order": 5,
                "lead_time_days": 1,
                "volume_discounts": [
                    {"quantity": 30, "discount_percent": 3},
                ],
            },
        ],
        "black_tea": [
            {
                "supplier": "Tea Masters Co",
                "unit": "lbs",
                "price_per_unit": 12.00,
                "min_order": 2,
                "lead_time_days": 3,
                "volume_discounts": [
                    {"quantity": 10, "discount_percent": 8},
                ],
            },
        ],
        "matcha_powder": [
            {
                "supplier": "Premium Matcha Ltd",
                "unit": "oz",
                "price_per_unit": 0.80,
                "min_order": 16,
                "lead_time_days": 5,
                "volume_discounts": [
                    {"quantity": 64, "discount_percent": 12},
                ],
            },
        ],
        "brown_sugar": [
            {
                "supplier": "Sugar Source Global",
                "unit": "lbs",
                "price_per_unit": 0.60,
                "min_order": 20,
                "lead_time_days": 2,
                "volume_discounts": [],
            },
        ],
    }

    @staticmethod
    def get_pricing(ingredient: str) -> dict[str, Any]:
        """Get current pricing for an ingredient from multiple suppliers."""
        ingredient_key = ingredient.lower().replace(" ", "_")

        if ingredient_key not in SupplierDataProvider.SUPPLIERS:
            return {
                "ingredient": ingredient,
                "available": False,
                "message": f"No suppliers found for {ingredient}",
            }

        suppliers = SupplierDataProvider.SUPPLIERS[ingredient_key]
        best_price = min(s["price_per_unit"] for s in suppliers)
        best_supplier = next(
            s for s in suppliers if s["price_per_unit"] == best_price
        )

        return {
            "ingredient": ingredient,
            "available": True,
            "best_price_per_unit": best_price,
            "best_supplier": best_supplier["supplier"],
            "unit": best_supplier["unit"],
            "all_options": suppliers,
            "estimated_monthly_cost": best_price * 100,  # Assume 100 units/month baseline
            "last_updated": datetime.utcnow().isoformat(),
        }

    @staticmethod
    def check_availability(
        ingredient: str, quantity: int, unit: str = "lbs"
    ) -> dict[str, Any]:
        """Check if ingredient is in stock at suppliers."""
        ingredient_key = ingredient.lower().replace(" ", "_")

        if ingredient_key not in SupplierDataProvider.SUPPLIERS:
            return {
                "ingredient": ingredient,
                "quantity": quantity,
                "available": False,
            }

        suppliers = SupplierDataProvider.SUPPLIERS[ingredient_key]
        available_suppliers = [
            s
            for s in suppliers
            if s["min_order"] <= quantity and s.get("stock", True)
        ]

        return {
            "ingredient": ingredient,
            "quantity_requested": quantity,
            "unit": unit,
            "available": len(available_suppliers) > 0,
            "available_suppliers": [
                {
                    "name": s["supplier"],
                    "lead_time_days": s["lead_time_days"],
                    "price_per_unit": s["price_per_unit"],
                }
                for s in available_suppliers
            ],
            "checked_at": datetime.utcnow().isoformat(),
        }

    @staticmethod
    def get_bulk_pricing(ingredient: str, quantity: int) -> dict[str, Any]:
        """Get pricing with volume discounts."""
        pricing = SupplierDataProvider.get_pricing(ingredient)

        if not pricing["available"]:
            return pricing

        base_price = pricing["best_price_per_unit"]
        best_supplier_data = next(
            (s for s in pricing["all_options"] if s["supplier"] == pricing["best_supplier"]),
            None,
        )

        if not best_supplier_data:
            return pricing

        # Apply volume discount
        discounts = best_supplier_data.get("volume_discounts", [])
        discount_percent = 0
        for discount in discounts:
            if quantity >= discount["quantity"]:
                discount_percent = discount["discount_percent"]

        final_price = base_price * (1 - discount_percent / 100)
        total_cost = final_price * quantity

        return {
            "ingredient": ingredient,
            "quantity": quantity,
            "unit": best_supplier_data["unit"],
            "base_price_per_unit": base_price,
            "discount_applied_percent": discount_percent,
            "final_price_per_unit": final_price,
            "total_cost": total_cost,
            "supplier": pricing["best_supplier"],
            "savings_vs_base": base_price * quantity - total_cost,
        }

    @staticmethod
    def get_price_trends(ingredient: str, days: int = 30) -> dict[str, Any]:
        """Get historical price trends."""
        import random

        pricing = SupplierDataProvider.get_pricing(ingredient)

        if not pricing["available"]:
            return pricing

        base_price = pricing["best_price_per_unit"]
        trend = []

        for day in range(days):
            # Simulate realistic price fluctuations
            variation = random.uniform(-0.05, 0.05)
            price = base_price * (1 + variation)
            trend.append(
                {
                    "date": (
                        datetime.utcnow() - timedelta(days=days - day)
                    ).isoformat(),
                    "price": round(price, 2),
                }
            )

        avg_price = sum(t["price"] for t in trend) / len(trend)
        min_price = min(t["price"] for t in trend)
        max_price = max(t["price"] for t in trend)

        return {
            "ingredient": ingredient,
            "days": days,
            "current_price": base_price,
            "average_price": round(avg_price, 2),
            "min_price": min_price,
            "max_price": max_price,
            "price_trend": trend,
            "recommendation": "Prices stable" if max_price - min_price < 0.1 else
                             "Prices rising" if trend[-1]["price"] > avg_price else
                             "Prices falling",
        }


class SupplierMCPServer:
    """MCP server exposing supplier tools."""

    def __init__(self):
        self.provider = SupplierDataProvider()

    def get_tools_schema(self) -> list[dict[str, Any]]:
        """Return tool schemas for MCP discovery."""
        return [
            {
                "name": "supplier_get_pricing",
                "description": "Get current pricing for an ingredient",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "ingredient": {
                            "type": "string",
                            "description": "Ingredient name",
                        },
                    },
                    "required": ["ingredient"],
                },
            },
            {
                "name": "supplier_check_availability",
                "description": "Check if ingredient is available at suppliers",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "ingredient": {
                            "type": "string",
                            "description": "Ingredient name",
                        },
                        "quantity": {
                            "type": "integer",
                            "description": "Quantity needed",
                        },
                        "unit": {
                            "type": "string",
                            "description": "Unit (lbs, oz, etc)",
                        },
                    },
                    "required": ["ingredient", "quantity"],
                },
            },
            {
                "name": "supplier_bulk_pricing",
                "description": "Get bulk pricing with volume discounts",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "ingredient": {
                            "type": "string",
                            "description": "Ingredient name",
                        },
                        "quantity": {
                            "type": "integer",
                            "description": "Quantity to order",
                        },
                    },
                    "required": ["ingredient", "quantity"],
                },
            },
            {
                "name": "supplier_price_trends",
                "description": "Get historical price trends",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "ingredient": {
                            "type": "string",
                            "description": "Ingredient name",
                        },
                        "days": {
                            "type": "integer",
                            "description": "Number of days to analyze",
                            "default": 30,
                        },
                    },
                    "required": ["ingredient"],
                },
            },
        ]

    async def process_tool_call(
        self, tool_name: str, **kwargs
    ) -> dict[str, Any]:
        """Process tool calls."""
        if tool_name == "supplier_get_pricing":
            return self.provider.get_pricing(kwargs["ingredient"])
        elif tool_name == "supplier_check_availability":
            return self.provider.check_availability(
                kwargs["ingredient"],
                kwargs["quantity"],
                kwargs.get("unit", "lbs"),
            )
        elif tool_name == "supplier_bulk_pricing":
            return self.provider.get_bulk_pricing(
                kwargs["ingredient"],
                kwargs["quantity"],
            )
        elif tool_name == "supplier_price_trends":
            return self.provider.get_price_trends(
                kwargs["ingredient"],
                kwargs.get("days", 30),
            )
        else:
            raise ValueError(f"Unknown tool: {tool_name}")


# Standalone server mode
if __name__ == "__main__":

    async def run_server():
        """Run MCP server for development/testing."""
        import uvicorn
        from fastapi import FastAPI, HTTPException

        app = FastAPI(title="Supplier MCP Server")
        server = SupplierMCPServer()

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

        uvicorn.run(app, host="0.0.0.0", port=8082)

    asyncio.run(run_server())
