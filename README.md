# ResearchPilot: Agentic AI Research and Literature Review Assistant

> **Turn a collection of research papers into a transparent, traceable, evidence-backed literature review—with every important claim linked to its source.**

---

## Key Features

- **Page-Aware PDF Ingestion:** Extracts text with PyMuPDF, preserving 1-based page coordinates. Enforces file signatures, page bounds, and detects scanned/image-only PDFs.
- **Hybrid Retrieval Engine:** Combines dense vector cosine similarity (pgvector) with PostgreSQL `tsvector` keyword search using Reciprocal Rank Fusion (RRF).
- **Agentic AI Planner:** Decomposes user questions into structured sub-questions, evidence requirements, and execution steps. Inspectable and editable before running.
- **Allowlisted Tool Registry:** Sandboxed research tools (`search_paper_library`, `get_document_metadata`, `retrieve_page_context`) with strict tenant isolation.
- **Cross-Paper Synthesis & Comparison:** Generates structured paper summaries, thematic reviews, and comparison matrices labeled with comparability tiers (`directly_comparable`, `partially_comparable`, `not_directly_comparable`).
- **Deterministic Citation Verification:** Ensures cited IDs physically exist in the database, page numbers are bounded, and excerpts map to stored chunk text. Rejects fabricated citations.
- **Publication-Ready Export:** Export reviews to structured Markdown or print-ready PDF format.

---

## Architecture Overview

ResearchPilot is structured as a clean modular monolith backend with a decoupled persistent background worker and a modern React frontend:

- **Frontend:** React 18, TypeScript, Vite, Tailwind CSS, Lucide Icons, React Router.
- **Backend:** FastAPI, Python 3.11+, SQLAlchemy 2 (async), Alembic migrations, Pydantic v2.
- **Database:** PostgreSQL 16 with pgvector extension (or SQLite in-memory for testing).
- **Worker Daemon:** Dedicated process polling `processing_jobs` using `SELECT ... FOR UPDATE SKIP LOCKED`.
- **Security:** Argon2id password hashing, signed JWT access tokens, and rotating refresh tokens with anti-replay `jti`.

---

## Quick Start (Docker Compose)

The easiest way to run ResearchPilot locally:

```bash
# 1. Clone repository
git clone https://github.com/SiddharthaShukla8/ResearchPilot-.git
cd ResearchPilot-

# 2. Setup environment
cp .env.example .env
# (Optional) Supply your OPENAI_API_KEY in .env

# 3. Start stack
docker compose up --build
```

- **Frontend Application:** [http://localhost:5173](http://localhost:5173)
- **Backend Swagger API Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **API Health Check:** [http://localhost:8000/health/live](http://localhost:8000/health/live)

---

## Local Development (Without Docker)

### 1. Backend Setup
```bash
cd backend
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]" greenlet "email-validator>=2.0.0"

# Run migrations
uv run alembic upgrade head

# Start API Server
uv run uvicorn researchpilot.main:app --host 0.0.0.0 --port 8000 --reload

# Start Background Worker (separate terminal)
uv run python -m researchpilot.jobs.worker
```

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

---

## Running Tests & Quality Checks

```bash
# Backend pytest suite (10/10 tests)
cd backend && uv run pytest

# Backend linting (Ruff)
cd backend && uv run ruff check src

# Frontend tests (Vitest)
cd frontend && npm test

# Frontend production build
cd frontend && npm run build
```

---

## Demo Walkthrough

Generate synthetic academic papers and run a literature review:
```bash
cd backend && uv run python ../scripts/generate_sample_papers.py
```
See [`docs/DEMO_SCRIPT.md`](docs/DEMO_SCRIPT.md) for step-by-step instructions.

---

## Documentation Index

- [Architecture Guide](docs/ARCHITECTURE.md)
- [Data Model & Schema](docs/DATA_MODEL.md)
- [API Reference](docs/API.md)
- [Agent Workflow & Provenance](docs/AGENT_WORKFLOW.md)
- [Security Architecture](docs/SECURITY.md)
- [Testing & Quality Gates](docs/TESTING.md)
- [Deployment Instructions](docs/DEPLOYMENT.md)
- [Demo Script](docs/DEMO_SCRIPT.md)
- [Repository Audit](docs/REPOSITORY_AUDIT.md)
