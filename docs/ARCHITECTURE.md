# Architecture Documentation — ResearchPilot

## 1. System Overview

ResearchPilot is an Agentic AI Literature Review Assistant designed for researchers and university students. The application operates as a modular monolith with a decoupled background worker process and row-level job claiming over PostgreSQL.

```
┌────────────────────────────────────────────────────────┐
│                   React 18 Frontend                    │
│   (Vite + TypeScript + Tailwind CSS + Lucide Icons)    │
└───────────────────────────┬────────────────────────────┘
                            │ REST / JSON (HTTP)
┌───────────────────────────▼────────────────────────────┐
│                  FastAPI Application                   │
│  - /auth (Argon2, Access/Rotating Refresh JWT)         │
│  - /projects (CRUD, User-scoped Isolation)             │
│  - /documents (MIME, Magic Bytes, PyMuPDF)             │
│  - /retrieval (Hybrid Cosine Dense + tsvector BM25)    │
│  - /research-runs (Plan Review, Orchestrator, Reports) │
└─────────────┬────────────────────────────┬─────────────┘
              │                            │
              ▼                            ▼
┌──────────────────────────┐  ┌──────────────────────────┐
│  PostgreSQL 16+ / SQLite │  │  Private File Storage    │
│  - pgvector embeddings   │  │  (Local storage adapter  │
│  - tsvector full-text    │  │   with path-traversal    │
│  - processing_jobs queue │  │   protection)            │
└─────────────▲────────────┘  └──────────────────────────┘
              │ FOR UPDATE SKIP LOCKED
┌─────────────┴────────────────────────────┐
│         Background Worker Daemon         │
│  - Document Ingestion Pipeline           │
│  - Research Agent Orchestrator           │
│  - Deterministic Citation Verifier       │
└──────────────────────────────────────────┘
```

## 2. Core Modules & Responsibilities

1. **`core/`**: Centralized configuration management using Pydantic v2 settings, Argon2 password hashing, and signed JWT token handling.
2. **`db/`**: SQLAlchemy 2 async models and Alembic database migrations.
3. **`repositories/`**: Data access layer enforcing ownership boundaries across all queries.
4. **`services/pdf_parser.py`**: PyMuPDF extraction preserving 1-based page coordinates, text sanitization, and token-aware overlapping chunking.
5. **`services/retrieval.py`**: Reciprocal Rank Fusion (RRF) combining dense vector cosine similarity and full-text keyword search.
6. **`agents/planner.py`**: Decomposes user research queries into verifiable sub-questions, execution steps, and comparison matrices.
7. **`agents/tools.py`**: Allowlisted, sandboxed research tools constrained to user-selected papers.
8. **`agents/orchestrator.py`**: Finite-state-machine executing retrieval, paper analysis, cross-paper comparison, and synthesis.
9. **`agents/verifier.py`**: Deterministic citation provenance verifier validating chunk existence, page bounds, and exact excerpts.
