# MCP Setup Guide - Step by Step

This guide walks through setting up MCP integration with BobaMaster for enhanced business intelligence.

## What MCP Adds

MCP (Model Context Protocol) connects BobaMaster to external data sources:

- **Weather Data**: Correlate temperature with demand to predict peak hours
- **Supplier Pricing**: Get real-time costs to optimize inventory purchasing
- **Local Events**: Predict demand spikes from concerts, sports games, community events

All data enriches the Business Intelligence dashboard to help managers make better decisions.

---

## Prerequisites

- BobaMaster backend and frontend installed
- Python 3.10+ installed
- Terminal/command prompt access
- 3 available ports: 8081 (weather), 8082 (supplier), 8083 (events)

---

## Step 1: Install MCP Dependencies

### Option A: Using requirements_mcp.txt (Recommended)

```bash
cd backend
pip install -r requirements_mcp.txt
```

### Option B: Manual Installation

```bash
pip install langchain_mcp_adapters langchain langchain_openai
```

**Verify installation:**
```bash
python -c "from langchain_mcp_adapters.client import MultiServerMCPClient; print('MCP installed successfully')"
```

---

## Step 2: Start MCP Servers

You'll need **3 terminal windows** open. In each, run one server.

### Terminal 1: Start Weather Server

```bash
cd backend
python -m app.mcp_servers.weather_server
```

Expected output:
```
INFO:     Uvicorn running on http://0.0.0.0:8081
```

**Test it:**
```bash
curl http://localhost:8081/mcp/tools
```

### Terminal 2: Start Supplier Server

```bash
cd backend
python -m app.mcp_servers.supplier_server
```

Expected output:
```
INFO:     Uvicorn running on http://0.0.0.0:8082
```

### Terminal 3: Start Events Server

```bash
cd backend
python -m app.mcp_servers.events_server
```

Expected output:
```
INFO:     Uvicorn running on http://0.0.0.0:8083
```

### Terminal 4: Start Backend

```bash
cd backend
python -m app.main
```

Expected output:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

## Step 3: Verify MCP Integration

Check that all servers are running and connected:

```bash
curl http://localhost:8000/api/v1/mcp/status
```

**Expected response:**
```json
{
  "mcp_available": true,
  "initialized": true,
  "enabled_servers": ["weather", "supplier", "events"],
  "server_count": 3,
  "message": "MCP integration ready"
}
```

If you get `"mcp_available": false`, install MCP dependencies (Step 1).

---

## Step 4: Test Each MCP Server

### Test Weather Server

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

You should get a forecast with demand multipliers.

### Test Supplier Server

```bash
curl -X POST http://localhost:8082/mcp/call_tool \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "supplier_get_pricing",
    "ingredient": "tapioca_pearls"
  }'
```

You should get pricing from multiple suppliers.

### Test Events Server

```bash
curl -X POST http://localhost:8083/mcp/call_tool \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "events_list",
    "city": "Downtown",
    "date_range_days": 7
  }'
```

You should get upcoming local events.

---

## Step 5: Enable MCP in Kiro IDE (Optional)

If you're using Kiro IDE, you can configure MCP through the UI.

### Create `.kiro/settings/mcp.json`

Create the directory if it doesn't exist:

```bash
mkdir -p .kiro/settings
```

Create `mcp.json`:

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

The MCP servers are now available in Kiro's MCP tool integration.

---

## Step 6: Use MCP Data in Business Intelligence

Open the Business Insights dashboard:

1. Start the frontend: `npm run dev` (in frontend directory)
2. Navigate to `http://localhost:5173`
3. Click "Insights" in the left sidebar
4. The dashboard now includes MCP-enhanced data:
   - Weather-adjusted peak windows
   - Event-based demand forecasts
   - Supplier pricing recommendations

---

## Configuration

### Environment Variables

Control which servers are enabled:

