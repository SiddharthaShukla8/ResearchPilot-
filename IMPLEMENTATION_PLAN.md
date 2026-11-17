# Implementation Plan — ResearchPilot

## Architecture Overview
- **Frontend:** React 18 / Vite / TypeScript / Tailwind CSS / Lucide / TanStack Query / React Router
- **Backend:** FastAPI / Python 3.11+ / SQLAlchemy 2 (asyncpg / psycopg) / Alembic / Pydantic v2
- **Vector & Storage:** PostgreSQL + pgvector + Full-text search (tsvector) + Local private file storage interface
- **Worker:** Dedicated Python worker process polling `processing_jobs` using `FOR UPDATE SKIP LOCKED`
- **Agent Orchestrator:** Bounded multi-step agent: Planner -> Tool Execution -> Document Analysis -> Synthesis -> Deterministic Citation Verifier

---

## Milestones & Status

- [x] **Milestone 0: Repository Audit and Planning**
  - Verify workspace & environment
  - Create `docs/REPOSITORY_AUDIT.md`, `IMPLEMENTATION_PLAN.md`, `DECISIONS.md`, `PROGRESS.md`, `AGENTS.md`
- [ ] **Milestone 1: Monorepo Foundation and Developer Experience**
  - Scaffold `backend/`, `frontend/`, `docker-compose.yml`, `.env.example`, `.gitignore`
  - Health checks (`/health/live`, `/health/ready`, `/system/capabilities`)
  - Tooling: Ruff, pytest, vitest, type checking
- [ ] **Milestone 2: Database, Authentication, Projects, and Ownership**
  - SQLAlchemy 2 models + Alembic migrations
  - Argon2 password hashing, JWT access/refresh tokens, session revocation
  - Project CRUD with ownership enforcement
- [ ] **Milestone 3: Secure PDF Library and Ingestion Worker**
  - Upload validation (magic bytes, size, page count, PDF integrity)
  - Safe file storage interface
  - PyMuPDF text extraction with 1-based page numbers
  - Token-aware chunking & embedding pipeline
  - Worker daemon with safe job claiming, heartbeats, and retries
- [ ] **Milestone 4: Retrieval Engine and Evidence Viewer**
  - Hybrid retrieval: pgvector dense cosine search + PostgreSQL tsvector keyword search
  - Reciprocal Rank Fusion (RRF) & token budget packing
  - Evidence viewer API and retrieval evaluation test suite
- [ ] **Milestone 5: Agent Planner, Tool Registry, and Run Orchestration**
  - Strict Pydantic schemas for research plans and tool definitions
  - Allowlisted tool registry (search library, exact terms, metadata, page context)
  - Research run state machine & plan review/edit/approve lifecycle
  - Background orchestrator execution with cancellation & progress events
- [ ] **Milestone 6: Paper Analysis, Synthesis, Comparison, and Citation Verification**
  - Structured per-paper analysis (dataset, methods, metrics, findings, limitations)
  - Thematic synthesis, comparison matrix with comparability labels
  - Agreement / disagreement / contextual difference classification
  - Candidate research gap extraction
  - Deterministic citation verification (document ID, page number, exact excerpt check)
- [ ] **Milestone 7: Complete Frontend Experience and Report Export**
  - Polished editorial UI: Landing, Auth, Dashboard, Project Workspace, PDF Library, Plan Review, Run Activity, Research Report, Evidence Viewer, Settings
  - Markdown and Print/PDF export
  - Real-time run activity polling and event stream
- [ ] **Milestone 8: Quality, Security, Performance, and Release Readiness**
  - Backend pytest suite (Auth, Access Control, PDF safety, Ingestion, Retrieval, Agent, Verification)
  - Frontend test suite
  - Playwright E2E test suite
  - GitHub Actions CI workflow
- [ ] **Milestone 9: Demo Readiness and Documentation**
  - Realistic demo script and sample research papers (synthetic/test)
  - Full documentation (`docs/ARCHITECTURE.md`, `docs/API.md`, `docs/DATA_MODEL.md`, `docs/SECURITY.md`, etc.)
  - Final audit and verification
