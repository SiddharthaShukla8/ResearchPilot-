# Decisions Log — ResearchPilot

## ADR 001: Modular Monolith with Decoupled Background Worker
- **Context:** The application requires asynchronous document extraction/chunking/embedding and multi-step research agent execution.
- **Decision:** Implement a clean modular monolith backend using FastAPI, with a standalone background worker sharing the same database and core models.
- **Rationale:** Simpler to maintain and deploy than microservices while maintaining strict code boundaries and preventing blocking of HTTP endpoints during heavy AI/PDF workloads.

## ADR 002: PostgreSQL Row-Level Job Queue (SKIP LOCKED) vs Celery/Redis
- **Context:** Need persistent, idempotent document and research processing jobs with recovery, retries, and cancellation.
- **Decision:** Use a PostgreSQL-backed `processing_jobs` table utilizing `SELECT ... FOR UPDATE SKIP LOCKED`.
- **Rationale:** Avoids extra infrastructure dependencies (Redis/RabbitMQ/Celery) while delivering transactional guarantees, crash recovery, worker heartbeats, and zero external broker sync issues.

## ADR 003: Hybrid Retrieval with pgvector and PostgreSQL Full-Text Search (RRF)
- **Context:** Academic literature contains both technical jargon, acronyms, author names, and broad conceptual claims.
- **Decision:** Combine pgvector cosine distance dense retrieval with PostgreSQL `tsvector` keyword search using Reciprocal Rank Fusion (RRF).
- **Rationale:** Ensures exact term matches (e.g. "ResNet-50", "AUC 0.94") are retrieved alongside semantically similar passages.

## ADR 004: Strict Citation Grounding and Hallucination Control
- **Context:** Academic reviews require rigorous provenance. Fabricated citations and claims destroy credibility.
- **Decision:** Require all synthesized claims to link to valid document chunks and 1-based page numbers. Implement a deterministic verification pipeline that validates excerpt presence in stored chunks, rejects unknown references, and flags unsupported claims.

## ADR 005: AI Provider Abstraction with Configurable Models
- **Context:** OpenAI API models can evolve; local mock/testing must be deterministic without network or secret leaks.
- **Decision:** Abstract LLM and Embedding calls behind a provider interface (`services/ai/`), reading model parameters and credentials from validated Pydantic settings. Include a deterministic test double provider for integration/E2E testing.
