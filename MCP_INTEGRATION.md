# MCP Integration Guide

## Overview

BobaMaster now supports **Model Context Protocol (MCP)** integration for connecting external data sources to enhance business intelligence and operations decisions.

### MCP Servers Available

1. **Weather Server** (Port 8081)
   - Weather forecasts for demand correlation
   - Hourly weather predictions for intra-day planning
   - Seasonal demand adjustments
   - Tools: `weather_forecast`, `weather_hourly`, `weather_seasonal`

2. **Supplier Server** (Port 8082)
   - Real-time supplier pricing
   - Inventory availability checking
   - Bulk pricing with volume discounts
   - Price trend analysis
   - Tools: `supplier_get_pricing`, `supplier_check_availability`, `supplier_bulk_pricing`, `supplier_price_trends`

3. **Events Server** (Port 8083)
   - Local events calendar
   - Event-based demand forecasting
   - Nearby events detection
   - Peak prediction from concerts, sports, community events
   - Tools: `events_list`, `events_detail`, `events_demand_forecast`, `events_nearby`

---

## Quick Start

### 1. Enable MCP Support

**Install the MCP adapter:**

```bash
pip install langchain_mcp_adapters
```

**Or in the project root:**

```bash
cd backend
pip install -r requirements_mcp.txt
```

### 2. Configure MCP Servers

Create `.kiro/settings/mcp.json` (Kiro IDE) or `.mcp.json` (local development):

```json
{
  "mcpServers": {
    "weather": {
      "transport": "http",
      "url": "http://localhost:8081/mcp",
      "disabled": false
    },
    "supplier": {
      "transport": "http",
      "url": "http://localhost:8082/mcp",
      "disabled": false
    },
    "events": {
      "transport": "http",
      "url": "http://localhost:8083/mcp",
      "disabled": false
    }
  }
}
```

### 3. Start MCP Servers

Start each server in a separate terminal:

```bash
# Terminal 1: Weather server
cd backend
python -m app.mcp_servers.weather_server

# Terminal 2: Supplier server
python -m app.mcp_servers.supplier_server

# Terminal 3: Events server
python -m app.mcp_servers.events_server
```

Or use environment variables to enable/disable servers:

```bash
export MCP_WEATHER_ENABLED=true
export MCP_SUPPLIER_ENABLED=true
export MCP_EVENTS_ENABLED=true
```

### 4. Start BobaMaster Backend

```bash
cd backend
python -m app.main
```

### 5. Check MCP Status

```bash
curl http://localhost:8000/api/v1/mcp/status
```

Expected response:

```json
{
  "mcp_available": true,
  "initialized": true,
  "enabled_servers": ["weather", "supplier", "events"],
  "server_count": 3,
  "message": "MCP integration ready"
}
```

---

## API Reference

### MCP Configuration Endpoints

#### Check MCP Status
```
GET /api/v1/mcp/status
```

Returns whether MCP is available and initialized.

**Response:**
```json
{
  "mcp_available": true,
  "initialized": true,
  "enabled_servers": ["weather", "supplier", "events"],
  "server_count": 3
}
```

#### List Servers
```
GET /api/v1/mcp/servers
```

Returns all configured MCP servers.

**Response:**
```json
{
  "servers": [
    {
      "name": "weather",
      "url": "http://localhost:8081/mcp",
      "transport": "http",
      "enabled": true,
      "description": "Weather data and forecasts for demand correlation"
    }
  ],
  "total": 3,
  "enabled_count": 3
}
```

#### Get Tools from Server
```
GET /api/v1/mcp/tools/{server_name}
```

Returns available tools from a specific server (e.g., `weather`, `supplier`, `events`).

**Response:**
```json
{
  "server": "weather",
  "tool_count": 3,
  "tools": [
    {
      "name": "weather_forecast",
      "description": "Get weather forecast for demand correlation"
    },
    {
      "name": "weather_hourly",
      "description": "Get hourly weather forecast"
    }
  ]
}
```

#### Get MCP Configuration
```
GET /api/v1/mcp/config
```

Returns the full MCP configuration needed for setup.

---

## Weather Server Tools

### `weather_forecast`

Get 7-day weather forecast for demand correlation.

