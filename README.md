# 🧋 BobaMaster — AI Operations Platform for Bubble Tea Shops

> **Antigravity Hackathon Submission** | Category: Agents for Business

BobaMaster is a real-time, multi-agent AI operations platform that solves a deceptively hard problem in the food & beverage industry: **when should a bubble tea shop start cooking the next batch of tapioca pearls?**

Get it wrong in one direction → pearls run out, customers leave angry.  
Get it wrong in the other → excess stock spoils, $$$  thrown in the bin.

A single mid-sized bubble tea shop wastes **$30–$80 of ingredients per day** from manual inventory mismanagement alone.

## 🎯 The Problem

Bubble tea shops face a unique inventory challenge:

| Challenge | Impact |
|---|---|
| Tapioca pearls take ~50 min to cook but stay fresh ~4 hours | Staff must decide now for demand 1 hour away |
| Tea base takes ~15 min but stays fresh ~6 hours | Wrong prediction = stockouts OR waste |
| Peak demand times are predictable but volatile | Rain, school rush, local events create spikes |
| Staff rely on hunches, not data | Margins are tight; waste cascades |

**Real scenario:** It's 3 PM, a bubble tea shop has 400g of pearls left. School ends at 3:30 PM. Cook now or wait? If you're wrong, you either run out during the rush or throw away a fresh batch at 7 PM closing.

## ✨ The Solution

BobaMaster replaces human guesswork with a **closed-loop AI agent pipeline** that:

1. **Perceives:** Reads real-time POS sales, weather, school calendar
2. **Forecasts:** Uses demand patterns to predict consumption for t+30/60/120 min  
3. **Decides:** Applies safety stock algorithms to determine: BREW_NOW / WARN / WAIT
4. **Explains:** Calls Gemini 1.5 Flash to generate a 1-2 sentence staff explanation (*"School rush starting in 15 mins. Pearls projected to hit zero at 3:47 PM. Start cook now."*)
5. **Broadcasts:** Sends the alert to the kitchen display tablet in real-time via WebSocket
6. **Learns:** Each night, analyzes forecast accuracy, waste, and auto-tunes safety buffers for tomorrow

## 🏗️ Architecture: 7-Agent Pipeline

```
POS Sale ──► DecompoAgent ──► InventoryAgent ──► OpsDeciderAgent ──► DispatcherAgent ──► KDS Tablet
                                    ▲                    ▲
                              ContextAgent ──► PredictorAgent
                                    ▲
                          Weather / Calendar APIs

Daily ──► FeedbackAgent ──► System Tuning
```

| Agent | Role | Key Tech |
|---|---|---|
| **DecompoAgent** | Parse POS transaction → recipe deductions | Pydantic V2, FIFO scaling |
| **ContextAgent** | Weather, school calendar, local events | Redis cache, mock adapters |
| **PredictorAgent** | Demand forecast for t+30/60/120 min | Linear regression + context multipliers |
| **InventoryAgent** | FIFO batch lifecycle, expiry sweep | Redis sorted sets, pipelining |
| **OpsDeciderAgent** | Safety stock → BREW_NOW / WARN / WAIT | Deterministic math, 10-min dedup |
| **DispatcherAgent** | Gemini explanation + WebSocket broadcast | Gemini 1.5 Flash, retry/fallback |
| **FeedbackAgent** | Daily MAPE audit, safety buffer tuning | PostgreSQL, synthetic data fallback |

## 🔑 Key Concepts Applied

### ✅ Multi-Agent System (ADK)
Seven purpose-built agents form an event-driven pipeline. Each is independently testable, has a defined input/output contract, and can be replaced or enhanced without affecting others.

### ✅ Model Context Protocol (MCP) Pattern
The `DispatcherAgent` implements the **MCP pattern**: it constructs a rich structured context (inventory levels, forecast vectors, weather, school status) and passes it to Gemini 1.5 Flash as a coherent prompt. The LLM receives *exactly* what it needs.

### ✅ Security Features
- No API keys in source code — secrets via environment variables only
- Pydantic V2 strict validation on all inputs (prevents injection)
- SQL parameterized queries via psycopg2 (no string interpolation)
- WebSocket connections scoped per shop (no data leakage)

### ✅ Deployability
- Frontend: Vercel (zero-config, auto-deploy from GitHub)
- Backend: Docker Compose (PostgreSQL + Redis) + Uvicorn
- Graceful degradation: Works with PostgreSQL down (synthetic data mode)

---

## 5. Tech Stack

| Layer | Technology | Why |
|---|---|---|
| **Backend** | FastAPI (Python) | Async, WebSocket support, Pydantic native |
| **AI / LLM** | Google Gemini 1.5 Flash | Low-latency, structured JSON output, cost-effective |
| **Time-Series DB** | PostgreSQL + TimescaleDB | Hypertables for POS velocity data |
| **State Cache** | Redis | Sub-ms FIFO batch reads, pub/sub for inventory events |
| **Frontend** | React 19 + Vite + TypeScript | Fast HMR, component isolation |
| **Styling** | Tailwind CSS v3 | Utility-first, M3 design tokens |
| **Testing** | pytest (backend), TypeScript strict mode (frontend) |

