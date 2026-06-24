# BobaMaster - AI Operations Agent for Bubble Tea Shops

BobaMaster is an enterprise AI operations platform designed to solve the over-brewing vs. under-brewing challenge in bubble tea stores. It tracks inventory, predicts demand, and alerts kitchen staff when to cook fresh tapioca pearls and brew tea bases.

---

## Project Structure

```
BobaMaster/
├── docker/
│   └── docker-compose.yml       # PostgreSQL (TimescaleDB) and Redis configurations
├── backend/
│   ├── requirements.txt         # Package dependencies
│   └── app/
│       ├── api/                 # API Routes and endpoints
│       ├── agents/              # Decision and Forecasting AI agents
│       │   ├── forecast_agent.py
│       │   ├── inventory_agent.py
│       │   ├── decision_agent.py
│       │   ├── insight_agent.py
│       │   └── learning_agent.py
│       ├── services/            # Shared service layers (Gemini client, Weather API)
│       │   ├── gemini_service.py
│       │   ├── weather_service.py
│       │   └── inventory_service.py
│       ├── database/
│       │   ├── schema.sql       # Database table declarations (TimescaleDB hypertables)
│       │   └── init_db.py       # Database schema migration script
│       ├── models/              # Pydantic V2 data validation schemas
│       └── prompts/             # LLM prompt templates
├── frontend/                    # UI tablet Dashboard
├── docs/                        # Architectural documentation
├── tests/                       # Automated testing suites
└── README.md
```

---

## Milestone 1: Setup & Initialization

### Prerequisites
*   Docker & Docker Compose
*   Python 3.10+

### Steps to Run
1.  **Start Database and Caching Containers:**
    ```bash
    cd BobaMaster/docker
    docker-compose up -d
    ```

2.  **Install Python Dependencies:**
    ```bash
    cd ../backend
    pip install -r requirements.txt
    ```

3.  **Run Database Migration:**
    ```bash
    python app/database/init_db.py
    ```

### Environment Settings
You can customize connection paths using environment variables:
*   `DATABASE_URL`: Connection URL for PostgreSQL (TimescaleDB). Default: `postgresql://postgres:postgres@localhost:5432/BobaMaster`
*   `REDIS_URL`: Connection URL for Redis. Default: `redis://localhost:6379/0`
