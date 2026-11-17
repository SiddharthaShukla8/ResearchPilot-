# Data Model Documentation — ResearchPilot

All primary keys use UUID strings (36 characters). All timestamps are stored in UTC with timezone awareness.

## Tables & Schemas

### 1. `users`
- `id` (PK, String 36)
- `name` (String 100)
- `email` (String 255, Unique Index)
- `password_hash` (String 255, Argon2 hash)
- `is_active` (Boolean)
- `created_at`, `updated_at` (DateTime UTC)

### 2. `refresh_sessions`
- `id` (PK, String 36)
- `user_id` (FK -> users.id, Cascade Delete)
- `hashed_refresh_token` (String 255, Unique Index)
- `expires_at` (DateTime UTC)
- `revoked_at` (DateTime UTC, Nullable)
- `created_at` (DateTime UTC)

### 3. `projects`
- `id` (PK, String 36)
- `owner_id` (FK -> users.id, Cascade Delete, Index)
- `title` (String 255)
- `description` (Text, Nullable)
- `created_at`, `updated_at` (DateTime UTC)

### 4. `documents`
- `id` (PK, String 36)
- `project_id` (FK -> projects.id, Cascade Delete, Index)
- `owner_id` (FK -> users.id, Cascade Delete, Index)
- `original_filename` (String 255)
- `private_storage_key` (String 255, Unique)
- `sha256` (String 64, Index)
- `mime_type` (String 100)
- `file_size` (BigInteger)
- `page_count` (Integer)
- `title` (String 500, Nullable)
- `authors` (JSONB, Nullable)
- `publication_year` (Integer, Nullable)
- `doi` (String 255, Nullable)
- `processing_status` (String 50: `uploaded`, `extracting`, `chunking`, `embedding`, `indexing`, `ready`, `failed`)
- `processing_error` (Text, Nullable)
- `created_at`, `processed_at` (DateTime UTC)

### 5. `document_chunks`
- `id` (PK, String 36)
- `document_id` (FK -> documents.id, Cascade Delete, Index)
- `owner_id` (FK -> users.id, Cascade Delete, Index)
- `chunk_index` (Integer)
- `page_start` (Integer, 1-based)
- `page_end` (Integer, 1-based)
- `text` (Text)
- `token_count` (Integer)
- `content_hash` (String 64)
- `embedding` (Vector 1536, Nullable)
- `tsv` (TSVECTOR, Nullable)
- `created_at` (DateTime UTC)

### 6. `processing_jobs`
- `id` (PK, String 36)
- `owner_id` (FK -> users.id, Index)
- `project_id` (FK -> projects.id, Nullable)
- `target_id` (String 36, Index)
- `job_type` (String 50: `ingest_document`, `execute_research`)
- `status` (String 50: `queued`, `processing`, `completed`, `failed`, `cancelled`)
- `attempts`, `max_attempts` (Integer)
- `available_at` (DateTime UTC)
- `locked_at`, `locked_by`, `heartbeat_at` (DateTime UTC)
- `last_error` (Text, Nullable)
- `created_at`, `updated_at` (DateTime UTC)

### 7. `research_runs`
- `id` (PK, String 36)
- `project_id` (FK -> projects.id, Cascade Delete, Index)
- `owner_id` (FK -> users.id, Cascade Delete, Index)
- `research_question` (Text)
- `selected_document_ids` (JSONB)
- `citation_style` (String 50)
- `status` (String 50: `queued`, `planning`, `awaiting_approval`, `retrieving`, `analysing`, `synthesising`, `verifying`, `completed`, `failed`, `cancelled`)
- `plan_json` (JSONB, Nullable)
- `report_json` (JSONB, Nullable)
- `report_markdown` (Text, Nullable)
- `error_code`, `error_message` (Nullable)
- `started_at`, `completed_at`, `created_at`, `updated_at` (DateTime UTC)

### 8. `agent_events`
- `id` (PK, String 36)
- `run_id` (FK -> research_runs.id, Cascade Delete, Index)
- `sequence` (Integer)
- `event_type` (String 50)
- `safe_summary` (Text)
- `metadata_json` (JSONB, Nullable)
- `created_at` (DateTime UTC)

### 9. `report_citations`
- `id` (PK, String 36)
- `run_id` (FK -> research_runs.id, Cascade Delete, Index)
- `citation_key` (String 50, e.g. `[1]`)
- `document_id` (FK -> documents.id, Cascade Delete, Index)
- `chunk_id` (FK -> document_chunks.id, Set Null)
- `page_number` (Integer, 1-based)
- `exact_excerpt` (Text)
- `source_metadata_json` (JSONB, Nullable)
- `verification_status` (String 50)