---

## 6. Project Structure

```
BobaMaster/
├── backend/
│   └── app/
│       ├── agents/
│       │   ├── context_agent.py       # ContextAgent — weather + calendar
│       │   ├── decompo_agent.py       # DecompoAgent — POS → ingredients
│       │   ├── dispatcher_agent.py    # DispatcherAgent — Gemini + WebSocket
│       │   ├── inventory_agent.py     # InventoryAgent — FIFO batch ledger
│       │   ├── ops_decider_agent.py   # OpsDeciderAgent — safety stock decisions
│       │   └── predictor_agent.py     # PredictorAgent — demand forecast
│       ├── api/
│       │   ├── context.py             # GET /api/v1/context/{shop_id}
│       │   ├── forecast.py            # GET /api/v1/forecast/{shop_id}/{ingredient}
│       │   ├── inventory.py           # CRUD /api/v1/inventory/...
│       │   ├── operations.py          # GET /api/v1/operations/decisions/{shop_id}
│       │   ├── pos.py                 # POST /api/v1/pos/webhook
│       │   └── websocket.py           # WS /ws/shop/{shop_id}
│       ├── config/
│       │   └── recipes.json           # Recipe BOM (30 drinks, size + ice multipliers)
│       ├── database/
│       │   ├── init_db.py             # DB migration runner (retry logic)
│       │   └── schema.sql             # TimescaleDB hypertables
│       ├── models/                    # Pydantic V2 schemas
│       └── services/
│           ├── calendar_service.py    # School calendar adapter (mock + real stub)
│           ├── inventory_service.py   # Redis persistence adapter
│           ├── recommendation_service.py  # PostgreSQL recommendation logger
│           └── weather_service.py     # Weather adapter (mock + OWM stub)
├── docker/
│   └── docker-compose.yml
├── frontend/
│   ├── public/
│   │   └── favicon.svg
│   ├── src/
│   │   ├── components/
│   │   │   ├── ActiveTimers.tsx       # Brew countdown timers
│   │   │   ├── AlertBanner.tsx        # Critical operations banner
│   │   │   ├── CircularProgress.tsx   # SVG ring for ingredient levels
│   │   │   ├── Dashboard.tsx          # Main dashboard layout
│   │   │   ├── NavigationRail.tsx     # Left navigation rail
│   │   │   └── TopBar.tsx             # Top app bar + WS status
│   │   ├── hooks/
│   │   │   └── useWebSocket.ts        # Auto-reconnect WS hook
│   │   ├── store/
│   │   │   └── dashboardStore.ts      # useReducer global state
│   │   ├── types/
│   │   │   └── index.ts               # Shared TypeScript types
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── .env.example                   # Environment variable template
│   ├── index.html
│   ├── package.json
│   ├── tailwind.config.js
│   └── vite.config.ts
├── tests/
│   ├── test_context.py                # 8 tests
│   ├── test_decompo.py                # 7 tests
│   ├── test_dispatcher.py             # 14 tests
│   ├── test_inventory.py              # 6 tests
│   ├── test_ops_decider.py            # 10 tests
│   └── test_predictor.py             # 13 tests
├── artifacts/                         # Design documents
├── .gitignore
├── package.json                       # Root build script (for Vercel)
├── vercel.json                        # Vercel deployment config
└── README.md
```

---

## 7. Setup & Installation

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- A Gemini API key ([get one here](https://ai.google.dev/gemini-api/docs/api-key))

### Backend Setup

```bash
# 1. Clone the repo
git clone <your-repo-url>
cd BobaMaster

# 2. Start infrastructure (PostgreSQL + Redis)
cd docker
docker-compose up -d
cd ..

# 3. Install Python dependencies
cd backend
pip install -r requirements.txt

# 4. Set environment variables (never commit real values)
cp .env.example .env
# Edit .env and fill in GEMINI_API_KEY, POSTGRES_*, REDIS_URL

# 5. Run database migration
python app/database/init_db.py

# 6. Start the backend server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend Setup

```bash
cd frontend
cp .env.example .env
# Edit .env — set VITE_WS_URL and VITE_API_URL to point at your backend

npm install
npm run dev
# Open http://localhost:5173
```

---

## 8. Running the Application

### Full Stack (all services)

```bash
# Terminal 1 — Infrastructure
cd docker && docker-compose up

# Terminal 2 — Backend API
cd backend && uvicorn app.main:app --reload --port 8000

# Terminal 3 — Frontend
cd frontend && npm run dev
```

### Backend only (no Docker, tests)

```bash
cd BobaMaster
python -m pytest tests/ -v
# Expected: 58 passed, 0 warnings
```

### Triggering a test alert (no POS system needed)

```bash
# Start the backend, then:
curl -X POST "http://localhost:8000/api/v1/dispatcher/trigger-test-alert?shop_id=00000000-0000-0000-0000-000000000001"
```

This fires a BREW_NOW scenario for tapioca pearls through the full Gemini → WebSocket pipeline.


## License


*Built with ❤️ and too much bubble tea.*
