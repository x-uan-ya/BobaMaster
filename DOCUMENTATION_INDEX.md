# BobaMaster Documentation Index

Welcome to BobaMaster! This index helps you navigate the project documentation.

---

## Quick Start (5 minutes)

**New to the project?** Start here:

1. Read: **[README.md](./README.md)** — What is BobaMaster? How does it work?
2. Run: `cd docker && docker-compose up -d`
3. Run: `cd backend && python app/database/init_db.py && uvicorn app.main:app --reload`
4. Run: `cd frontend && npm run dev`
5. Open: http://localhost:5173

---

## Documentation by Use Case

### "I want to understand the problem and solution"
→ **[README.md](./README.md)** — Problem statement, solution overview, architecture

### "I want to deploy this to the cloud"
→ **[DEPLOYMENT.md](./DEPLOYMENT.md)** — Local development, Docker, Vercel, Fly.io

### "I want to understand how AI concepts are demonstrated"
→ **[AI_CONCEPTS.md](./AI_CONCEPTS.md)** — Multi-agent systems, MCP pattern, security, etc.

### "I want to understand what was accomplished in this session"
→ **[PROGRESS.md](./PROGRESS.md)** — Bug fixes, real-time sync, frontend/backend status

### "I want to submit this for a competition/assignment"
→ **[SESSION_SUMMARY.md](./SESSION_SUMMARY.md)** — Project summary, checklist, demo script