**Parameters:**
- `latitude` (required): Latitude coordinate
- `longitude` (required): Longitude coordinate
- `days` (optional): Number of days to forecast (default: 7)

**Example:**
```bash
curl -X POST http://localhost:8081/mcp/call_tool \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "weather_forecast",
    "latitude": 40.7580,
    "longitude": -73.9855,
    "days": 7
  }'
```

**Response:**
```json
{
  "location": { "lat": 40.7580, "lon": -73.9855 },
  "forecast": [
    {
      "date": "2024-06-27",
      "temp_high_f": 78,
      "temp_low_f": 63,
      "humidity_percent": 65,
      "rain_probability": 20,
      "conditions": "Partly Cloudy",
      "demand_multiplier": 1.2
    }
  ],
  "insights": [
    "Temperature will reach 92F in next 7 days",
    "Best sales days: 2024-06-27, 2024-06-28"
  ]
}
```

### `weather_hourly`

Get hourly weather for intra-day demand prediction.

**Parameters:**
- `latitude` (required)
- `longitude` (required)
- `hours` (optional): Hours to forecast (default: 24)

### `weather_seasonal`

Get seasonal demand adjustments.

**Parameters:**
- `date` (required): Date in YYYY-MM-DD format

---

## Supplier Server Tools

### `supplier_get_pricing`

Get current pricing for an ingredient.

**Parameters:**
- `ingredient` (required): Ingredient name

**Example:**
```bash
curl -X POST http://localhost:8082/mcp/call_tool \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "supplier_get_pricing",
    "ingredient": "tapioca_pearls"
  }'
```

**Response:**
```json
{
  "ingredient": "tapioca_pearls",
  "available": true,
  "best_price_per_unit": 2.50,
  "best_supplier": "BobaTech Wholesale",
  "unit": "lbs",
  "all_options": [
    {
      "supplier": "BobaTech Wholesale",
      "price_per_unit": 2.50,
      "min_order": 10,
      "lead_time_days": 2
    }
  ],
  "estimated_monthly_cost": 250.00
}
```

### `supplier_bulk_pricing`

Get volume discount pricing.

**Parameters:**
- `ingredient` (required)
- `quantity` (required): Quantity to order

**Response includes:**
- Base price per unit
- Discount percentage applied
- Final price per unit
- Total cost
- Savings calculation

### `supplier_check_availability`

Check if ingredient is in stock.

### `supplier_price_trends`

Get 30-day price history and trends.

---

## Events Server Tools

### `events_list`

Get upcoming local events.

**Parameters:**
- `city` (required): City name
- `date_range_days` (optional): Days to look ahead (default: 7)

**Example Response:**
```json
{
  "city": "Downtown",
  "events": [
    {
      "id": "evt_001",
      "name": "Downtown Street Fair",
      "date": "2024-06-30",
      "time": "10:00-18:00",
      "location": "Main Street",
      "expected_attendance": 5000,
      "category": "community_event",
      "demand_impact": 2.5
    }
  ]
}
```

### `events_demand_forecast`

Get demand forecast based on upcoming events.

**Returns:**
- Date-by-date demand multipliers
- List of events per date
- Recommendations for high-demand days

### `events_detail`

Get detailed information about a specific event.

**Parameters:**
- `event_id` (required): Event ID

**Response includes:**
- Event details
- Preparation recommendations
- Peak hour predictions

### `events_nearby`

Get events near a geographic location.

**Parameters:**
- `latitude` (required)
- `longitude` (required)
- `radius_miles` (optional): Search radius (default: 5)

---

## Integration with Business Intelligence

The Business Intelligence Agent automatically enriches insights with MCP data:

1. **Weather Integration**: Adjusts peak window predictions based on forecast
2. **Events Integration**: Incorporates event-based demand surges
3. **Supplier Integration**: Updates cost optimization recommendations with real pricing

MCP enrichment is **non-blocking** — Business Intelligence always returns insights immediately, with external data enriched asynchronously.

### Example: Impact on Insights

**Without MCP (Demo):**
```json
{
  "peak_windows": [
    { "start_hour": 11, "end_hour": 13, "avg_cups_per_minute": 12.5 }
  ],
  "today_revenue_estimate": 1476.00
}
```

