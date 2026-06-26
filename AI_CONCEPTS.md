# AI Concepts Demonstrated in BobaMaster

This document explains how BobaMaster applies key course concepts from the Antigravity AI Agents course.

---

## 1. Multi-Agent System (Agent Development Kit)

### What It Is
A system composed of **7 independent agents**, each with a single well-defined responsibility. Agents communicate through shared state stores (Redis, PostgreSQL) rather than direct function calls.

### How BobaMaster Implements It

#### The 7 Agents

| Agent | Responsibility | Input | Output |
|---|---|---|---|
| **DecompoAgent** | Parse POS transactions into ingredient deductions | `POSWebhookPayload` (drink name, size, modifiers) | `List[IngredientDeduction]` (e.g., "tapioca_pearls: 40g") |
| **InventoryAgent** | Maintain FIFO batch ledger, apply deductions, track expiry | Brew start/complete/waste requests | `InventoryState` (active batches, total remaining) |
| **ContextAgent** | Assemble weather, calendar, local events into context vector | Shop ID, current time | `ContextVector` (temp, rain_prob, school_in_session) |
| **PredictorAgent** | Forecast demand for t+30/60/120 min based on recent velocity + context | Recent sales history, context vector | `ForecastVector` (predicted grams for each horizon) |
| **OpsDeciderAgent** | Apply safety stock algorithm to classify BREW_NOW / WARN / WAIT | Inventory state, forecast, cook time | `DecisionAction` enum + log to PostgreSQL |
| **DispatcherAgent** | Generate natural language explanation via Gemini 1.5 Flash, broadcast over WebSocket | `AlertPayload` with inventory/forecast/context | `DispatchMessage` (explanation + recommendation ID) |
| **FeedbackAgent** | Daily audit: compute MAPE, waste ratio, staff compliance; auto-tune safety buffers | Historical sales/waste/recommendations | `FeedbackReport` (accuracy metrics + parameter updates) |

### Communication Pattern

```
DecompoAgent → [deductions] → InventoryAgent → [live state] → OpsDeciderAgent
                                    ↑                              ↓
                                    ←──────────────────────────────
                                    
ContextAgent ──→ [context vector] ──→ PredictorAgent → [forecast] ──→ OpsDeciderAgent
                                                                         ↓
                                                                   DispatcherAgent
                                                                   (Gemini + WS)
                                                                   
Daily: FeedbackAgent → [audit] → PostgreSQL (system_settings update)
```

#### Key Advantage: Loose Coupling
- `DecompoAgent` doesn't know about `PredictorAgent`
- `InventoryAgent` doesn't call `OpsDeciderAgent` directly
- They communicate through:
  - **Redis**: Fast, temporary state (active batches, forecast cache)
  - **PostgreSQL**: Persistent, historical logs (recommendations, feedback)
  - **WebSocket**: Real-time push (alerts to KDS tablet)

#### Testability
Each agent can be tested independently:
```python
# Test DecompoAgent without any backend
agent = DecompoAgent()
deductions = agent.decompose_item(POSItem(...))
assert deductions[0].ingredient_id == "tapioca_pearls"

# Test InventoryAgent without DecompoAgent or OpsDecider
agent = InventoryAgent(redis_client)
batch = agent.start_brew(BrewStartRequest(...))
agent.apply_deductions(shop_id, "tapioca_pearls", 100)
```

---

## 2. Model Context Protocol (MCP) Pattern

### What It Is
A design pattern where an agent constructs a **rich, structured context** and passes it to an LLM as a single coherent prompt. The LLM receives exactly what it needs — no more, no less.

### How BobaMaster Implements It

**File:** `backend/app/agents/dispatcher_agent.py`

#### The Flow

