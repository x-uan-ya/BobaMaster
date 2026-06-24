# AI Coding Prompts: Bobaflow Milestones

This document compiles 10 distinct, self-contained AI coding prompts corresponding to each milestone of the Bobaflow development roadmap. These prompts are structured specifically for execution by AI coding assistants, emphasizing architectural rigor, clean code practices, and zero-placeholder implementations.

---

## Prompt 1: Project Setup & Database Schema Initialization (Milestone 1)

```yaml
Context:
  Project: Bobaflow Bubble Tea Operations Platform
  Milestone: 1 (Project Setup & Database Schema Initialization)
  Architecture: FastAPI (Backend), PostgreSQL/TimescaleDB (Relational/Time-Series), Redis (State Cache)

Goal: Set up the repository layout, Docker services, database schemas, and migration runner.

Directory Layout:
  .
  ├── docker-compose.yml
  ├── backend/
  │   ├── requirements.txt
  │   └── database/
  │       ├── schema.sql
  │       └── init_db.py

Requirements:
  1. Docker Compose:
     - Spin up PostgreSQL (image: timescale/timescaledb:latest-pg15) mapping host port 5432 to container port 5432. Use environment variables: POSTGRES_USER=postgres, POSTGRES_PASSWORD=postgres, POSTGRES_DB=bobaflow.
     - Spin up Redis (image: redis:7-alpine) mapping host port 6379 to container port 6379.
     - Ensure data persistence using volume mounts.
  2. Database Schema (schema.sql):
     - Enable TimescaleDB extension: `CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;`.
     - Table `inventory_states`: tracks ingredient quantities. Columns: timestamp (TIMESTAMPTZ, primary key partition), shop_id (UUID), ingredient_id (VARCHAR), estimated_qty_grams (NUMERIC), active_brewing_qty_grams (NUMERIC), nearest_expiry (TIMESTAMPTZ). Convert this to a TimescaleDB hypertable chunked by `timestamp` daily.
     - Table `brew_logs`: tracks cooking events. Columns: id (UUID primary key), shop_id (UUID), ingredient_id (VARCHAR), started_at (TIMESTAMPTZ), completed_at (TIMESTAMPTZ, nullable), expires_at (TIMESTAMPTZ, nullable), initial_qty_grams (NUMERIC), wasted_qty_grams (NUMERIC).
     - Table `recommendation_logs`: Columns: id (UUID primary key), shop_id (UUID), created_at (TIMESTAMPTZ), ingredient_id (VARCHAR), action_recommended (VARCHAR), predicted_shortage_at (TIMESTAMPTZ), explanation_text (TEXT), model_features_snapshot (JSONB).
     - Table `recommendation_feedback`: Columns: recommendation_id (UUID primary key, foreign key to recommendation_logs), responded_at (TIMESTAMPTZ), action_taken (VARCHAR), delay_minutes (INTEGER), staff_notes (TEXT).
  3. Migration Script (init_db.py):
     - Write a Python script using `psycopg2-binary` to connect to PostgreSQL, read `schema.sql`, and execute it to set up the tables. Use standard environment variables for connection credentials.
  4. Backend Requirements (backend/requirements.txt):
     - Include `fastapi`, `uvicorn`, `psycopg2-binary`, `redis`, `pydantic`.

Instructions:
  - Write production-quality code. Do not use placeholders or omit setup lines.
  - Implement robust connection retry logic (up to 5 attempts) in `init_db.py` to allow PostgreSQL to boot up during docker-compose.
  - Ensure all database tables use explicit column naming, primary keys, and foreign keys where applicable.

How to verify:
  - Verify that `docker-compose up` launches Postgres and Redis.
  - Verify that running `python backend/database/init_db.py` runs successfully.
```

---

## Prompt 2: POS Event Ingestion & Recipe Decomposition (Milestone 2)