**With MCP (Enriched):**
```json
{
  "peak_windows": [
    { "start_hour": 11, "end_hour": 13, "avg_cups_per_minute": 15.0 },
    { "start_hour": 18, "end_hour": 20, "avg_cups_per_minute": 18.0 }
  ],
  "today_revenue_estimate": 1890.00,
  "mcp_enhancements": {
    "weather_boost": 1.15,
    "event_surge": 1.25,
    "enriched_at": "2024-06-26T14:32:00Z"
  }
}
```

---

## Development & Testing

### Test Weather Server Locally

```python
from app.mcp_servers.weather_server import WeatherDataProvider

provider = WeatherDataProvider()
forecast = provider.get_forecast(40.7580, -73.9855, days=7)
print(forecast)
```

### Test Supplier Server Locally

```python
from app.mcp_servers.supplier_server import SupplierDataProvider

provider = SupplierDataProvider()
pricing = provider.get_pricing("tapioca_pearls")
print(pricing)

bulk = provider.get_bulk_pricing("tapioca_pearls", quantity=100)
print(bulk)
```

### Test Events Server Locally

```python
from app.mcp_servers.events_server import EventsDataProvider

provider = EventsDataProvider()
events = provider.list_events("Downtown", date_range_days=7)
print(events)

forecast = provider.get_demand_forecast_from_events("Downtown", days=7)
print(forecast)
```

---

## Production Deployment

### Docker Compose Setup

Create `docker-compose.yml`:

```yaml
version: '3.8'
services:
  weather:
    build: ./backend/app/mcp_servers/weather_server
    ports:
      - "8081:8081"
    environment:
      - MCP_WEATHER_ENABLED=true

  supplier:
    build: ./backend/app/mcp_servers/supplier_server
    ports:
      - "8082:8082"
    environment:
      - MCP_SUPPLIER_ENABLED=true

  events:
    build: ./backend/app/mcp_servers/events_server
    ports:
      - "8083:8083"
    environment:
      - MCP_EVENTS_ENABLED=true

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    depends_on:
      - weather
      - supplier
      - events
    environment:
      - MCP_WEATHER_ENABLED=true
      - MCP_WEATHER_URL=http://weather:8081/mcp
      - MCP_SUPPLIER_ENABLED=true
      - MCP_SUPPLIER_URL=http://supplier:8082/mcp
      - MCP_EVENTS_ENABLED=true
      - MCP_EVENTS_URL=http://events:8083/mcp
```

### Environment Variables

```bash
# Enable/disable specific servers
MCP_WEATHER_ENABLED=true
MCP_SUPPLIER_ENABLED=true
MCP_EVENTS_ENABLED=true

# Custom server URLs
MCP_WEATHER_URL=http://weather-service:8081/mcp
MCP_SUPPLIER_URL=http://supplier-service:8082/mcp
MCP_EVENTS_URL=http://events-service:8083/mcp
```

---

## Troubleshooting

### MCP Client Not Initialized

**Problem:** `"mcp_available": false`

**Solution:**
```bash
pip install langchain_mcp_adapters
```

### Servers Unreachable

**Problem:** MCP integration returns empty data

**Check:**
```bash
curl http://localhost:8081/mcp/tools
curl http://localhost:8082/mcp/tools
curl http://localhost:8083/mcp/tools
```

**Solution:** Restart MCP servers and ensure they're listening on correct ports.

### Long Response Times

**Problem:** Business Intelligence requests slow

**Solution:** MCP enrichment happens asynchronously. Responses should still be fast. Check server logs:
```bash
# Check Business Intelligence logs
curl http://localhost:8000/api/v1/business/insights/{shop_id}
```

---

## Next Steps

1. **Integrate Real Weather API**: Replace mock data with OpenWeatherMap or WeatherAPI
2. **Connect Real Supplier APIs**: Integrate with actual supplier systems
3. **Add Social Media Sentiment**: Monitor social media for event discussions
4. **Real-Time POS Data**: Stream POS data into demand forecasting
5. **Machine Learning**: Train models on historical weather + sales data

---

## Resources

- [Model Context Protocol Documentation](https://modelcontextprotocol.io/)
- [LangChain MCP Adapters](https://github.com/langchain-ai/langchain-mcp-adapters)
- [OpenWeatherMap API](https://openweathermap.org/api)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
