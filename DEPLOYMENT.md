# Deployment Guide for BobaMaster

This guide covers deploying BobaMaster to various environments: local development, Docker, cloud platforms, and Vercel.

---

## Quick Start (5 minutes)

### Prerequisites
- Python 3.11+ and Node.js 18+
- Docker & Docker Compose (for full stack)
- Gemini API key (optional, system works without it)

### Local Development
```bash
# 1. Clone and navigate
git clone <repo>
cd BobaMaster

# 2. Start infrastructure
cd docker && docker-compose up -d && cd ..

# 3. Start backend
cd backend
pip install -r requirements.txt
python app/database/init_db.py
uvicorn app.main:app --reload --port 8000
# Backend running at http://localhost:8000

# 4. Start frontend (new terminal)
cd frontend
npm install
npm run dev
# Frontend running at http://localhost:5173

# 5. Open in browser
# http://localhost:5173
```

---

## Backend Deployment

### Option A: Local + Docker Infrastructure

```bash
# Start services
cd docker && docker-compose up -d

# Initialize database
cd ../backend
pip install -r requirements.txt
python app/database/init_db.py

# Run backend
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Verify
curl http://localhost:8000/health
# Response: {"status": "healthy", ...}
```

### Option B: Docker (Full Stack)

```bash
# Build backend image
docker build -t bobamaster-backend -f Dockerfile .

# Run with docker-compose
docker-compose -f docker/docker-compose.yml up -d

# Logs
docker-compose logs -f backend

# Stop
docker-compose down
```

### Option C: Cloud Deployment (Fly.io)

```bash
# 1. Create Fly.io account
# 2. Create fly.toml in project root

[build]
  image = "bobamaster-backend"

[[services]]
  internal_port = 8000
  protocol = "tcp"

  [services.ports]
    ports = [8000]

[[services]]
  protocol = "https"

# 3. Set environment variables
flyctl secrets set GEMINI_API_KEY=sk-...
flyctl secrets set POSTGRES_PASSWORD=...
flyctl secrets set REDIS_URL=redis://redis-service:6379

# 4. Deploy
flyctl deploy

# Logs
flyctl logs
```

---

## Frontend Deployment

### Option A: Development Server
```bash
cd frontend
npm install
npm run dev
# Open http://localhost:5173
```

### Option B: Build & Serve Locally
```bash
cd frontend
npm install
npm run build
# dist/ folder created with optimized production build

# Serve with any static server
npx serve dist
# Open http://localhost:3000
```

### Option C: Vercel (Recommended)

