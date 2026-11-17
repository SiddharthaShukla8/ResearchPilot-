# Deployment Guide — ResearchPilot

## 1. Local Development via Docker Compose

```bash
# 1. Clone repository
git clone https://github.com/SiddharthaShukla8/ResearchPilot-.git
cd ResearchPilot-

# 2. Configure environment
cp .env.example .env
# Edit .env and supply your OPENAI_API_KEY (optional for mock testing)

# 3. Start full stack (PostgreSQL + pgvector, FastAPI API, Background Worker, React Frontend)
docker compose up --build
```

Access services:
- Frontend UI: `http://localhost:5173`
- Backend API Docs: `http://localhost:8000/docs`
- Health Probe: `http://localhost:8000/health/live`

## 2. Local Host Run (Without Docker)

### Backend & Worker
```bash
cd backend
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]" greenlet "email-validator>=2.0.0"

# Apply database migrations
uv run alembic upgrade head

# Start API server (Terminal 1)
uv run uvicorn researchpilot.main:app --host 0.0.0.0 --port 8000 --reload

# Start Background Worker (Terminal 2)
uv run python -m researchpilot.jobs.worker
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```
