# Testing Strategy & Verification — ResearchPilot

## Test Suites

### 1. Backend Test Suite (`pytest`)
- `tests/test_health.py`: Liveness, readiness, and system capability disclosure safety.
- `tests/test_auth_and_projects.py`: Registration, duplicate rejection, login, token refresh rotation, and project ownership isolation.
- `tests/test_documents.py`: PDF validation, magic bytes, page limits, upload deduplication, download authorization, and deletion cascade.
- `tests/test_retrieval.py`: Dense vector similarity, keyword matching, Reciprocal Rank Fusion, token budget packing, and cross-user isolation.
- `tests/test_agent_orchestration.py`: Planner prompt & schema validation, plan editing & approval, pipeline execution, and deterministic citation verification.

### 2. Frontend Test Suite (`vitest`)
- `frontend/src/App.test.ts`: Client-side rendering and environment verification.

### 3. Execution Commands
```bash
# Run backend tests
cd backend && uv run pytest

# Run linter
cd backend && uv run ruff check src

# Run frontend tests
cd frontend && npm test

# Run frontend build
cd frontend && npm run build
```