```bash
export MCP_WEATHER_ENABLED=true
export MCP_SUPPLIER_ENABLED=true
export MCP_EVENTS_ENABLED=true

# Override server URLs
export MCP_WEATHER_URL=http://localhost:8081/mcp
export MCP_SUPPLIER_URL=http://localhost:8082/mcp
export MCP_EVENTS_URL=http://localhost:8083/mcp
```

### Disable Specific Servers

Edit `backend/app/services/mcp_client.py` and change:

```python
enabled=os.getenv("MCP_WEATHER_ENABLED", "false").lower() == "true",
```

Or set environment variable:

```bash
export MCP_WEATHER_ENABLED=false
```

---

## Development: Running Standalone Servers

Each MCP server can run independently for testing:

### Weather Server
```bash
python -m app.mcp_servers.weather_server
# Available at http://localhost:8081
```

### Supplier Server
```bash
python -m app.mcp_servers.supplier_server
# Available at http://localhost:8082
```

### Events Server
```bash
python -m app.mcp_servers.events_server
# Available at http://localhost:8083
```

---

## Troubleshooting

### Problem: "mcp_available: false"

**Cause:** `langchain_mcp_adapters` not installed

**Solution:**
```bash
pip install langchain_mcp_adapters
```

### Problem: Servers timeout or not responding

**Check ports are open:**
```bash
netstat -an | findstr "8081\|8082\|8083\|8000"  # Windows
lsof -i :8081  # Mac/Linux
```

**Solution:** Change port numbers if already in use, or stop conflicting processes.

### Problem: MCP Integration doesn't enriched insights

**Check server status:**
```bash
curl http://localhost:8000/api/v1/mcp/status
```

**Check server tools:**
```bash
curl http://localhost:8000/api/v1/mcp/servers
```

### Problem: "Connection refused" errors

**Ensure servers are running:**
```bash
# Terminal 1
python -m app.mcp_servers.weather_server

# Terminal 2
python -m app.mcp_servers.supplier_server

# Terminal 3
python -m app.mcp_servers.events_server

# Terminal 4
python -m app.main
```

---

## Next Steps

1. **Integrate Real Weather API**: Replace mock data in `weather_server.py` with OpenWeatherMap
2. **Connect Real Suppliers**: Integrate actual supplier REST APIs
3. **Add More Events**: Connect to EventBrite or local event APIs
4. **Monitor Performance**: Check enrichment speed and adjust caching
5. **Train ML Models**: Use historical data + MCP sources for better predictions

---

## Production Deployment

### Using Docker Compose

Create a `docker-compose.yml` at project root:

```yaml
version: '3.8'
services:
  weather:
    build:
      context: .
      dockerfile: Dockerfile.weather
    ports:
      - "8081:8081"
    environment:
      - MCP_WEATHER_ENABLED=true

  supplier:
    build:
      context: .
      dockerfile: Dockerfile.supplier
    ports:
      - "8082:8082"

  events:
    build:
      context: .
      dockerfile: Dockerfile.events
    ports:
      - "8083:8083"

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
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

Then deploy:
```bash
docker-compose up
```

### Using Kubernetes

Deploy each MCP server as a separate pod, then configure backend with service DNS names.

---

## API Reference

### Check MCP Status
```
GET /api/v1/mcp/status
```

### List Configured Servers
```
GET /api/v1/mcp/servers
```

### Get Tools from Server
```
GET /api/v1/mcp/tools/{server_name}
```

### Get MCP Configuration
```
GET /api/v1/mcp/config
```

---

## Support

For issues or questions:

1. Check logs: `tail -f backend/bobamaster.log`
2. Test individual servers: `curl http://localhost:808x/mcp/tools`
3. Review MCP_INTEGRATION.md for detailed documentation
4. Check Python version: `python --version` (requires 3.10+)

---

## Summary

You now have MCP integration running! 

- **3 External Data Sources**: Weather, Supplier Pricing, Local Events
- **Enhanced BI Dashboard**: Shows enriched insights with MCP data
- **Production Ready**: Can scale to Docker/Kubernetes deployment

Start exploring the Business Intelligence dashboard to see MCP in action.