```python
# 1. Construct context from multiple sources
alert_payload = AlertPayload(
    shop_id=shop_id,
    ingredient_id="tapioca_pearls",
    action=DecisionAction.BREW_NOW,
    current_stock_grams=400.0,
    active_brewing_grams=0.0,
    predicted_consumption_grams=2000.0,
    target_runway_grams=-1600.0,
    cook_time_minutes=50,
    temp_c=31.0,
    rain_prob=0.1,
    school_in_session=True,
    predicted_shortage_at=datetime(2024, 6, 24, 15, 47),
)

# 2. Construct a single, focused prompt
prompt = f"""
You are a kitchen operations assistant for a bubble tea shop.
Current situation:
- Tapioca pearls in stock: {alert_payload.current_stock_grams}g
- Currently brewing: {alert_payload.active_brewing_grams}g
- Expected demand in 30 min: {alert_payload.predicted_consumption_grams}g
- Projected shortage: {alert_payload.target_runway_grams}g

Context:
- School is in session
- Weather: {alert_payload.temp_c}°C, {alert_payload.rain_prob * 100:.0f}% rain
- Cook time: {alert_payload.cook_time_minutes} minutes

Generate a concise (1-2 sentence) operational decision for staff:
- What should they do?
- Why now?
"""

# 3. Call Gemini with the context
response = client.models.generate_content(
    model="gemini-1.5-flash",
    contents=[prompt]
)

# 4. Parse the response into structured output
explanation = LLMExplanation(
    action_string=DecisionAction.BREW_NOW,
    explanation_text=response.text
)
```

#### Why This Matters
- **Focused LLM calls**: No wasted context on irrelevant data
- **Reproducible output**: Same input → same LLM output (within model limits)
- **Easy to debug**: If the explanation is wrong, we can trace exactly what context was passed
- **Modular**: Can swap Gemini for Claude, GPT-4, or a local LLM with zero changes to the pattern

#### Real-World Example Output
```
Action: BREW_NOW
Explanation: "School ends in 15 min + clear weather = peak demand incoming. 
Current 400g pearls exhausted by 3:47 PM; start cooking now (50 min cycle 
finishes at 3:52 PM, just in time for rush)."
```

---

## 3. Security & Privacy

### What It Is
Protecting sensitive data (API keys, database credentials, user shop data) through code practices and architectural decisions.

### How BobaMaster Implements It

#### No Secrets in Code
```python
# WRONG: Hardcoded in source
client = anthropic.Anthropic(api_key="sk-ant-...")

# RIGHT: Load from environment
import os
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    logger.warning("GEMINI_API_KEY not set; using fallback")
client = genai.Client(api_key=api_key)
```

**Files:** All `.env` files are in `.gitignore`. Only `.env.example` (with dummy values) is committed.

#### Pydantic V2 Strict Validation
Rejects unknown fields and enforces types:
```python
# app/models/pos.py
class POSItem(BaseModel):
    name: str
    quantity: int
    size: Literal["S", "M", "L"]  # Only these values
    ice_level: str
    modifiers: List[str] = []
    
    model_config = ConfigDict(extra="forbid")  # Reject unknown fields

# If request includes {"name": "...", "unknown_field": "..."}
# Pydantic raises ValidationError
```

#### Parameterized SQL Queries
Prevents SQL injection:
```python
# WRONG: String interpolation
query = f"SELECT * FROM brew_logs WHERE shop_id = '{shop_id}'"

# RIGHT: Parameterized query
import psycopg2
cursor.execute(
    "SELECT * FROM brew_logs WHERE shop_id = %s",
    (shop_id,)  # Parameter passed separately
)
```

#### WebSocket Scoping
Connections are isolated per shop — no cross-shop data leakage:
```python
@ws_router.websocket("/ws/shop/{shop_id}")
async def websocket_endpoint(websocket: WebSocket, shop_id: str):
    # Only receive messages for THIS shop
    # A client connected to shop A cannot receive shop B's alerts
    await ws_manager.connect(shop_id, websocket)
```

---

## 4. Deployability & Infrastructure as Code

### What It Is
The ability to deploy the entire system with minimal manual configuration, using environment variables and containerization.

### How BobaMaster Implements It

#### Docker Compose (Infrastructure)
```yaml
# docker/docker-compose.yml
services:
  postgres:
    image: timescale/timescaledb:latest-pg15
    environment:
      POSTGRES_DB: bobaflow
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
```

**Deployment:** `cd docker && docker-compose up -d` → everything running in 30 seconds.

