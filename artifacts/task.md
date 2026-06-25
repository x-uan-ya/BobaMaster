# Task List: BobaMaster Platform

## Milestone 1: Setup & Initialization
- [x] Create project directory layout (`BobaMaster/`)
- [x] Create `docker-compose.yml` for PostgreSQL/TimescaleDB and Redis
- [x] Create `requirements.txt` listing Python backend dependencies
- [x] Create `schema.sql` defining database schemas & hypertables
- [x] Create `init_db.py` database migration script
- [x] Add syntax verification for initialization scripts
- [x] Write `README.md` instructions

## Milestone 2: POS Ingestion & Recipe Decomposition
- [x] Create `recipes.json` with 30 drinks, size multipliers, ice-level multipliers, and liquid registry
- [x] Create Pydantic V2 models (`models/pos.py`) with strict `size` and `ice_level` literals
- [x] Implement `DecompoAgent` with deterministic FIFO scaling pipeline
- [x] Create FastAPI POS webhook router (`api/pos.py`)
- [x] Create FastAPI app entrypoint (`app/main.py`)
- [x] Write pytest suite (`tests/test_decompo.py`) — 7 tests passing, 0 warnings

## Milestone 3: Inventory State Ledger & FIFO Batches
- [x] Create Pydantic V2 models (`models/inventory.py`) — brew, recalibrate, waste, state schemas
- [x] Create `InventoryService` Redis persistence adapter (`services/inventory_service.py`)
- [x] Implement `InventoryAgent` with FIFO deduction, brew lifecycle, recalibration, waste logging, and expiry sweeper (`agents/inventory_agent.py`)
- [x] Create FastAPI inventory router (`api/inventory.py`) — 5 endpoints
- [x] Attach inventory router to `app/main.py`
- [x] Write pytest suite (`tests/test_inventory.py`) with in-memory Redis mock — 6 tests passing, 0 warnings
- [x] Full combined suite — 13/13 passing

## Milestone 4: Context Enrichment Service
- [x] Create Pydantic V2 models (`models/context.py`) — WeatherContext, CalendarContext, LocalEventsContext, ContextVector
- [x] Create `MockWeatherAdapter` and `OpenWeatherMapAdapter` stub (`services/weather_service.py`)
- [x] Create `MockCalendarAdapter`, `MockLocalEventsAdapter` and real adapter stubs (`services/calendar_service.py`)
- [x] Implement `ContextAgent` with Redis caching (15 min TTL) and fallback handling (`agents/context_agent.py`)
- [x] Create FastAPI context router (`api/context.py`) — GET + cache-invalidate endpoints
- [x] Attach context router to `app/main.py`
- [x] Write pytest suite (`tests/test_context.py`) — 8 tests passing, 0 warnings
- [x] Full combined suite — 21/21 passing

## Milestone 5: Numerical Demand Forecasting Engine
- [x] Create Pydantic V2 models (`models/predictor.py`) — VelocityWindow, ForecastVector, ForecastRequest
- [x] Implement `PredictorAgent` with weighted-average base rate and context multipliers (`agents/predictor_agent.py`)
  - School session multiplier ×1.35
  - Hot weather multiplier ×1.25 (cold drink ingredients, temp_c > 28°C)
  - Rain multiplier ×1.20 (hot drink ingredients, rain_prob > 0.6)
  - Modular `_base_forecast()` method for future LightGBM swap-in
- [x] Create FastAPI forecast router (`api/forecast.py`) — GET by path + POST compute endpoint
- [x] Attach forecast router to `app/main.py`
- [x] Write pytest suite (`tests/test_predictor.py`) — 13 tests passing, 0 warnings
## Milestone 6: Operational Decision Model
- [x] Create Pydantic V2 models (`models/ops_decider.py`) — DecisionAction enum, IngredientConfig, OpsDecision, ActiveAlertsResponse, RecommendationLog
- [x] Implement `OpsDeciderAgent` with safety stock algorithm, forecast horizon selection, BREW_NOW/WARN/WAIT classification, cooldown deduplication, and PostgreSQL write delegation (`agents/ops_decider_agent.py`)
- [x] Create `RecommendationService` PostgreSQL persistence adapter (`services/recommendation_service.py`)
- [x] Create FastAPI operations router (`api/operations.py`) — GET decisions + POST trigger-test-alert endpoints
- [x] Attach operations router to `app/main.py`
- [x] Write pytest suite (`tests/test_ops_decider.py`) — 10 tests passing, 0 warnings
- [x] Full combined suite — 44/44 passing

## Milestone 7: Gemini Explanation & WebSocket Dispatch
- [x] Create Pydantic V2 models (`models/dispatcher.py`) — LLMExplanation, AlertPayload, DispatchMessage
- [x] Implement `DispatcherAgent` with Gemini 1.5 Flash integration, retry logic (3 attempts + exp. back-off), deterministic fallback, and injected broadcaster protocol (`agents/dispatcher_agent.py`)
- [x] Create `WebSocketManager` with per-shop connection grouping, broadcast, and dead-socket cleanup (`api/websocket.py`)
- [x] Create dispatcher REST router — POST /broadcast, POST /trigger-test-alert, GET /connections
- [x] Create WebSocket endpoint — `WS /ws/shop/{shop_id}`
- [x] Attach dispatcher and WebSocket routers to `app/main.py`
- [x] Write pytest suite (`tests/test_dispatcher.py`) — 14 tests passing, 0 warnings
- [x] Full combined suite — 58/58 passing

## Milestone 8: KDS Frontend Shell & Dashboard Visualization
- [x] Initialize a Vite React frontend with Tailwind CSS and app shell
- [x] Build the dashboard layout with alert banner, ingredient cards, and active timers
- [x] Wire WebSocket listener into global state for real-time updates
- [x] Add backend inventory snapshot endpoint and bootstrap frontend state
- [x] Verify frontend build successfully

## Milestone 9: KDS Alarm Interactions & Cooking Logs
- [x] Add alert acknowledgement workflows (`Start Cooking`, `Snooze`) with backend API actions
- [x] Add active brewing timer completion flow with `brew/complete`
- [x] Add sound chime and interaction polishing

## Milestone 10: Closed-Loop Daily Feedback & Retraining
- [x] Add `FeedbackAgent` feedback audit agent with system tuning
- [x] Add PostgreSQL schema tables for `system_settings`, `sales_forecasts`, and `sales_actuals`
- [x] Create FastAPI feedback router and wire it into `app/main.py`
- [x] Add feedback endpoint tests and documentation
- [x] Frontend FeedbackPage wired to feedback API endpoint
- [x] Fixed inventory refresh on waste/cook operations
- [x] Fixed POS webhook to apply deductions and broadcast real-time inventory updates via WebSocket