### "I'm troubleshooting an issue"
→ **[DEPLOYMENT.md](./DEPLOYMENT.md#troubleshooting)** — Common errors and solutions

---

## Documentation Structure

### Core Documents

| Document | Purpose | Audience |
|---|---|---|
| **README.md** | Main documentation, architecture, API reference | Everyone |
| **AI_CONCEPTS.md** | How course concepts are demonstrated | Judges, evaluators |
| **DEPLOYMENT.md** | Step-by-step deployment guide | DevOps, system admins |
| **PROGRESS.md** | Session work, bugs fixed, status | Project stakeholders |
| **SESSION_SUMMARY.md** | Executive summary, submission checklist | Competition/assignment |

### Design Artifacts

Located in `artifacts/` folder:

| Document | Purpose |
|---|---|
| `product_requirements_document.md` | Business requirements and use cases |
| `system_architecture.md` | Detailed architecture diagrams |
| `multi_agent_system_design.md` | Agent design and communication patterns |
| `milestone_prompts.md` | 10 milestone specifications |
| `development_milestones.md` | Roadmap and milestone completion |
| `task.md` | Task checklist (all complete) |

### Code Documentation

In each source directory:

- **`backend/app/main.py`** — FastAPI app initialization, router setup
- **`backend/app/agents/`** — 7 agent implementations with docstrings
- **`backend/app/api/`** — REST endpoints with docstring documentation
- **`backend/app/models/`** — Pydantic schemas with field descriptions
- **`backend/app/services/`** — Helper services (Redis, PostgreSQL adapters)
- **`frontend/src/components/`** — React components with inline comments
- **`frontend/src/store/`** — Global state management documentation

---

## How to Navigate Different Sections

### Architecture Questions
1. Start: [README.md — Multi-Agent Architecture](./README.md#3-multi-agent-architecture)
2. Deep dive: [AI_CONCEPTS.md — Multi-Agent System](./AI_CONCEPTS.md#1-multi-agent-system-agent-development-kit)
3. Details: [artifacts/system_architecture.md](./artifacts/system_architecture.md)

### Implementation Questions
1. Start: [README.md — Project Structure](./README.md#6-project-structure)
2. Details: Code files (`backend/app/agents/`, `frontend/src/`)
3. Examples: [AI_CONCEPTS.md — Code examples](./AI_CONCEPTS.md)

### Deployment Questions
1. Start: [README.md — Running the Application](./README.md#8-running-the-application)
2. Step-by-step: [DEPLOYMENT.md — All scenarios](./DEPLOYMENT.md)
3. Troubleshooting: [DEPLOYMENT.md — Troubleshooting](./DEPLOYMENT.md#troubleshooting)

### Course Concept Questions
1. Reference: [AI_CONCEPTS.md](./AI_CONCEPTS.md)
2. Look for specific concept:
   - Multi-Agent System → Section 1
   - MCP Pattern → Section 2
   - Security → Section 3
   - Deployability → Section 4
   - Real-Time Sync → Section 5
   - Adapter Pattern → Section 6
   - Closed-Loop Learning → Section 7

---

## File Tree with Documentation

```
BobaMaster/
├── 📖 README.md                          ← START HERE
├── 📖 AI_CONCEPTS.md                     ← Course concepts
├── 📖 DEPLOYMENT.md                      ← How to run/deploy
├── 📖 PROGRESS.md                        ← Session summary
├── 📖 SESSION_SUMMARY.md                 ← For submission
├── 📖 DOCUMENTATION_INDEX.md             ← You are here
│
├── backend/
│   ├── app/
│   │   ├── main.py                       (FastAPI app setup)
│   │   ├── agents/
│   │   │   ├── decompo_agent.py          (Parse POS → ingredients)
│   │   │   ├── inventory_agent.py        (FIFO batch ledger)
│   │   │   ├── context_agent.py          (Weather + calendar)
│   │   │   ├── predictor_agent.py        (Demand forecast)
│   │   │   ├── ops_decider_agent.py      (Safety stock logic)
│   │   │   ├── dispatcher_agent.py       (Gemini + WebSocket)
│   │   │   └── feedback.py               (Daily audit)
│   │   ├── api/
│   │   │   ├── pos.py                    (POS webhook)
│   │   │   ├── inventory.py              (Inventory endpoints)
│   │   │   ├── context.py                (Context API)
│   │   │   ├── forecast.py               (Forecast API)
│   │   │   ├── operations.py             (Decisions API)
│   │   │   ├── dispatcher.py             (Dispatcher API)
│   │   │   ├── feedback.py               (Feedback API)
│   │   │   └── websocket.py              (WebSocket + real-time)
│   │   ├── models/                       (Pydantic schemas)
│   │   ├── services/                     (Redis, PostgreSQL adapters)
│   │   └── database/
│   │       ├── schema.sql                (Database schema)
│   │       └── init_db.py                (Migration runner)
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── src/
│   │   ├── App.tsx                       (Root component)
│   │   ├── components/
│   │   │   ├── Dashboard.tsx             (Main view)
│   │   │   ├── InventoryPage.tsx         (Inventory management)
│   │   │   ├── ForecastPage.tsx          (Predictions)
│   │   │   ├── FeedbackPage.tsx          (Daily audit)
│   │   │   ├── AgentPanel.tsx            (AI controls)
│   │   │   └── ...more components
│   │   ├── store/
│   │   │   └── dashboardStore.ts         (Global state)
│   │   └── hooks/
│   │       └── useWebSocket.ts           (Real-time listener)
│   ├── package.json
│   └── .env.example
│
├── docker/
│   └── docker-compose.yml                (PostgreSQL + Redis)
│
├── artifacts/
│   ├── product_requirements_document.md
│   ├── system_architecture.md
│   ├── multi_agent_system_design.md
│   ├── development_milestones.md
│   └── ...more design docs
│
└── .gitignore
```

---

## How to Read the Code

### Architecture Flow (Follow This Order)

1. **Start:** `frontend/src/App.tsx` (entry point)
2. **Route handlers:** `frontend/src/components/` (each page component)
3. **State management:** `frontend/src/store/dashboardStore.ts` (global state)
4. **WebSocket:** `frontend/src/hooks/useWebSocket.ts` (real-time connection)
5. **Backend entry:** `backend/app/main.py` (API setup)
6. **Agent pipeline:** `backend/app/agents/` (business logic)
7. **API endpoints:** `backend/app/api/` (HTTP handlers)
8. **Models:** `backend/app/models/` (data validation)
9. **Services:** `backend/app/services/` (external integrations)

### Key Code Sections to Review

#### For Multi-Agent System
- `backend/app/agents/decompo_agent.py` — Simple, clear logic
- `backend/app/agents/inventory_agent.py` — FIFO implementation
- `backend/app/agents/ops_decider_agent.py` — Safety stock algorithm

#### For Real-Time Sync
- `backend/app/api/pos.py` — **NEW: Applies deductions + broadcasts**
- `backend/app/api/websocket.py` — WebSocket manager
- `frontend/src/hooks/useWebSocket.ts` — Client-side listener

#### For Gemini Integration
- `backend/app/agents/dispatcher_agent.py` — Construct context + LLM call
- `backend/app/models/dispatcher.py` — Data schemas

#### For Error Handling
- Every API endpoint in `backend/app/api/` — Try/except + logging
- `frontend/src/components/InventoryPage.tsx` — Error display

---

## Search Tips

### Find implementations of a concept
```bash
# Multi-agent: grep -r "Agent" backend/app/agents/
# WebSocket: grep -r "WebSocket\|broadcast" backend/app/
# Pydantic: grep -r "BaseModel\|Field" backend/app/models/
# React hooks: grep -r "useState\|useEffect" frontend/src/
```

### Find a specific endpoint
- Check `backend/app/api/pos.py` for POS logic
- Check `backend/app/api/inventory.py` for inventory operations
- Check `backend/app/api/websocket.py` for real-time connections

### Find a React component
- Dashboard: `frontend/src/components/Dashboard.tsx`
- Inventory management: `frontend/src/components/InventoryPage.tsx`
- Forecasts: `frontend/src/components/ForecastPage.tsx`
- Audit: `frontend/src/components/FeedbackPage.tsx`

---

## Documentation Maintenance

### How to Update Docs

1. **Architecture changes?** → Update `AI_CONCEPTS.md`
2. **New feature?** → Update `README.md` and `artifacts/`
3. **Deployment changes?** → Update `DEPLOYMENT.md`
4. **Bug fixes?** → Add to `PROGRESS.md`
5. **Code comments** → Add inline comments in source files

### Build Verification

```bash
# Frontend
cd frontend && npm run build  # Should succeed with no errors

# Backend  
cd backend && python -m py_compile app/main.py  # Should succeed

# Documentation
# All .md files should render correctly on GitHub
```

---

## Quick Reference: Common Tasks

### "How do I run the project?"
→ [README.md — Running the Application](./README.md#8-running-the-application)

### "What's the architecture?"
→ [README.md — Multi-Agent Architecture](./README.md#3-multi-agent-architecture)

### "How do I deploy to Vercel?"
→ [DEPLOYMENT.md — Frontend Deployment (Vercel)](./DEPLOYMENT.md#option-c-vercel-recommended)

### "How do I deploy the backend?"
→ [DEPLOYMENT.md — Backend Deployment](./DEPLOYMENT.md#backend-deployment)

### "What are the AI concepts?"
→ [AI_CONCEPTS.md](./AI_CONCEPTS.md)

### "What was fixed in this session?"
→ [PROGRESS.md — Issues Fixed](./PROGRESS.md#issues-fixed-this-session)

### "Is it ready for submission?"
→ [SESSION_SUMMARY.md — Production Readiness Checklist](./SESSION_SUMMARY.md#production-readiness-checklist)

### "Help, something's broken!"
→ [DEPLOYMENT.md — Troubleshooting](./DEPLOYMENT.md#troubleshooting)

---

## Document Reading Time

| Document | Reading Time | Best For |
|---|---|---|
| README.md | 15 min | Understanding the project |
| AI_CONCEPTS.md | 15 min | Learning how concepts are applied |
| DEPLOYMENT.md | 20 min | Setting up and troubleshooting |
| PROGRESS.md | 10 min | Session work summary |
| SESSION_SUMMARY.md | 10 min | Competition submission |

**Total: ~70 minutes to read all documentation.**

---

## Version Information

- **Project Version:** 1.0.0
- **Build Date:** June 25, 2024
- **Status:** Production-ready
- **All 10 milestones:** ✅ Complete

---

## Navigation Tips

### For Judges/Evaluators
1. Read: **SESSION_SUMMARY.md** (2 min)
2. Read: **AI_CONCEPTS.md** (15 min)
3. Check: Code in `backend/app/agents/` (concepts in action)
4. Watch: Demo video

### For Developers
1. Read: **README.md** (15 min)
2. Check: **DEPLOYMENT.md** (5 min)
3. Run: `docker-compose up -d && cd backend && ... && cd ../frontend && ...`
4. Explore: Code, make changes, test

### For DevOps/Deployment
1. Read: **DEPLOYMENT.md** (20 min)
2. Follow steps for your platform (Vercel, Fly.io, etc.)
3. Set environment variables
4. Deploy

### For Learning
1. Read: **AI_CONCEPTS.md** (15 min)
2. Read: **PROGRESS.md** (10 min)
3. Review code implementations
4. Run locally and experiment

---

**Navigation complete! Choose your starting point above.**