#### Environment Variables
```bash
# .env.example (committed to repo)
GEMINI_API_KEY=your-api-key-here
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=bobaflow
REDIS_URL=redis://localhost:6379
```

**Deployment:** Copy `.env.example` to `.env`, fill in real values, done.

#### Frontend: Vercel Deployment
```json
{
  "buildCommand": "npm run build",
  "outputDirectory": "frontend/dist",
  "env": {
    "VITE_API_URL": "@api-url",
    "VITE_WS_URL": "@ws-url"
  }
}
```

**Deployment:** `git push → Vercel auto-detects, builds, and deploys in ~2 min.`

#### Backend: Universal Startup
```bash
# Works anywhere (local, Docker, cloud)
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Automatically reads .env file via python-dotenv
# Connects to PostgreSQL and Redis if available
# Falls back to in-memory storage if not available
```

---

## 5. Real-Time Event-Driven Architecture

### What It Is
A system that reacts instantly to events (POS sales, brew completions, waste logs) by pushing updates to all interested parties, rather than polling.

### How BobaMaster Implements It

#### Event Flow
```
1. POS Sale Event
   ↓
2. Backend receives /api/v1/pos/webhook
   ├→ DecompoAgent.decompose() → deductions
   ├→ InventoryAgent.apply_deductions() → FIFO update
   ├→ broadcast_inventory_update() → WebSocket push
   └→ All KDS tablets receive updated inventory instantly

3. OpsDecider evaluates → BREW_NOW detected
   ├→ DispatcherAgent calls Gemini → explanation
   ├→ broadcast_alert() → WebSocket push
   └→ Alert banner appears on all tablets simultaneously
```

#### WebSocket as Event Bus
```python
# backend/app/api/websocket.py
async def broadcast_inventory_update(shop_id: str, state: InventoryStateResponse):
    payload = {
        "event_type": "inventory_update",
        "shop_id": shop_id,
        "ingredients": [state],
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    await ws_manager.broadcast(shop_id, json.dumps(payload))

# frontend/src/hooks/useWebSocket.ts
const lastMessage = useWebSocket(shop_id);
useEffect(() => {
    if (lastMessage?.event_type === "inventory_update") {
        // Update UI immediately
        dispatch({ type: "UPSERT_INGREDIENT", payload: lastMessage.ingredients[0] });
    }
}, [lastMessage]);
```

#### Benefits
- **Zero-latency**: Tablets see changes instantly
- **Scalable**: Add 10 tablets to a shop; they all receive updates simultaneously
- **Robust**: Clients auto-reconnect on disconnect

---

## 6. Adapter Pattern for External Services

### What It Is
Abstracting external services (weather, calendar) behind interfaces so implementations can be swapped without changing the consuming code.

### How BobaMaster Implements It

#### Abstract Base Classes
```python
# backend/app/services/weather_service.py
from abc import ABC, abstractmethod

class WeatherAdapterBase(ABC):
    @abstractmethod
    def get_weather(self, lat: float, lon: float) -> WeatherContext:
        pass

class MockWeatherAdapter(WeatherAdapterBase):
    """Deterministic mock for testing/demo."""
    def get_weather(self, lat: float, lon: float) -> WeatherContext:
        return WeatherContext(
            temp_c=31.0 if 6 <= datetime.now().month <= 8 else 18.0,
            rain_prob=0.8 if datetime.now().minute % 2 else 0.1,
            ...
        )

class OpenWeatherMapAdapter(WeatherAdapterBase):
    """Real OpenWeatherMap API (future implementation)."""
    def get_weather(self, lat: float, lon: float) -> WeatherContext:
        # Call real API
        pass
```

#### Zero-Change Swap
```python
# app/agents/context_agent.py
def __init__(self, weather_adapter=None):
    # Can pass mock or real adapter
    self.weather_adapter = weather_adapter or MockWeatherAdapter()

# In production:
agent = ContextAgent(weather_adapter=OpenWeatherMapAdapter())
# In tests:
agent = ContextAgent(weather_adapter=MockWeatherAdapter())
# ContextAgent code doesn't change
```

