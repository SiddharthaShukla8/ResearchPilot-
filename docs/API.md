# API Specification — ResearchPilot

Base Path: `/api/v1`

## 1. Authentication
- `POST /api/v1/auth/register` — Register user account, returns access + refresh JWTs.
- `POST /api/v1/auth/login` — Authenticate email/password.
- `POST /api/v1/auth/refresh` — Rotate and issue fresh tokens.
- `POST /api/v1/auth/logout` — Revoke active refresh session.
- `GET /api/v1/auth/me` — Authenticated profile endpoint.

## 2. Projects
- `GET /api/v1/projects` — List user's research projects.
- `POST /api/v1/projects` — Create workspace project.
- `GET /api/v1/projects/{project_id}` — Retrieve project details with document counts.
- `PATCH /api/v1/projects/{project_id}` — Update title/description.
- `DELETE /api/v1/projects/{project_id}` — Delete project and cascade documents/runs.

## 3. Documents
- `GET /api/v1/projects/{project_id}/documents` — List documents in project.
- `POST /api/v1/projects/{project_id}/documents` — Multipart file upload with validation.
- `GET /api/v1/documents/{document_id}` — Get document metadata & extraction state.
- `GET /api/v1/documents/{document_id}/download` — Download original PDF (authenticated).
- `DELETE /api/v1/documents/{document_id}` — Delete document and delete chunks/storage file.

## 4. Retrieval & Evidence
- `POST /api/v1/retrieval/search` — Execute hybrid vector + keyword search over selected corpus.
- `GET /api/v1/retrieval/evidence/chunk/{chunk_id}` — Get full chunk text and page context.

## 5. Research Runs & Agent Orchestrator
- `POST /api/v1/projects/{project_id}/research-runs` — Create run and generate initial plan.
- `GET /api/v1/research-runs/{run_id}` — Get run status and report.
- `PATCH /api/v1/research-runs/{run_id}/plan` — Edit plan before approval.
- `POST /api/v1/research-runs/{run_id}/approve` — Approve plan and start agent.
- `POST /api/v1/research-runs/{run_id}/cancel` — Cancel active run.
- `GET /api/v1/research-runs/{run_id}/events` — Retrieve activity timeline events.
- `GET /api/v1/research-runs/{run_id}/report` — Retrieve final report JSON & Markdown.
- `GET /api/v1/research-runs/{run_id}/export?format=markdown|pdf` — Export review report.

## 6. System Probes
- `GET /health/live` — Liveness probe (`{"status": "ok"}`).
- `GET /health/ready` — Readiness probe (checks storage and env).
- `GET /system/capabilities` — Reports AI model configuration without leaking keys.