#### Prerequisites
- GitHub account with repo pushed
- Vercel account ([vercel.com](https://vercel.com))

#### Steps
1. **Log in to Vercel and click "Add New Project"**
2. **Select your GitHub repository**
3. **Vercel auto-detects the config from `vercel.json`**
4. **Set Environment Variables in Vercel Dashboard:**

   | Variable | Value | Example |
   |---|---|---|
   | `VITE_API_URL` | Backend API URL | `https://bobamaster-api.fly.dev` |
   | `VITE_WS_URL` | WebSocket URL | `wss://bobamaster-api.fly.dev` |
   | `VITE_SHOP_ID` | Shop UUID | `00000000-0000-0000-0000-000000000001` |
   | `VITE_STORE_NAME` | Display name | `Downtown Store` |

5. **Click "Deploy"**
6. **Get your URL** (e.g., `https://bobamaster.vercel.app`)

#### Vercel Config (already in repo)
```json
{
  "buildCommand": "npm run build",
  "outputDirectory": "frontend/dist",
  "framework": "vite"
}
```

---

## Environment Variables

### Backend (.env)
```bash
# Required
GEMINI_API_KEY=your-gemini-key

# Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-password
POSTGRES_DB=bobaflow

# Redis
REDIS_URL=redis://localhost:6379

# Optional
LOG_LEVEL=INFO
API_PORT=8000
```

### Frontend (.env)
```bash
# Backend connection
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000

# Shop identification
VITE_SHOP_ID=00000000-0000-0000-0000-000000000001
VITE_STORE_NAME=Downtown Store
```

---

## Troubleshooting

### Backend Won't Start

#### Error: "Connection refused to Redis"
```
HTTPException: Error 10061 connecting to localhost:6379
```
**Solution:**
```bash
# Check if Redis is running
docker-compose ps

# If not running:
cd docker && docker-compose up -d redis

# Or use in-memory fallback (automatically enabled)
# Backend will log: redis_mode: "in-memory"
```

#### Error: "GEMINI_API_KEY not set"
```
WARNING: GEMINI_API_KEY not set; using fallback
```
**Solution:**
```bash
# Set the environment variable
export GEMINI_API_KEY=your-actual-key
# Or in .env file:
echo "GEMINI_API_KEY=your-key" >> backend/.env

# Restart backend
uvicorn app.main:app --reload
```

#### Error: "Cannot import app.main"
```
ModuleNotFoundError: No module named 'app'
```
**Solution:**
```bash
# Ensure you're in the backend directory
cd backend

# Or add backend to Python path
cd ..
PYTHONPATH=backend uvicorn backend.app.main:app --reload
```

### Frontend Won't Build

#### Error: "Cannot find module"
```
TS2307: Cannot find module '@lucide-react'
```
**Solution:**
```bash
cd frontend
npm install
npm run build
```

#### Error: "VITE_API_URL not set"
**Solution:**
```bash
cd frontend
cp .env.example .env
# Edit .env with your backend URL
npm run dev
```

### WebSocket Connection Failed

#### Frontend shows "Offline" status
```
Error: WebSocket connection failed
```
**Solution:**
1. Verify backend is running: `curl http://localhost:8000/health`
2. Check WebSocket URL in frontend `.env`: `VITE_WS_URL=ws://localhost:8000`
3. Check browser console for connection errors
4. If deployed: ensure WebSocket is enabled (not all hosting supports it)

### Inventory Not Updating in Real-Time

#### Inventory changes appear after manual refresh
**Likely causes:**
1. WebSocket not connected (check browser Network tab)
2. Backend not broadcasting updates (check server logs)

**Solution:**
```bash
# Check server logs
docker-compose logs -f backend | grep broadcast

# Verify WebSocket is working:
curl http://localhost:8000/api/v1/dispatcher/connections
# Should show connected shops

# Test manual trigger:
curl -X POST "http://localhost:8000/api/v1/dispatcher/trigger-test-alert?shop_id=00000000-0000-0000-0000-000000000001"
```

---

## Database Management

### View Database (PostgreSQL)

```bash
# Connect to PostgreSQL
psql postgresql://postgres:postgres@localhost:5432/bobaflow

# List tables
\dt

# View schema
\d inventory_states
\d brew_logs
\d recommendation_logs

# Query active batches
SELECT batch_id, ingredient_id, remaining_qty, expires_at
FROM brew_logs
WHERE completed_at IS NOT NULL
ORDER BY expires_at;

# View system settings
SELECT key, value, updated_at FROM system_settings;

# Exit
\q
```

### Reset Database

```bash
# Drop and recreate
docker-compose down -v
docker-compose up -d postgres redis
cd backend && python app/database/init_db.py
```

### Backup Database

```bash
# Create dump
docker-compose exec postgres pg_dump \
  -U postgres bobaflow > backup_$(date +%Y%m%d).sql

# Restore dump
docker-compose exec -T postgres psql \
  -U postgres bobaflow < backup_20240624.sql
```

---

## Performance Tuning

### Redis Cache
BobaMaster caches context (weather, calendar) for 15 minutes to avoid redundant API calls.

```bash
# View cache keys
redis-cli KEYS "*context:*"

# View cache size
redis-cli INFO memory

# Clear all cache (development only)
redis-cli FLUSHALL
```

### Database Queries
TimescaleDB hypertables automatically compress old data. Check usage:

```bash
# Connect to PostgreSQL
psql postgresql://postgres:postgres@localhost:5432/bobaflow

# View hypertable sizes
SELECT hypertable_name, table_bytes, index_bytes, toast_bytes, total_bytes
FROM hypertable_detailed_size('inventory_states');

# Check compression
SELECT * FROM _timescaledb_internal.compressed_hypertable_stats;
```

### Scaling

#### Multi-process Backend
```bash
# Use gunicorn with 4 workers
pip install gunicorn
gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker

# Or use uvicorn with multiple processes
uvicorn app.main:app --port 8000 --workers 4
```

#### Horizontal Frontend Scaling
Vercel automatically scales based on traffic. No configuration needed.

---

## Monitoring & Logging

### Backend Logs
```bash
# Live logs
docker-compose logs -f backend

# Logs from specific service
docker-compose logs redis

# View past logs
docker-compose logs backend | tail -100
```

### Frontend Logs
```bash
# Browser console (press F12)
# Look for:
# - Network errors in Network tab
# - Console errors in Console tab
# - WebSocket messages in Network > WS tab
```

### Health Check
```bash
# Backend health
curl http://localhost:8000/health
# Response: {"status": "healthy", "redis_mode": "redis" or "in-memory"}

# API documentation
curl http://localhost:8000/docs
# Opens interactive API docs in browser

# Active WebSocket connections
curl http://localhost:8000/api/v1/dispatcher/connections
```

---

## Production Checklist

- [ ] Gemini API key set and valid
- [ ] PostgreSQL and Redis configured and running
- [ ] Database migrations completed (`python app/database/init_db.py`)
- [ ] Backend environment variables set (`.env`)
- [ ] Frontend build succeeds (`npm run build`)
- [ ] Frontend environment variables set (`.env`)
- [ ] Backend health check passes (`curl /health`)
- [ ] WebSocket connections working (check Network tab)
- [ ] SSL/TLS enabled (HTTPS/WSS)
- [ ] Rate limiting configured (if needed)
- [ ] Backup strategy in place
- [ ] Monitoring and alerting set up
- [ ] Load balancer configured (if scaling)

---

## Common Deployment Scenarios

### Scenario 1: Single Demo Instance (Local)
```bash
# Minimal setup for testing
docker-compose up -d
cd backend && python app/database/init_db.py
uvicorn app.main:app --port 8000 &
cd ../frontend && npm run dev
# Done! No cloud costs.
```

### Scenario 2: Proof of Concept (Fly.io + Vercel)
```bash
# Deploy backend to Fly.io
flyctl launch
flyctl secrets set GEMINI_API_KEY=...
flyctl deploy

# Deploy frontend to Vercel
# Connect GitHub repo, set env vars, done

# Result: Live at https://bobamaster.vercel.app
```

### Scenario 3: Production (Multiple Shops)
```bash
# Load balancer + multiple backend instances + RDS + Elasticache
# Use infrastructure as code (Terraform/CloudFormation)
# Auto-scaling groups for backends
# Separate PostgreSQL and Redis for redundancy
# CDN for frontend (Cloudflare, CloudFront)
```

---

## Support

### Resources
- API Docs: http://localhost:8000/docs
- README: `/README.md`
- Architecture: `/AI_CONCEPTS.md`
- Troubleshooting: This file

### Debugging Tips
1. Always check `.env` files are loaded
2. Verify services are running: `docker-compose ps`
3. Check logs: `docker-compose logs <service>`
4. Use curl to test API endpoints
5. Use browser DevTools to check WebSocket connections

---

## Update Instructions

### Update Dependencies
```bash
# Backend
cd backend
pip install --upgrade -r requirements.txt

# Frontend
cd frontend
npm update
npm run build
```

### Update to Latest Code
```bash
git fetch origin
git pull origin main
cd backend && python app/database/init_db.py  # Run migrations
npm run build  # Rebuild frontend
```

---

*Last updated: June 2024. For latest deployment info, see `README.md`.*

