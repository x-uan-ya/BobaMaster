# Software Development Milestones: Bobaflow Platform

This document outlines a 10-milestone roadmap to build the Bobaflow AI Operations Platform. Each milestone is structured to be independently testable and achievable within a single focused coding session.

---

## Milestone 1: Project Setup & Database Schema Initialization
*   **Goal:** Establish the project structure, spin up local services (database, cache), and initialize schemas.
*   **Tasks:**
    1.  Initialize a Python project with `poetry` or `pip` (FastAPI backend).
    2.  Write a `docker-compose.yml` defining PostgreSQL (TimescaleDB) and Redis.
    3.  Create SQL schema scripts for tables: `inventory_states`, `brew_logs`, `recommendation_logs`, `recommendation_feedback`.
    4.  Write a python setup script to execute SQL migrations.
*   **Files to create:**
    *   `docker-compose.yml`
    *   `requirements.txt`
    *   `database/schema.sql`
    *   `database/init_db.py`
*   **How to test:** Run `docker-compose up -d`, then execute `python database/init_db.py`.
*   **Expected output:** Database and Redis services running; schemas verified inside PostgreSQL console via `\dt`.

---

## Milestone 2: POS Event Ingestion & Recipe Decomposition (`DecompoAgent`)
*   **Goal:** Ingest POS webhook event payloads and map transaction items to raw ingredient deductions.
*   **Tasks:**
    1.  Create a FastAPI app hosting `/api/v1/pos/webhook`.
    2.  Build the `DecompoAgent` that parses menu items, modifiers (e.g. "extra pearls"), and resolves them into raw weights.
    3.  Create a static recipe dictionary in JSON format.
*   **Files to create:**
    *   `backend/main.py`
    *   `backend/agents/decompo.py`
    *   `backend/config/recipes.json`
    *   `backend/tests/test_decompo.py`
*   **How to test:** Run backend server, send mock POS webhook POST payload via `curl` or Postman, assert payload parsing.
*   **Expected output:** Webhook returns HTTP `200 OK` with JSON payload confirming specific ingredient deductions (e.g. `{"tapioca_pearls": 50.0}`).

---

## Milestone 3: Inventory State Ledger & FIFO Batches (`InventoryAgent`)
*   **Goal:** Implement real-time prepared inventory estimation tracking individual cooked batches and expiration limits.
*   **Tasks:**
    1.  Implement `InventoryAgent` managing a FIFO queue of cooked batches.
    2.  Create REST endpoints to log manual stock updates (`POST /api/v1/inventory/recalibrate`) and waste logs.
    3.  Implement deduction logic: subtracting sales volume from the oldest active cooked batch.
*   **Files to create:**
    *   `backend/agents/inventory.py`
    *   `backend/tests/test_inventory.py`
*   **How to test:** Seed two cooked batches of pearls with differing exiries. Post mock sales deductions and check that the oldest batch's weight decreases first, then expires, shifting deductions to the second.
*   **Expected output:** Inventory state endpoint returns precise remaining weights and correct nearest expiration timestamp.

---

## Milestone 4: Context Enrichment Service (`ContextAgent`)
*   **Goal:** Compile location and temporal metadata into a normalized operational context vector.
*   **Tasks:**
    1.  Build `ContextAgent` with mock clients for weather forecasts (temperature, rain) and school calendars.
    2.  Write logic resolving coordinate locations to active local context coefficients.
*   **Files to create:**
    *   `backend/agents/context.py`
    *   `backend/tests/test_context.py`
*   **How to test:** Trigger the context fetch function with standard latitude/longitude coordinates; check the resulting JSON data.
*   **Expected output:** Valid context vector JSON output containing fields `temp_c`, `rain_intensity_mm`, and `school_in_session`.

---

## Milestone 5: Numerical Demand Forecasting Engine (`PredictorAgent`)
*   **Goal:** Run statistical forecasts to project cup sales for the next 30, 60, and 120-minute frames.
*   **Tasks:**
    1.  Create `PredictorAgent` with a tabular regressor script (mock weights/inference code using LightGBM or simple moving averages).
    2.  Integrate the recent sales velocity logs (read from Redis cache) and the context vector.
*   **Files to create:**
    *   `backend/agents/predictor.py`
    *   `backend/tests/test_predictor.py`
