# LOCAL_SETUP_AUDIT.md — ResearchPilot Environment & Dependency Audit

**Audit Date:** November 20, 2026  
**Auditor:** Senior Full-Stack & Systems Validation Engineer  
**Repository:** `https://github.com/SiddharthaShukla8/ResearchPilot-`  
**Target Environment:** macOS (Darwin arm64) & Docker Compose  
**System Status:** **VERIFIED GREEN / RELEASE-READY**

---

## 1. Current Architecture Overview

ResearchPilot is an Agentic AI Research and Literature Review Assistant built with a clean separation of concerns:

- **Frontend (Client UI):** Single Page Application written in React 18, TypeScript, Tailwind CSS, Lucide icons, and React Router v6. Built via Vite.
  - Development Server: `vite` on port `5173`.
  - Production Container: Nginx reverse proxy on port `80` (mapped to host `5173`) routing `/api/`, `/health/`, `/system/`, `/docs` to the FastAPI backend while serving SPA routing via `try_files $uri $uri/ /index.html;`.
- **Backend (API Service):** Asynchronous ASGI REST API built with FastAPI and Pydantic v2.
  - Server: `uvicorn` on port `8000`.
  - Authentication: Argon2 password hashing, HS256 JWT access tokens (30 min TTL), and rotating SHA-256 hashed refresh tokens (7 day TTL).
  - Storage: Local filesystem private storage abstraction (`LocalFileStorage`) with path-traversal sanitization and SHA-256 content deduplication.
  - Endpoints: Multi-tenant ownership isolation enforced across projects, documents, runs, events, and citations.
- **Database & Vector Store:**
  - PostgreSQL 16/18 with `pgvector` extension enabled (`CREATE EXTENSION IF NOT EXISTS vector;`).
  - ORM: SQLAlchemy 2.0 with `asyncpg` async dialect.
  - Migrations: Alembic transactional migrations (`alembic upgrade head`).
  - Search: Hybrid Dense Vector Cosine Similarity (`vector <=> embedding`) + Lexical Full-Text Search (`to_tsvector` / `websearch_to_tsquery`) fused via Reciprocal Rank Fusion (RRF, $k=60$).
- **Background Worker:**
  - Asynchronous persistent polling daemon (`BackgroundWorker`) utilizing PostgreSQL row-level locks (`SELECT ... FOR UPDATE SKIP LOCKED`) via table `processing_jobs`.
  - Executes document extraction & chunking (`ingest_document`) and multi-step agent research pipelines (`execute_research`).
- **Agent Orchestrator & Citation Verification:**
  - Multi-state research engine (`queued` &rarr; `retrieving` &rarr; `analysing` &rarr; `synthesising` &rarr; `verifying` &rarr; `completed`).
  - Allowlisted tool registry (`search_paper_library`, `get_document_metadata`, `retrieve_page_context`, `search_exact_terms`) with ownership constraints.
  - Deterministic citation verification (`CitationVerifier`) ensuring every claim links to verified document IDs, 1-based page bounds, and chunk hashes.

---

## 2. Environment Toolchain Status (Local Mac)

| Tool / Runtime | Installed Version | Status | Location |
| :--- | :--- | :--- | :--- |
| **macOS** | Darwin 25.2.0 (Apple Silicon arm64) | Active | Host |
| **Python** | 3.13.2 (system) / 3.14.4 (uv managed venv) | Installed & Verified | `/opt/homebrew/bin/python3`, `/Users/siddhartha/.local/share/uv/python` |
| **uv** | 0.11.8 | Installed & Verified | `/Users/siddhartha/.local/bin/uv` |
| **Node.js** | v22.23.4 (via nvm) | Installed & Verified | `/Users/siddhartha/.nvm/versions/node/v22.23.4/bin/node` |
| **npm** | 10.9.9 | Installed & Verified | `/Users/siddhartha/.nvm/versions/node/v22.23.4/bin/npm` |
| **PostgreSQL** | 18.3 (Homebrew) & 16.8 (Docker) | Installed & Running | `/opt/homebrew/opt/postgresql@18/bin/psql`, port 5432 |
| **pgvector** | 0.8.7 (Homebrew & Docker pg16) | Installed & Active | Both local PostgreSQL 18 and Docker container |
| **Docker** | 29.9.3 (Desktop Linux context) | Installed & Running | `/usr/local/bin/docker`, Docker Desktop |
| **Docker Compose** | Compose v2 | Installed & Running | `/usr/local/bin/docker-compose` |
| **Git** | 2.50.1 (Apple Git-155) | Clean on `main` | `/usr/bin/git` |