```yaml
Context:
  Project: Bobaflow
  Milestone: 2 (POS Event Ingestion & Recipe Decomposition)
  Target Agent: DecompoAgent

Goal: Build a REST endpoint to accept POS sale webhooks and resolve transactions into ingredient deductions.

Directory Layout:
  backend/
  ├── main.py
  ├── config/
  │   └── recipes.json
  ├── agents/
  │   └── decompo.py
  └── tests/
      └── test_decompo.py

Requirements:
  1. Recipe JSON Config (recipes.json):
     - Define recipe mappings for: "Classic Milk Tea (M)" (tapioca_pearls: 40g, black_tea: 200ml, fructose: 25g), "Classic Milk Tea (L)" (tapioca_pearls: 60g, black_tea: 300ml, fructose: 35g), "Matcha Latte (M)" (matcha_powder: 10g, milk: 200ml, fructose: 20g).
  2. DecompoAgent (decompo.py):
     - Implement a class `DecompoAgent` that parses POS transaction inputs.
     - Input Schema: transaction_id (string), shop_id (UUID), items (list of objects: item_name, quantity, modifiers [list of strings, e.g., 'extra pearls']).
     - If modifiers contain 'extra pearls', multiply tapioca_pearls deduction by 1.5x. If 'no pearls', set tapioca_pearls deduction to 0.
     - Return list of ingredient deductions: ingredient_id, qty_grams_ml.
  3. FastAPI Endpoints (main.py):
     - Add route `POST /api/v1/pos/webhook` parsing the POS transaction payload.
     - Call `DecompoAgent` to get deductions.
     - Log the deduction payload to stdout using standard logging.
  4. Unit Tests (test_decompo.py):
     - Write pytest cases targeting Classic Milk Tea (M) and (L) sales, validating modifiers logic.

Instructions:
  - Do not use placeholders. Write the full parsing and matching algorithms.
  - Ensure typing is strict (Pydantic classes for incoming payload validation).

How to verify:
  - Run pytest `pytest backend/tests/test_decompo.py`.
  - POST a mock JSON payload to `/api/v1/pos/webhook` using curl and inspect the return value.
```

---

## Prompt 3: Inventory State Ledger & FIFO Batches (Milestone 3)

```yaml
Context:
  Project: Bobaflow
  Milestone: 3 (Inventory State Ledger & FIFO Batches)
  Target Agent: InventoryAgent

Goal: Track prepared inventory volumes by maintaining a FIFO stack of cooked batches and handling sales deductions.

Directory Layout:
  backend/
  ├── agents/
  │   └── inventory.py
  └── tests/
      └── test_inventory.py

Requirements:
  1. State Modeling:
     - Define a `PreparedBatch` schema: batch_id (UUID), ingredient_id (string), initial_qty (float), remaining_qty (float), expires_at (datetime).
  2. FIFO Deduction Logic:
     - Implement a class `InventoryAgent` that connects to Redis.
     - When a sales deduction arrives (from `DecompoAgent` output):
       - Retrieve the current list of active batches for that ingredient sorted by expiration (FIFO).
       - Subtract the sale amount from the oldest batch. If the amount exceeds the remaining batch quantity, exhaust it, mark it as completed, and subtract the remainder from the next oldest batch.
       - Discard any batches whose `expires_at` is older than the current time.
  3. API Endpoints:
     - `POST /api/v1/inventory/recalibrate`: Accept manual scale adjustment from staff. Payload: `{ "ingredient_id": "tapioca_pearls", "actual_qty_grams": 1200.0 }`. This overrides the sum of remaining quantities across active batches.
     - `POST /api/v1/inventory/waste`: Log early discard.
  4. Unit Tests:
     - Test FIFO depletion: add a batch of 1000g expiring in 1 hour, and another of 1000g expiring in 3 hours. Deduct 1200g. Assert the first batch is fully depleted and the second has 800g remaining.

Instructions:
  - Use Redis transactions or locks (pipelining) to ensure concurrency safety.
  - Avoid any fake mock databases in memory; write concrete Redis client calls.

How to verify:
  - Run `pytest backend/tests/test_inventory.py` with Redis running.
```