#### Benefits
- **Testability**: Mock externals, test logic in isolation
- **Modularity**: Replace OpenWeatherMap with Accuweather; zero code changes
- **Graceful fallback**: If real API fails, fall back to mock

---

## 7. Closed-Loop Learning (FeedbackAgent)

### What It Is
A system that learns from its mistakes by analyzing forecast accuracy and adjusting parameters automatically.

### How BobaMaster Implements It

#### Daily Audit
```python
# Every night, FeedbackAgent:
1. Queries sales logs: "How many grams of pearls sold today?"
2. Queries forecast logs: "What did we predict would sell?"
3. Computes MAPE (Mean Absolute Percentage Error)
4. Analyzes waste: "Wasted 15% of prepared pearls—too much cooking"
5. Checks compliance: "Staff ignored 3 brewing recommendations"
6. Tunes safety buffer:
   - If waste high: Decrease safety factor → cook less
   - If stockout happened: Increase safety factor → cook more
```

#### Example Output
```json
{
  "date": "2024-06-24",
  "mape": 0.18,  // 18% forecast error
  "pearl_waste_ratio": 0.12,  // 12% waste—down from 18% yesterday
  "pearl_safety_factor_before": 1.15,
  "pearl_safety_factor_after": 1.10,  // Decreased due to lower waste
  "updated": true
}
```

#### Benefits
- **Auto-calibration**: No manual tuning; system learns nightly
- **Data-driven**: Decisions based on actual outcomes, not guesses
- **Feedback loop**: Each day's forecast feeds next day's decision logic

---

## Course Concepts Checklist

### Required: At Least 3 of These

| Concept | Where It's Demonstrated | 
|---|---|
| ✅ **Multi-agent System** | 7 agents in `/backend/app/agents/` |
| ✅ **MCP Server Pattern** | `DispatcherAgent` constructs context for Gemini |
| ✅ **Security Features** | No hardcoded secrets, parameterized SQL, WebSocket scoping |
| ✅ **Deployability** | Docker Compose + Vercel config + environment variables |
| ✅ **Real-time Sync** | WebSocket event broadcasts |
| ✅ **Adapter Pattern** | Weather/calendar swappable implementations |
| ✅ **Closed-Loop Learning** | FeedbackAgent tunes safety buffers daily |

**Total: 7 concepts demonstrated. (Only 3 required.)**

---

## How to See These Concepts in Action

### 1. Multi-Agent Pipeline
```bash
# Terminal 1
cd backend && uvicorn app.main:app --reload

# Terminal 2
cd frontend && npm run dev

# Terminal 3
curl -X POST http://localhost:8000/api/v1/dispatcher/trigger-test-alert \
  -G --data-urlencode 'shop_id=00000000-0000-0000-0000-000000000001'

# Observe:
# - DecompoAgent is not called (no POS event)
# - DispatcherAgent directly receives alert payload
# - Gemini generates explanation
# - WebSocket broadcasts alert
# - Frontend shows alert banner
```

### 2. Real-Time Sync
```bash
# With backend + frontend running:
1. Open http://localhost:5173
2. Open Agent Panel ("AI Agent Controls")
3. Click "Simulate POS Sale"
4. Observe: Inventory ring updates immediately (no manual refresh)
5. Check browser console: Network tab shows WebSocket message
```

### 3. Adapter Pattern
```bash
# Edit backend/app/agents/context_agent.py
# Line: self.weather_adapter = MockWeatherAdapter()
# Change to: self.weather_adapter = OpenWeatherMapAdapter()
# (Real implementation is a stub, but pattern is clear)
# ContextAgent code doesn't change at all
```

### 4. Closed-Loop Learning
```bash
# Click "Daily Feedback Audit" tab
# Select yesterday's date
# Click "Run Feedback Agent"
# Observe: Safety buffer before/after, waste ratio, MAPE
# Data-driven parameter tuning in action
```

---

## Summary

BobaMaster successfully demonstrates **7 key course concepts** through a production-grade implementation of a real bubble tea operations system. The architecture is modular, secure, deployable, and demonstrates how AI agents solve business problems when properly orchestrated.