---

## 3. Complete Required APIs & External Services Inventory

| Integration | Purpose | Required / Optional | Where to Obtain | Environment Variable | Default Behavior if Unset |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **OpenAI API** | Live LLM completions (gpt-4o-mini) and high-dimensional dense embeddings (text-embedding-3-small, 1536-dim) | **Optional** (Application runs completely in offline mock mode without it) | [platform.openai.com/api-keys](https://platform.openai.com/api-keys) | `OPENAI_API_KEY` | Automatically falls back to deterministic `MockAIProvider`. Diagnostic endpoint `/system/capabilities` reports `provider_mode: "offline_mock"`. |
| **PostgreSQL** | Relational data persistence (users, projects, documents, jobs, runs, events) | **Required** | Local Homebrew (`brew install postgresql@18`) or Docker Compose | `DATABASE_URL` | Defaults to `postgresql+asyncpg://postgres:postgres@localhost:5432/researchpilot`. |
| **pgvector** | Dense vector similarity indexing & embeddings search | **Required** | Homebrew (`brew install pgvector`) or Docker image `pgvector/pgvector:pg16` | Included in PostgreSQL | Required for hybrid dense vector cosine similarity search. |
| **Local Filesystem** | Secure storage for uploaded research PDFs | **Required** | Built-in (Local directory on host disk) | `LOCAL_STORAGE_PATH` | Defaults to `./storage/documents` relative to backend root. |
| **Redis / Celery** | Distributed queue | **Not Needed** | N/A | None | Native PostgreSQL row-level locking (`FOR UPDATE SKIP LOCKED`) is used instead of Redis. |
| **External Paper APIs** | Real-time web paper discovery | **Not Needed** | Initial release is user-uploaded PDFs only | None | Preserves strict source-of-truth grounding without web hallucination. |

---

## 4. Known Issues Remediated

1. **Docker Frontend Port Mapping & SPA Routing:**
   - *Problem:* Container ran Nginx on internal port 80, but Compose mapped 5173:5173. Browser refreshes threw 404s.
   - *Resolution:* Added `frontend/nginx.conf` with reverse proxy (`/api/` &rarr; `http://api:8000`) and SPA fallback (`try_files $uri $uri/ /index.html;`). Mapped host port 5173 to container port 80.
2. **Database Readiness in Startup Scripts:**
   - *Problem:* Backend API and Worker containers could start before PostgreSQL accepted connections.
   - *Resolution:* Added an `asyncpg` connection polling loop in `backend/entrypoint.sh` executing `alembic upgrade head` synchronously before launching uvicorn.
3. **Null-Byte Characters in Complex Academic PDFs:**
   - *Problem:* Academic typography in papers like `zhou2018_unetplusplus.pdf` caused `CharacterNotInRepertoireError (0x00)` during bulk PostgreSQL insertion.
   - *Resolution:* Added text stream null-byte sanitization (`text.replace('\x00', '')`) in `PDFParser.extract_pages`.
4. **Token Propagation on Direct Browser Exports:**
   - *Problem:* Opening PDF / Markdown export in a new browser tab (`window.open`) did not pass Bearer auth headers.
   - *Resolution:* Added `token_query` fallback query parameter handling to `get_current_user` in `backend/src/researchpilot/api/deps.py` and updated `ReportViewerPage.tsx`.

---

## 5. Verification Checklist

- [x] Docker stack healthy (`researchpilot-db`, `researchpilot-api`, `researchpilot-worker`, `researchpilot-frontend`).
- [x] Native macOS stack verified (`PostgreSQL 18` + `pgvector 0.8.7`, `uv run uvicorn`, `uv run python -m researchpilot.jobs.worker`, `npm run dev`).
- [x] Backend unit & integration test suite (10/10 tests passed).
- [x] Frontend test suite (Vitest passed).
- [x] TypeScript compilation and Vite production build clean.
- [x] Full Playwright E2E browser journey verified end-to-end (Register &rarr; Workspace &rarr; Ingestion &rarr; Plan &rarr; Approval &rarr; Worker Execution &rarr; Verified Report &rarr; Provenance Inspection &rarr; Persistence).