---

## Prompt 4: Context Enrichment Service (Milestone 4)

```yaml
Context:
  Project: Bobaflow
  Milestone: 4 (Context Enrichment Service)
  Target Agent: ContextAgent

Goal: Compile current location coordinates and time into a normalized context vector for forecasting.

Directory Layout:
  backend/
  ├── agents/
  │   └── context.py
  └── tests/
      └── test_context.py

Requirements:
  1. ContextAgent Implementation:
     - Create a class `ContextAgent`.
     - Method `fetch_context(shop_id: UUID, lat: float, lon: float) -> ContextVector`.
     - Structure a mock adapter for the weather API (returning temperature, precipitation probability, humidity) and the school calendar (boolean check if a date falls in school term dates).
     - Standardize output context dictionary: `{ "temp_c": float, "rain_prob": float, "school_in_session": bool, "holiday_flag": bool }`.
  2. Mock Data Configuration:
     - Set up seasonal logic: if month is June/July/August, school_in_session is False.
     - Implement weather mocking: if latitude coordinate ends in an odd digit, return "rainy" (rain_prob: 0.8), else "clear" (rain_prob: 0.1).
  3. Endpoint Integration:
     - Add endpoint `GET /api/v1/context/{shop_id}` returning current context metrics.

Instructions:
  - Write robust exception handling. If a mock calendar or weather retrieval fails, return a default context vector with clear fallbacks (e.g. 20C, clear, school in session).
  - Use Pydantic to strictly serialize context vector payloads.

How to verify:
  - Execute `pytest backend/tests/test_context.py`.
```

---

## Prompt 5: Numerical Demand Forecasting Engine (Milestone 5)

```yaml
Context:
  Project: Bobaflow
  Milestone: 5 (Numerical Demand Forecasting Engine)
  Target Agent: PredictorAgent

Goal: Generate numeric demand forecasts for 30m, 60m, and 120m horizons.

Directory Layout:
  backend/
  ├── agents/
  │   └── predictor.py
  └── tests/
      └── test_predictor.py

Requirements:
  1. PredictorAgent Class:
     - Create `PredictorAgent`.
     - Inputs: recent sales velocity (average cups sold/min in last 10m, 30m, 60m), context vector (weather, school status).
     - Calculate projected demand vectors using a linear regression heuristic adjusted by context:
       - Base Forecast = average of (10m velocity, 30m velocity, 60m velocity).
       - If school_in_session is true, multiply projection by 1.35x.
       - If temp_c is > 28C, multiply cold drink base forecast by 1.25x.
       - If rain_prob is > 0.6, multiply hot drink base forecast by 1.20x.
     - Output: `{ "t30": float, "t60": float, "t120": float }` in units of expected ingredient portions (grams/ml).
  2. Velocity Logs:
     - Read transaction records from TimescaleDB for the preceding 1 hour to compute input velocity parameters dynamically.
  3. API Endpoint:
     - `GET /api/v1/forecast/{shop_id}/{ingredient_id}`: Outputs the predicted demand vectors for the target ingredient.

Instructions:
  - Use type hints for all data models.
  - Implement mathematical scaling logic cleanly without external heavy ML libraries for now (keep the predictor class modular so a LightGBM model file can be dropped in later).

How to verify:
  - Run the test script and verify that mock changes to the context vector correctly adjust demand forecast outputs.
```

---

## Prompt 6: Operational Decision Model (Milestone 6)

