# 🧋 BobaMaster — AI Operations Platform for Bubble Tea Shops

> **Antigravity Hackathon Submission** | Category: Agents for Business

BobaMaster is a real-time, multi-agent AI operations platform that solves a deceptively hard problem in the food & beverage industry: **when should a bubble tea shop start cooking the next batch of tapioca pearls?**

Get it wrong in one direction → pearls run out, customers leave angry.  
Get it wrong in the other → excess stock spoils, $$$  thrown in the bin.

BobaMaster replaces human guesswork with a closed-loop AI agent pipeline that perceives live sales data, forecasts demand, and tells kitchen staff *exactly* when to act — with a natural language explanation from Gemini 1.5 Flash explaining *why*.

---

## 🎥 Demo

> _[YouTube demo link — add before submission]_

---

## 📋 Table of Contents

1. [Problem Statement](#1-problem-statement)
2. [Solution Overview](#2-solution-overview)
3. [Multi-Agent Architecture](#3-multi-agent-architecture)
4. [Key Concepts Applied](#4-key-concepts-applied)
5. [Tech Stack](#5-tech-stack)
6. [Project Structure](#6-project-structure)
7. [Setup & Installation](#7-setup--installation)
8. [Running the Application](#8-running-the-application)
9. [Frontend Deployment (Vercel)](#9-frontend-deployment-vercel)
10. [API Reference](#10-api-reference)
11. [Security](#11-security)
12. [Testing](#12-testing)
13. [Roadmap](#13-roadmap)

---

## 1. Problem Statement

Bubble tea shops face a unique inventory challenge:

| Ingredient | Cook Time | Shelf Life (once cooked) |
|---|---|---|
| Tapioca Pearls | ~50 minutes | ~4 hours |
| Tea Base | ~15 minutes | ~6 hours |

Staff must decide *now* whether to start cooking — for demand that won't materialise for another hour. Manual prediction leads to:

- **Stockouts** during school rush / rainy days → angry customers, lost revenue
- **Over-preparation** near closing time → kilograms of pearls thrown away nightly

A single mid-sized bubble tea shop can waste $30–$80 of ingredients per day from this problem alone.

---

## 2. Solution Overview

BobaMaster operates as a **Sense → Plan → Act** AI agent loop running continuously alongside the POS system:

```
POS Sale ──► DecompoAgent ──► InventoryAgent ──► OpsDeciderAgent ──► DispatcherAgent ──► KDS Tablet
                                    ▲                    ▲
                              ContextAgent ──► PredictorAgent
                                    ▲
                          Weather / Calendar APIs
```

When a shortfall is predicted, the `DispatcherAgent` calls **Gemini 1.5 Flash** to generate a concise, staff-facing explanation and broadcasts it over WebSocket to the kitchen display tablet. Staff see *what* to do and *why* — in plain language.

---

## 3. Multi-Agent Architecture

The system is composed of **7 specialized agents**, each with a single responsibility:

### Agent Pipeline

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Agent Pipeline                               │
│                                                                     │
│  POS Event ──► [1] DecompoAgent                                     │
│                     │ ingredient deductions                         │
│                     ▼                                               │
│               [4] InventoryAgent  ◄──────────────────┐             │
│                     │ live stock state                │             │
│                     ▼                                 │             │
│               [5] OpsDeciderAgent                     │             │
│                     │ BREW_NOW / WARN / WAIT          │             │
│                     ▼                                 │             │
│               [6] DispatcherAgent ──► WebSocket ──► KDS Tablet      │
│                     │                                │             │
│                     ▼                                │             │
│  Clock ──► [2] ContextAgent ──► [3] PredictorAgent ──┘             │
│                                                                     │
│  Daily ──► [7] FeedbackAgent ──► parameter tuning                   │
└─────────────────────────────────────────────────────────────────────┘
```

| # | Agent | Role | Key Technology |
|---|---|---|---|
| 1 | **DecompoAgent** | Parse POS transactions → raw ingredient deductions using recipe BOM | Pydantic V2, FIFO scaling |
| 2 | **ContextAgent** | Gather weather, school calendar, local events → context vector | Redis cache (15-min TTL), mock adapters |
| 3 | **PredictorAgent** | Statistical demand forecast for t+30/60/120 min | Linear regression heuristic (LightGBM-ready) |
| 4 | **InventoryAgent** | FIFO batch lifecycle, expiry sweeper, recalibration | Redis sorted sets, pipelining |
| 5 | **OpsDeciderAgent** | Safety stock algorithm → BREW_NOW / WARN / WAIT | Deterministic arithmetic, 10-min cooldown dedup |
| 6 | **DispatcherAgent** | Gemini explanation + WebSocket broadcast | Gemini 1.5 Flash, FastAPI WebSocket, retry/fallback |
| 7 | **FeedbackAgent** | Daily MAPE analysis, waste audit, safety buffer tuning | psycopg2, PostgreSQL |

### Communication Pattern

Agents are **decoupled** — they do not call each other directly. They communicate through:
- **Redis** (short-term state: active batches, context cache, velocity windows)
- **PostgreSQL** (long-term log: recommendation history, feedback, sales)
- **WebSocket** (real-time push: kitchen display alerts)

---

## 4. Key Concepts Applied

### ✅ Multi-Agent System
Seven purpose-built agents form an event-driven pipeline. Each agent is independently testable, has a defined input/output contract, and can be replaced without affecting the others (e.g., swap `MockWeatherAdapter` for a real OpenWeatherMap adapter with zero changes to `ContextAgent`).

### ✅ MCP Server Pattern
The `DispatcherAgent` implements the **Model Context Protocol** pattern: it constructs a rich structured context (inventory levels, forecast vectors, weather, school session status) and passes it to Gemini 1.5 Flash as a single coherent prompt. The LLM receives exactly what it needs and nothing more.

### ✅ Security Features
- No API keys in source code — all secrets loaded from environment variables
- `.env` files blocked from git via `.gitignore`
- Pydantic V2 strict validation on all API inputs (prevents injection via malformed payloads)
- SQL parameterized queries via psycopg2 (no raw string interpolation)
- WebSocket connections are shop-scoped (no cross-shop data leakage)

### ✅ Deployability
- Frontend: Vercel (zero-config via `vercel.json`)
- Backend: Docker Compose (PostgreSQL + Redis) + `uvicorn`
- Environment variables documented in `.env.example`

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