*   **How to test:** Execute predictor unit test passing recent velocity trends and context factors (e.g. temperature drops + school lets out).
*   **Expected output:** Forecast object returning numeric projections for pearls and tea bases across all three target horizons.

---

## Milestone 6: Operational Decision Model (`OpsDeciderAgent`)
*   **Goal:** Evaluate inventory runway against cook lead times to output discrete cooking suggestions.
*   **Tasks:**
    1.  Build `OpsDeciderAgent` utilizing safety stock algorithms.
    2.  Resolve decisions: `BREW_NOW`, `WAIT`, or `WARN` by comparing predicted shortfalls with available cooked stock.
*   **Files to create:**
    *   `backend/agents/ops_decider.py`
    *   `backend/tests/test_ops_decider.py`
*   **How to test:** Seed low pearl inventory (400g) and set a high 60-minute forecast projection (2000g). Run the decider.
*   **Expected output:** Decision output logs a critical `BREW_NOW` action with target volume specified.

---

## Milestone 7: Gemini Explanation & WebSocket Broadcast (`DispatcherAgent`)
*   **Goal:** Generate LLM explanations and stream operational alerts to client screens.
*   **Tasks:**
    1.  Integrate Google GenAI API calling Gemini 1.5 Flash.
    2.  Construct the prompt combining decision metrics and context.
    3.  Set up WebSocket endpoints in FastAPI to push active alert payloads.
*   **Files to create:**
    *   `backend/agents/dispatcher.py`
    *   `backend/tests/test_dispatcher.py`
*   **How to test:** Execute a test script feeding a decision payload. Check console log for LLM text and verify WebSocket broadcast receives the payload.
*   **Expected output:** Structured WebSocket message containing natural language explanation (e.g. *"School rush starting in 15 mins... "*).

---

## Milestone 8: KDS Frontend Shell & Dashboard Visualization
*   **Goal:** Create the basic React front-end dashboard visualizing real-time metrics.
*   **Tasks:**
    1.  Initialize a Vite React project with Tailwind CSS.
    2.  Build the layout grid: Navigation Rail, App Bar, Live State Cards (circular progress rings).
    3.  Integrate WebSocket listeners to update the UI on receipt of backend events.
*   **Files to create:**
    *   `frontend/package.json`
    *   `frontend/src/App.tsx`
    *   `frontend/src/components/Dashboard.tsx`
*   **How to test:** Launch Vite dev server, trigger a mock WebSocket event from the backend, verify progress rings and alerts update dynamically.
*   **Expected output:** Web page showing color-coded progress circles representing pearl and tea base quantities.

---

## Milestone 9: KDS Alarm Interactions & Cooking Logs
*   **Goal:** Implement alert acknowledgement workflows (snooze, start cooking) on the tablet.
*   **Tasks:**
    1.  Build Alert Banner component with sound chimes (looping audio every 15s).
    2.  Wire up `[ Start Cooking ]` and `[ Snooze ]` button actions calling API routes.
    3.  Add active brewing progress cards with countdown timers.
*   **Files to create:**
    *   `frontend/src/components/AlertBanner.tsx`
    *   `frontend/src/components/ActiveTimers.tsx`
*   **How to test:** Trigger alert. Verify chime loops. Click `[ Start Cooking ]`. Verify audio silences, alert disappears, and a countdown timer starts ticking.
*   **Expected output:** Client interactions mutate backend inventory states and update active cooking lists.

---

## Milestone 10: Closed-Loop Daily Feedback & Retraining (`FeedbackAgent`)
*   **Goal:** Review daily accuracy, calculate waste, and automatically calibrate forecasting thresholds.
*   **Tasks:**
    1.  Build `FeedbackAgent` script parsing daily transaction, waste, and feedback tables.
    2.  Calculate Mean Absolute Percentage Error (MAPE).
    3.  Adjust safety factor parameters in system configurations.
*   **Files to create:**
    *   `backend/agents/feedback.py`
    *   `backend/tests/test_feedback.py`
*   **How to test:** Seed mock historical table logs representing a day of high waste due to over-forecasting. Run feedback agent script.
*   **Expected output:** Generated JSON report auditing store performance and updated model config showing a decreased safety buffer constant.
