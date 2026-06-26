"""
Example: Using MCP in BobaMaster

This demonstrates how to use MCP clients for weather, supplier, and events data.
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parents[1]))


async def example_weather():
    """Example: Get weather forecast and use for demand prediction."""
    from app.services.mcp_client import get_mcp_client

    client = get_mcp_client()
    await client.initialize()

    print("\n=== WEATHER EXAMPLE ===")
    weather = await client.get_weather_forecast(
        lat=40.7580,  # NYC
        lon=-73.9855,
        days=7,
    )

    if weather:
        print(f"Location: {weather.get('location')}")
        forecast = weather.get("forecast", [])
        print(f"\nForecasts ({len(forecast)} days):")
        for day in forecast:
            print(
                f"  {day['date']}: {day['temp_high_f']}F, "
                f"Demand: {day['demand_multiplier']:.1f}x"
            )
    else:
        print("Weather server not available")


async def example_supplier():
    """Example: Check ingredient pricing and bulk discounts."""
    from app.services.mcp_client import get_mcp_client

    client = get_mcp_client()
    await client.initialize()

    print("\n=== SUPPLIER PRICING EXAMPLE ===")

    # Check current pricing
    pricing = await client.get_supplier_pricing("tapioca_pearls")
    if pricing and pricing.get("available"):
        print(f"Ingredient: {pricing['ingredient']}")
        print(f"Best price: ${pricing['best_price_per_unit']} per {pricing['unit']}")
        print(f"Best supplier: {pricing['best_supplier']}")

    # Get bulk discount pricing
    bulk = await client.call_tool(
        "supplier",
        "supplier_bulk_pricing",
        ingredient="tapioca_pearls",
        quantity=100,
    )
    if bulk:
        print(f"\nBulk order (100 lbs):")
        print(f"  Discount: {bulk['discount_applied_percent']}%")
        print(f"  Final price: ${bulk['final_price_per_unit']} per unit")
        print(f"  Total cost: ${bulk['total_cost']:.2f}")
        print(f"  Savings: ${bulk['savings_vs_base']:.2f}")


async def example_events():
    """Example: Get upcoming events and predict demand spikes."""
    from app.services.mcp_client import get_mcp_client

    client = get_mcp_client()
    await client.initialize()

    print("\n=== EVENTS EXAMPLE ===")

    # Get upcoming events
    events = await client.get_local_events(
        city="Downtown",
        date_range_days=7,
    )

    if events:
        print(f"Found {len(events)} events in next 7 days:")
        for event in events:
            print(f"\n  {event['name']}")
            print(f"    Date: {event['date']}")
            print(f"    Location: {event['location']}")
            print(f"    Attendance: {event['expected_attendance']}")
            print(f"    Demand impact: {event['demand_impact']:.1f}x")

    # Get demand forecast
    forecast = await client.call_tool(
        "events",
        "events_demand_forecast",
        city="Downtown",
        days=7,
    )
    if forecast:
        print(f"\nDemand forecast:")
        for day in forecast.get("demand_forecast", []):
            print(
                f"  {day['date']}: {day['demand_multiplier']:.1f}x "
                f"({', '.join(day['events'])})"
            )


async def example_enhanced_insights():
    """Example: Generate insights enriched with MCP data."""
    from app.agents.business_agent import get_business_agent
    from uuid import UUID

    print("\n=== ENHANCED BUSINESS INSIGHTS ===")

    agent = get_business_agent()
    shop_id = UUID("00000000-0000-0000-0000-000000000001")

    insights = agent.get_insights(shop_id)

    print(f"\nShop ID: {insights.shop_id}")
    print(f"Generated at: {insights.generated_at}")
    print(f"Demo mode: {insights.demo_mode}")

    print(f"\nRevenue estimate: ${insights.today_revenue_estimate:.2f}")
    print(f"Waste percentage: {insights.waste_percentage:.1f}%")
    print(f"Staff efficiency: {insights.staff_efficiency_score:.0f}%")

    print(f"\nPeak windows:")
    for window in insights.peak_windows:
        print(
            f"  {window.start_hour:02d}:00 - {window.end_hour:02d}:00: "
            f"{window.avg_cups_per_minute:.1f} cups/min "
            f"(confidence: {window.confidence:.0%})"
        )

    print(f"\nTop drinks:")
    for drink in insights.top_drinks:
        trend_icon = "↑" if drink.trend == "trending_up" else \
                    "↓" if drink.trend == "trending_down" else "→"
        print(
            f"  #{drink.popularity_rank} {drink.drink_name}: "
            f"{drink.cups_sold_today} cups, ${drink.revenue_estimate:.2f} {trend_icon}"
        )

    print(f"\nOptimization recommendations:")
    for rec in insights.inventory_optimizations:
        print(f"  {rec.ingredient_id}:")
        print(f"    Current: {rec.current_level_grams}g")
        print(f"    Recommended: {rec.recommended_level_grams}g")
        print(f"    Reason: {rec.reason}")
        if rec.savings_potential > 0:
            print(f"    Potential savings: {rec.savings_potential}g/day")


async def example_mcp_status():
    """Example: Check MCP status and available servers."""
    from app.services.mcp_client import get_mcp_client

    client = get_mcp_client()

    print("\n=== MCP STATUS CHECK ===")
    print(f"MCP client initialized: {client.initialized}")

    print(f"\nConfigured servers:")
    for name, config in client.servers.items():
        status = "ENABLED" if config.enabled else "DISABLED"
        print(f"  {name}: {config.url} [{status}]")

    if client.initialized:
        print(f"\nEnabled servers: {client.get_enabled_servers()}")

    print("\nServer configuration (mcp.json):")
    config = client.get_server_config()
    import json
    print(json.dumps(config, indent=2))


async def main():
    """Run all examples."""
    print("=" * 60)
    print("BobaMaster MCP Integration Examples")
    print("=" * 60)

    try:
        await example_mcp_status()
        await example_weather()
        await example_supplier()
        await example_events()
        await example_enhanced_insights()

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
