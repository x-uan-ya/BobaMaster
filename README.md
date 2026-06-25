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

---

## 9. Frontend Deployment (Vercel)

### One-click deploy

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/YOUR_USERNAME/BobaMaster)

### Manual Vercel deployment

1. Push the repo to GitHub
2. Import the repo on [vercel.com](https://vercel.com)
3. Vercel auto-detects the config from `vercel.json`
4. Set these **Environment Variables** in the Vercel dashboard:

| Variable | Description | Example |
|---|---|---|
| `VITE_WS_URL` | WebSocket URL of your deployed backend | `wss://your-backend.fly.dev` |
| `VITE_API_URL` | REST API URL of your deployed backend | `https://your-backend.fly.dev` |
| `VITE_SHOP_ID` | Shop UUID for this terminal | `00000000-0000-0000-0000-000000000001` |
| `VITE_STORE_NAME` | Display name | `Downtown Store` |

5. Click **Deploy**

> **Note:** The frontend is a static SPA. It connects to your backend over WebSocket. If you only want to demo the UI without a live backend, it renders gracefully in "Offline" mode with placeholder inventory data.

### Build settings (auto-detected from vercel.json)

| Setting | Value |
|---|---|
| Build Command | `npm run build` |
| Output Directory | `frontend/dist` |
| Install Command | `npm install` |
| Framework | Vite |

---

## 10. API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `POST` | `/api/v1/pos/webhook` | Ingest a POS transaction |
| `POST` | `/api/v1/inventory/brew/start` | Log brew start |
| `POST` | `/api/v1/inventory/brew/complete` | Log brew completion |
| `POST` | `/api/v1/inventory/recalibrate` | Manual stock audit override |
| `POST` | `/api/v1/inventory/waste` | Log ingredient waste |
| `GET` | `/api/v1/inventory/state/{shop_id}/{ingredient_id}` | Current inventory state |
| `GET` | `/api/v1/context/{shop_id}` | Current context vector (weather, calendar) |
| `GET` | `/api/v1/forecast/{shop_id}/{ingredient_id}` | Demand forecast (t30/t60/t120) |
| `GET` | `/api/v1/operations/decisions/{shop_id}` | Active BREW_NOW / WARN alerts |
| `POST` | `/api/v1/dispatcher/broadcast` | Push alert through Gemini → WebSocket |
| `POST` | `/api/v1/dispatcher/trigger-test-alert` | Fire a test BREW_NOW (no POS needed) |
| `GET` | `/api/v1/dispatcher/connections` | Active WebSocket connection count |
| `WS` | `/ws/shop/{shop_id}` | Real-time KDS tablet channel |

Full interactive docs available at `http://localhost:8000/docs` when the backend is running.

---

## 11. Security

- **No secrets in code** — all credentials (Gemini API key, DB password, Redis URL) are loaded from environment variables
- **`.env` files are gitignored** — only `.env.example` with placeholder values is committed
- **Input validation** — Pydantic V2 strict mode validates every API request; unknown fields are rejected
- **Parameterized SQL** — psycopg2 parameterized queries prevent SQL injection in all DB writes
- **WebSocket scoping** — connections are isolated per `shop_id`; a tablet for shop A cannot receive messages for shop B
- **LLM output validation** — Gemini responses are parsed through Pydantic before being broadcast; malformed LLM output triggers the deterministic fallback

---

## 12. Testing

```bash
cd BobaMaster
python -m pytest tests/ -v
```

| Test File | Tests | Coverage |
|---|---|---|
| `test_decompo.py` | 7 | Recipe parsing, size/ice modifiers, unrecognized items |
| `test_inventory.py` | 6 | FIFO deduction, expiry sweep, recalibration, waste |
| `test_context.py` | 8 | Weather mock, school calendar, cache hit/miss, invalidation |
| `test_predictor.py` | 13 | All multiplier combinations, horizon scaling, zero velocity |
| `test_ops_decider.py` | 10 | BREW_NOW/WARN/WAIT classification, cooldown dedup, DB write |
| `test_dispatcher.py` | 14 | Gemini mock, fallback on failure, WS broadcast, JSON parsing |
| **Total** | **58** | **0 warnings** |

---

## 13. Roadmap

| Phase | Feature |
|---|---|
| ✅ M1 | Project setup, Docker, TimescaleDB schema |
| ✅ M2 | POS ingestion, recipe decomposition (DecompoAgent) |
| ✅ M3 | FIFO inventory ledger (InventoryAgent) |
| ✅ M4 | Context enrichment — weather + calendar (ContextAgent) |
| ✅ M5 | Demand forecasting engine (PredictorAgent) |
| ✅ M6 | Safety stock decisions (OpsDeciderAgent) |
| ✅ M7 | Gemini explanations + WebSocket broadcast (DispatcherAgent) |
| ✅ M8 | React KDS dashboard — live ingredient rings + alert banner |
| 🔲 M9 | Alert interactions — audio chimes, snooze, cook timers |
| 🔲 M10 | Feedback agent — daily MAPE audit, safety buffer tuning |

---

## License

MIT — see `LICENSE` for details.

---

*Built with ❤️ and too much bubble tea.*
