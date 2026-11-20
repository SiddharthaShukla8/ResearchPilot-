# ResearchPilot 🧭

> **Agentic AI Research and Literature Review Assistant**  
> *Turn collections of academic papers into transparent, traceable, evidence-backed literature reviews—with every important claim linked to its verifiable source.*

[![CI](https://github.com/SiddharthaShukla8/ResearchPilot-/actions/workflows/ci.yml/badge.svg)](https://github.com/SiddharthaShukla8/ResearchPilot-/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![React 18](https://img.shields.io/badge/React-18-61dafb.svg)](https://react.dev/)
[![PostgreSQL 16+](https://img.shields.io/badge/PostgreSQL-16+-336791.svg)](https://www.postgresql.org/)
[![pgvector](https://img.shields.io/badge/pgvector-0.8+-orange.svg)](https://github.com/pgvector/pgvector)

---

## 1. Project Overview

**ResearchPilot** is an open-source, full-stack, agentic research assistant designed for university students, researchers, and academic teams. Unlike generic chat interfaces or simple PDF search tools that summarize text in a single prompt, ResearchPilot implements a **bounded, observable agent state machine**:

1. Ingests and indexes user-uploaded academic PDFs with page-level provenance.
2. Decomposes complex research questions into structured sub-questions and methodology targets.
3. Solicits explicit human-in-the-loop plan inspection and approval before spending compute.
4. Executes allowlisted tools to retrieve evidence using **Hybrid Dense-Vector + Lexical Search with Reciprocal Rank Fusion (RRF)**.
5. Performs comparative analysis across methods, datasets, sample sizes, and quantitative findings.
6. Synthesizes a structured literature review where **every citation is deterministically verified** against original document chunks and 1-based page bounds.

---

## 2. Problem Statement

Existing literature review tools suffer from three fundamental flaws:

1. **Hallucination & Fabrication:** Large Language Models frequently invent citations, author years, statistical findings, or DOIs when prompted directly.
2. **Black-Box Opacity:** Users cannot inspect what tools the model invoked, what queries it ran, or how contradictory evidence was weighed.
3. **Lack of Human Guidance:** Fully autonomous agents often wander off-topic, executing expensive operations on irrelevant tangents without human oversight.

ResearchPilot solves this with **strict provenance grounding**: uploaded PDFs are the sole source of truth, research plans require human approval, and an automated verification engine removes or flags any assertion lacking exact textual backing.

---

## 3. Key Features

- 📑 **Secure Multi-PDF Ingestion:** PyMuPDF-based text and metadata extraction preserving 1-based page coordinates. Strict validation checks file size (25 MB), page bounds (500 pages), PDF magic bytes (`%PDF-`), scanned document detection, and SHA-256 deduplication.
- 🔍 **Hybrid Retrieval Engine:** Combines high-dimensional dense vector embeddings (`vector <=> embedding`) with PostgreSQL full-text search (`tsvector` / `websearch_to_tsquery`) fused via Reciprocal Rank Fusion ($k=60$).
- 🧠 **Observable Agent State Machine:** Multi-stage execution cycle: `queued` &rarr; `retrieving` &rarr; `analysing` &rarr; `synthesising` &rarr; `verifying` &rarr; `completed`.
- 🛡️ **Human-in-the-Loop Plan Review:** Inspect sub-questions, methodology targets, and comparative dimensions with full freedom to edit or refine parameters before execution.
- 📊 **Comparative Synthesis Matrix:** Generates side-by-side matrices contrasting architectures, datasets, metrics, limitations, and explicit comparability classifications (`directly_comparable`, `partially_comparable`, `not_directly_comparable`).
- ⚖️ **Disagreement & Research Gap Identification:** Surfaces conflicting claims, contextual variations across cohorts, and candidate research gaps with explicit corpus caveats.
- 🎯 **Interactive Citation Inspection:** Click any citation badge (`[1]`, `[2]`) in the report viewer to open the exact excerpt modal showing the verified source document, 1-based page number, and similarity score.
- 📄 **Publication-Grade Export:** Export synthesized literature reviews to formatted Markdown and paginated PDF documents with a single click.
- 🌐 **Dual AI Execution Modes:** Seamlessly toggles between **Live OpenAI Mode** (`gpt-4o-mini`, `text-embedding-3-small`) and **Offline Mock Mode** (`MockAIProvider`, deterministic bag-of-words hash embeddings with zero cost and no external credentials).

---

## 4. What Makes ResearchPilot Different

| Capability | Generic PDF Chatbot | Pure RAG Wrapper | ResearchPilot |
| :--- | :--- | :--- | :--- |
| **Agentic Planning** | ❌ None (Single-prompt) | ❌ None | ✅ Structured plan with human-in-the-loop review |
| **Multi-Paper Comparison**| ⚠️ Superficial | ⚠️ Fragile multi-context | ✅ Structured comparative matrices and agreement tagging |
| **Citation Verification** | ❌ Hallucinated | ⚠️ Vector top-k only | ✅ Deterministic chunk-level text and page verification |
| **Tool Execution** | ❌ None | ❌ Static retrieval | ✅ Allowlisted, observable, event-streamed tool registry |
| **Offline Operation** | ❌ Blocked without API key | ❌ Blocked | ✅ Full offline capability via deterministic `MockAIProvider` |

---

## 5. Technology Stack

- **Frontend:** React 18, TypeScript, Tailwind CSS, Lucide React, React Router DOM v6, Vite.
- **Backend API:** FastAPI (Python 3.11+ / 3.14 compatible), Pydantic v2, Uvicorn.
- **Database & Search:** PostgreSQL 16/18, `pgvector` extension, SQLAlchemy 2.0 (AsyncIO), Alembic.
- **Worker & Queue:** Asynchronous PostgreSQL row-level locked queue (`SELECT ... FOR UPDATE SKIP LOCKED`).
- **PDF Processing:** PyMuPDF (`fitz`), TikToken (token-bounded recursive chunking).
- **AI Providers:** OpenAI Async Client (`gpt-4o-mini`, `text-embedding-3-small`) + `MockAIProvider`.
- **Testing & Quality:** Pytest, Pytest-AsyncIO, Vitest, Playwright, Ruff.
- **Deployment:** Docker, Docker Compose, Nginx (SPA reverse proxy).

---

## 6. System Architecture

```mermaid
flowchart TD
    subgraph Client ["Client Layer"]
        Browser["React 18 SPA (Vite / Nginx :5173)"]
    end

    subgraph Gateway ["Reverse Proxy / API Gateway"]
        Nginx["Nginx Reverse Proxy (:80 -> :5173)"]
        FastAPI["FastAPI REST API (:8000)"]
    end

    subgraph Services ["Backend Core Services"]
        Auth["Auth & Security (Argon2 / JWT)"]
        Ingest["Document Ingestion & Chunking"]
        Retriever["Hybrid Retrieval (Vector + Lexical RRF)"]
        Planner["Agent Planner & Tool Registry"]
        Orchestrator["Research Orchestrator"]
        Verifier["Citation Provenance Verifier"]
    end

    subgraph Storage ["Persistence Layer"]
        Postgres[("PostgreSQL 16/18 + pgvector")]
        DocStore[("Private Document Storage")]
    end

    subgraph Workers ["Async Execution"]
        Worker["Background Job Worker (FOR UPDATE SKIP LOCKED)"]
    end

    Browser -->|HTTP / SPA Navigation| Nginx
    Nginx -->|/api/v1 Reverse Proxy| FastAPI
    FastAPI --> Auth
    FastAPI --> Ingest
    FastAPI --> Retriever
    FastAPI --> Planner
    FastAPI -->|Enqueue Jobs| Postgres
    Worker -->|Claim Jobs| Postgres
    Worker --> Orchestrator
    Orchestrator --> Retriever
    Orchestrator --> Verifier
    Ingest --> DocStore
    Ingest --> Postgres
    Retriever --> Postgres
```

---

## 7. Agentic AI Workflow

```mermaid
stateDiagram-v2
    [*] --> Submitted: Research Question & Selected Papers
    Submitted --> Planning: AI Planner Decomposes Question
    Planning --> AwaitingApproval: Structured Plan Generated
    AwaitingApproval --> Queued: User Reviews & Approves Plan
    AwaitingApproval --> Planning: User Refines Parameters
    Queued --> Retrieving: Background Worker Claims Run
    Retrieving --> Analysing: Hybrid Search Gathers Evidence
    Analysing --> Comparing: Paper Objectives, Methods & Metrics
    Comparing --> Synthesising: Cross-Paper Agreements & Gaps
    Synthesising --> Verifying: Full Text & Page Bounds Check
    Verifying --> Completed: Provenance Score > 95%
    Completed --> [*]: Publication-Grade Literature Review
```

---

## 8. Database Architecture

ResearchPilot uses PostgreSQL with the `pgvector` extension. Key entities include:

- `users`: Accounts, password hashes (Argon2), active states.
- `refresh_sessions`: Hashed JWT refresh tokens with rotation and revocation.
- `projects`: Workspace collections owned by a specific user.
- `documents`: Uploaded PDF metadata, file size, page counts, SHA-256 hashes, processing status.
- `document_chunks`: Token-bounded chunks, 1-based page start/end, content hashes, dense vector embeddings (`vector(1536)`).
- `processing_jobs`: Worker queue tasks with row-level locking (`status`, `attempts`, `available_at`).
- `research_runs`: Run execution records, question, plan JSON, status, final report JSON & Markdown.
- `research_steps`: Granular step logs for active runs.
- `agent_events`: Observable activity feed events streamed to the UI timeline.
- `report_citations`: Extracted citations linking claim text to verified chunk IDs and document pages.

---

## 9. Project Directory Structure

```text
ResearchPilot-/
├── .github/workflows/ci.yml       # Automated GitHub Actions CI pipeline
├── backend/
│   ├── alembic/                   # Database migration scripts
│   ├── src/researchpilot/
│   │   ├── agents/                # Planner, Orchestrator, Tools, Verifier, Schemas
│   │   ├── api/                   # FastAPI routes (auth, projects, docs, runs, retrieval)
│   │   ├── core/                  # Configuration (Pydantic v2), security (Argon2, JWT)
│   │   ├── db/                    # SQLAlchemy models and session factory
│   │   ├── jobs/                  # Persistent background worker daemon
│   │   ├── repositories/          # Database access repositories
│   │   ├── reports/               # Markdown and HTML/PDF report generators
│   │   └── services/              # AI providers, PDF parser, storage, hybrid retrieval
│   ├── tests/                     # Pytest backend integration test suite
│   ├── Dockerfile                 # Backend container definition
│   ├── entrypoint.sh              # DB connection poll, migration runner, service launcher
│   └── pyproject.toml             # Python dependencies and uv toolchain configuration
├── frontend/
│   ├── src/
│   │   ├── api/                   # API client bindings
│   │   ├── components/            # Layout and navigation components
│   │   ├── context/               # Authentication React context
│   │   ├── pages/                 # Dashboard, Workspace, Plan, Activity, Report, Settings
│   │   └── types/                 # TypeScript interfaces
│   ├── e2e/                       # Playwright browser end-to-end tests
│   ├── nginx.conf                 # Nginx SPA and reverse proxy configuration
│   ├── Dockerfile                 # Frontend multi-stage production build
│   └── package.json               # Node.js dependencies and build scripts
├── real_papers/                   # Genuine academic papers for benchmark verification
├── scripts/
│   └── generate_sample_papers.py  # Synthetic benchmark PDF generator
├── docs/                          # Architecture, audit, and decision records
├── docker-compose.yml             # Full-stack multi-container orchestration
├── .env.example                   # Annotated environment variable template
└── README.md                      # Complete product and setup documentation
```

---

## 10. Required APIs, Accounts, and Environment Variables

### API Inventory

| Integration | Purpose | Required / Optional | Where to Get It | Environment Variable | Default Behavior if Unset |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **OpenAI API** | Live LLM completions and 1536-dim embeddings | **Optional** | [platform.openai.com](https://platform.openai.com/api-keys) | `OPENAI_API_KEY` | Automatically runs in offline mode using deterministic `MockAIProvider`. |
| **PostgreSQL** | Relational data persistence and queue | **Required** | Local installation or Docker | `DATABASE_URL` | Defaults to `postgresql+asyncpg://postgres:postgres@localhost:5432/researchpilot`. |
| **pgvector** | Dense vector similarity search | **Required** | Local Homebrew or Docker | Managed in DB | Enables vector search operations. |

### Complete `.env` Reference

```bash
# Application Mode
APP_ENV=development
APP_NAME=ResearchPilot
DEBUG=true
APP_SECRET_KEY=generate-a-secure-random-secret-key-at-least-32-chars-long

# Networking
PORT=8000
HOST=0.0.0.0
FRONTEND_ORIGIN=http://localhost:5173

# Database & Storage
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/researchpilot
LOCAL_STORAGE_PATH=./storage/documents

# Authentication Tokens
ACCESS_TOKEN_TTL_MINUTES=30
REFRESH_TOKEN_TTL_DAYS=7

# OpenAI API (Optional - leave empty for offline mock mode)
OPENAI_API_KEY=
OPENAI_CHAT_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSIONS=1536

# Processing Limits
MAX_UPLOAD_MB=25
MAX_PDF_PAGES=500
CHUNK_SIZE_TOKENS=800
CHUNK_OVERLAP_TOKENS=120
MAX_TOOL_CALLS_PER_RUN=25
MAX_RETRIEVED_CHUNKS_PER_RUN=40
MAX_RUN_DURATION_SECONDS=300
```

---

## 11. Quick Start: Running the Application

You can run ResearchPilot using either **Docker Compose** (recommended for zero-setup containerized execution) or **Native macOS** (for local development).

### Option A: Docker Compose (Recommended)

Make sure Docker Desktop is running on your Mac, then:

```bash
# 1. Clone the repository
git clone https://github.com/SiddharthaShukla8/ResearchPilot-.git
cd ResearchPilot-

# 2. Configure environment file
cp .env.example .env

# 3. Build and launch all 4 services
docker-compose up --build
```

The services will start in dependency order:
- `researchpilot-db`: PostgreSQL 16 with pgvector on port `5432`.
- `researchpilot-api`: FastAPI backend running migrations on port `8000`.
- `researchpilot-worker`: Background worker listening for jobs.
- `researchpilot-frontend`: React application with Nginx on port `5173`.

Access the application in your browser at: **`http://localhost:5173`**

---

### Option B: Native macOS Development (Without Docker)

#### Step 1: Install System Prerequisites
Using Homebrew:
```bash
brew install postgresql@18 pgvector node uv
```

#### Step 2: Configure PostgreSQL & pgvector
```bash
# Start PostgreSQL service
brew services start postgresql@18

# Create postgres user and researchpilot database (if not already existing)
psql -d postgres -c "CREATE USER postgres WITH SUPERUSER PASSWORD 'postgres';"
psql -d postgres -c "CREATE DATABASE researchpilot OWNER postgres;"

# Enable pgvector extension
psql -U postgres -d researchpilot -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

#### Step 3: Run Database Migrations
```bash
cd backend
cp ../.env.example .env
uv venv
uv pip install -e ".[dev]" greenlet "email-validator>=2.0.0"
PYTHONPATH=src uv run alembic upgrade head
```

#### Step 4: Start All Services in Separate Terminals

**Terminal 1 — Backend API Server:**
```bash
cd backend
PYTHONPATH=src uv run uvicorn researchpilot.main:app --host 0.0.0.0 --port 8000 --reload
```
*Backend health check:* `curl http://localhost:8000/health/live`  
*Interactive Swagger docs:* `http://localhost:8000/docs`

**Terminal 2 — Background Job Worker:**
```bash
cd backend
PYTHONPATH=src uv run python -m researchpilot.jobs.worker
```
*The worker will log:* `Worker worker-X-XXXXXX started and listening for jobs...`

**Terminal 3 — Frontend Development Server:**
```bash
cd frontend
npm install
npm run dev
```
*Access the UI at:* `http://localhost:5173`

---

## 12. Complete Research Workflow Guide

1. **Register & Sign In:** Navigate to `http://localhost:5173` and create your account.
2. **Create a Research Workspace:** Click *"New Project"*, provide a title (e.g. *"Brain Tumor MRI Segmentation Review"*), and enter the project dashboard.
3. **Upload Academic Papers:** Drag and drop your research PDFs into the upload dropzone. The background worker parses the documents, extracts text and metadata, partitions them into token-bounded chunks, and indexes embeddings in `pgvector`. Wait until all papers display the green `Ready` badge.
4. **Formulate Research Question:** Click *"Start Research Run"*, enter your query (e.g. *"Compare CNN architectures with Vision Transformers for brain tumor segmentation in terms of Dice scores"*), select your papers, and click *"Generate Research Plan"*.
5. **Inspect & Approve Plan:** Review the AI-generated sub-questions and methodology steps. Modify or refine parameters if desired, then click *"Approve & Run"*.
6. **Monitor Live Execution:** The Activity Timeline dynamically logs tool executions (`search_paper_library`, `analyze_paper`, `compare_findings`, `detect_gaps`).
7. **Explore the Literature Review:** Once completed, explore the 4-tab synthesized report:
   - *Thematic Review & Scope*
   - *Methodology Comparison Matrix*
   - *Agreements & Variations*
   - *Candidate Research Gaps*
8. **Verify Citation Provenance:** Click any interactive citation badge (`[1]`, `[2]`) to view the exact excerpt, source document, and verified 1-based page number.
9. **Export Report:** Click *"Copy Markdown"* to grab the formatted text or *"Export PDF"* to generate a publication-ready document.

---

## 13. Testing Instructions

### Run Backend Test Suite
```bash
cd backend
uv run pytest -v
uv run ruff check src
```
*Expected output: `10 passed`, `All checks passed!`*

### Run Frontend Unit Tests
```bash
cd frontend
npm test
npm run build
```
*Expected output: `1 passed`, TypeScript compilation and Vite build with 0 errors.*

### Run Playwright Browser End-to-End Tests
Ensure the application is running at `http://localhost:5173`, then:
```bash
cd frontend
npx playwright test
```
*Validates the entire end-to-end journey in an automated browser.*

---

## 14. Troubleshooting

- **Database Connection Error (`connection refused on port 5432`):**  
  Ensure PostgreSQL is running: `brew services list` or `docker ps`. Verify `DATABASE_URL` in `.env`.
- **Extension Vector Not Found (`extension "vector" is not available`):**  
  Install pgvector: `brew install pgvector` (Mac) or ensure you are using image `pgvector/pgvector:pg16` in Docker.
- **Worker Not Processing Jobs:**  
  Verify the background worker process is running in Terminal 2 or via Docker (`docker logs researchpilot-worker`). Ensure `DATABASE_URL` matches the API server.
- **Port 5173 or 8000 Already in Use:**  
  Find the active process using `lsof -i :8000 -i :5173` and terminate it, or update `PORT` in `.env` and `vite.config.ts`.

---

## 15. Security & Isolation

- **Zero Data Hallucination:** Only user-uploaded papers are indexed; no external web searches or unverified claims are invented.
- **Multi-Tenant Ownership:** Every database query enforces strict owner ID checking. Users cannot view, modify, or search documents or projects belonging to other accounts.
- **Path Traversal Protection:** Document keys are generated as random UUIDs and stored privately; original filenames are sanitized.
- **Credential Safety:** Secrets are never hardcoded or exposed in frontend bundles; token hashes use Argon2 and SHA-256.

---

## 16. Author and Repository

- **Repository:** [https://github.com/SiddharthaShukla8/ResearchPilot-](https://github.com/SiddharthaShukla8/ResearchPilot-)
- **Author:** Siddhartha Shukla