```yaml
Context:
  Project: Bobaflow
  Milestone: 6 (Operational Decision Model)
  Target Agent: OpsDeciderAgent

Goal: Run safety stock calculations to generate discrete operational cook decisions.

Directory Layout:
  backend/
  ├── agents/
  │   └── ops_decider.py
  └── tests/
      └── test_ops_decider.py

Requirements:
  1. Safety Buffer Algorithms:
     - Define parameters per ingredient: Cook Time (tapioca_pearls: 50m, black_tea: 15m), Batch size (pearls: 2000g, tea: 4000ml).
     - Implement `OpsDeciderAgent`.
     - Calculation:
       - Predicted Consumption = Forecasted demand during the cook window (e.g. next 50m).
       - Target Runway = Current stock + items currently brewing - Predicted Consumption.
       - If Target Runway < Safety Buffer (e.g., 200g for pearls), trigger a `BREW_NOW` action.
       - If runway is secure, return `WAIT`.
  2. State Evaluation Scheduler:
     - Write a service routine (run every 60s or debounced on transactions) that pulls the latest values from `InventoryAgent` and `PredictorAgent` to run safety stock algorithms.
     - If decision is `BREW_NOW`, write recommendation log details to the SQL table `recommendation_logs`.
  3. Endpoint:
     - `GET /api/v1/operations/decisions/{shop_id}`: Returns active alerts list.

Instructions:
  - Store recommendation outcomes in PostgreSQL. Do not log duplicate alerts for the same shortage window (implement a cool-down period of 10 minutes).

How to verify:
  - Run pytest simulating low stock conditions; verify database contains a logged `BREW_NOW` event.
```

---

## Prompt 7: Gemini Explanation & WebSocket Dispatch (Milestone 7)

```yaml
Context:
  Project: Bobaflow
  Milestone: 7 (Gemini Explanation & WebSocket Dispatch)
  Target Agent: DispatcherAgent

Goal: Connect Gemini 1.5 Flash to generate natural language explanations and broadcast alerts over WebSockets.

Directory Layout:
  backend/
  ├── agents/
  │   └── dispatcher.py
  └── tests/
      └── test_dispatcher.py

Requirements:
  1. LLM Integration:
     - Initialize the Google GenAI SDK (use Gemini 1.5 Flash). Read the API key from environment variable GEMINI_API_KEY.
     - Prompt Template: Pass current inventory level, active brewing statuses, time of day, weather, and forecast numbers. Ask Gemini to write a concise (max 3 sentences), highly actionable operational justification.
     - Request structured JSON output using Pydantic schemas containing `action_string` and `explanation_text`.
  2. WebSocket Broadcast Engine:
     - Implement a WebSocket connection manager in FastAPI (`/ws/shop/{shop_id}`).
     - When `OpsDeciderAgent` logs a `BREW_NOW` event, call the LLM generator, format the output, and broadcast it to all connected sockets.
  3. API Endpoint:
     - `POST /api/v1/operations/trigger-test-alert`: Manually triggers a mock alert path to test the WebSocket pipe.

Instructions:
  - Do not write mock text templates for the AI output; call the real Gemini API.
  - Implement retry limits and fallback messages in case the LLM API is rate-limited or returns an error.

How to verify:
  - Run the WebSocket server, connect using a test client, trigger the endpoint, and verify you receive a valid message with LLM text.
```

---

## Prompt 8: KDS Frontend Shell & Dashboard Visualization (Milestone 8)

```yaml
Context:
  Project: Bobaflow
  Milestone: 8 (KDS Frontend Shell & Dashboard Visualization)
  Framework: React (Vite), TypeScript, Tailwind CSS, lucide-react

Goal: Build the client tablet dashboard UI and wire up WebSocket connection state telemetry.

Directory Layout:
  frontend/
  ├── index.html
  ├── src/
  │   ├── main.tsx
  │   ├── App.tsx
  │   ├── components/
  │   │   ├── Dashboard.tsx
  │   │   ├── NavigationRail.tsx
  │   │   └── CircularProgress.tsx
  │   └── index.css

Requirements:
  1. UI Layout (Material Design 3 style):
     - Left Navigation Rail with icons. Collapsible to full drawer.
     - Top app status bar showing store name and WS Connection State (Green "Online", Amber "Connecting", Red "Offline").
  2. Circular Progress Rings:
     - Design a reusable component displaying ingredient levels. Value bounds: 0% to 100%. Color transitions: Green (>50%), Amber (20-50%), Red (<20%).
  3. WebSocket Receiver Hook:
     - Write a React hook handling connection retries and updating the global state upon receiving `inventory_update` or `recommendation_alert` WebSocket messages.
  4. Design System Tokens:
     - Configure `tailwind.config.js` to support customized M3 dynamic themes.

Instructions:
  - Write standard Tailwind CSS styles. Do not use external styled libraries unless configured inside the repository workspace.
  - Do not use React components with dummy data; wire them to the active state hook.

How to verify:
  - Run `npm run dev` and open the app in a browser. Ensure WebSocket updates trigger appropriate changes in component values.
```

---

## Prompt 9: KDS Alarm Interactions & Cooking Logs (Milestone 9)

```yaml
Context:
  Project: Bobaflow
  Milestone: 9 (KDS Alarm Interactions & Cooking Logs)
  Framework: React, TypeScript, Tailwind CSS

Goal: Add the flashing Alert Banner component, play loop audio chimes, and wire up dashboard buttons to log cook events.

Directory Layout:
  frontend/src/
  ├── components/
  │   ├── AlertBanner.tsx
  │   ├── ActiveTimers.tsx
  │   └── CalibrationModal.tsx
  └── App.tsx

Requirements:
  1. Alert Banner Component:
     - Render at the top of the dashboard. Flashing red border for critical alert status.
     - Play a warning audio chime using Web Audio API or HTML5 Audio. Sound must loop every 15 seconds.
     - Actions:
       - `[ Start Cooking ]` calls backend route `POST /api/v1/kitchen/brew-actions`.
       - `[ Snooze ]` prompts for a 5-minute snooze interval and pauses the chime.
  2. Active Cooking Progress Cards:
     - Render active timers. Display progress bar counting down until brew completions.
     - Play a chime when a countdown reaches zero.
  3. Calibration Modal:
     - Numeric touch-keypad layout. Selecting an ingredient and typing values submits a post payload to `/api/v1/inventory/recalibrate`.

Instructions:
  - Implement full interaction cycle. Audio context must initialize on the first user click (as required by browser security restrictions).
  - Use high-contrast CSS and large tap targets (minimum size $64\text{px} \times 64\text{px}$).

How to verify:
  - Test clicking "Start Cooking" and verify the alert disappears and a countdown begins.
```

---

## Prompt 10: Closed-Loop Daily Feedback & Retraining (Milestone 10)

```yaml
Context:
  Project: Bobaflow
  Milestone: 10 (Closed-Loop Daily Feedback & Retraining)
  Target Agent: FeedbackAgent

Goal: Build the post-operational audit agent that calculates forecasting errors, wastage profiles, and adjusts safety stock parameters.

Directory Layout:
  backend/
  ├── agents/
  │   └── feedback.py
  └── tests/
      └── test_feedback.py

Requirements:
  1. Performance Analytics Engine:
     - Write a script targeting the database schemas.
     - Queries:
       - Match sales tables with predictor logs to compute Mean Absolute Percentage Error (MAPE) on the 60m window.
       - Sum total weight values from waste tables.
       - Measure crew compliance (percentage of recommendations marked accepted vs ignored).
  2. Safety Buffer Tuning Logic:
     - If pearl waste exceeds 15% of total prepared weight over the day, decrease `pearl_safety_buffer_factor` by 0.05 (min limit: 1.0).
     - If pearl stockout minutes is > 0, increase safety factor by 0.10 (max limit: 1.50).
     - Write updated safety configurations back to PostgreSQL settings database.
  3. Daily Report Generator:
     - Output a detailed audit log payload and save it in `/backend/data/reports/`.

Instructions:
  - Handle zero-division errors if a day logs no transactions.
  - Implement safe validation bounds so safety parameters do not drift to infinity.

How to verify:
  - Run the feedback script with mock history containing stockout minutes and verify safety constants decrease or increase accordingly.
```
