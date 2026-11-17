# Security Architecture & Data Protection — ResearchPilot

## 1. Authentication & Session Security
- **Argon2 Password Hashing:** Plaintext passwords are never stored. Passwords are hashed using the Argon2id scheme with memory-hard parameters.
- **Short-Lived Access Tokens:** Signed HS256 JWT access tokens expire in 30 minutes.
- **Rotating Refresh Tokens:** Refresh tokens contain unique `jti` anti-replay identifiers, are hashed with SHA-256 before storage in `refresh_sessions`, and are revoked upon rotation or logout.

## 2. Authorization & Tenant Isolation
- **Ownership Verification:** Every database query joins against `owner_id == current_user.id`.
- **404 Denial:** Requests for unauthorized projects, documents, or runs return `404 Not Found` rather than `403 Forbidden` to prevent object existence enumeration.

## 3. PDF Ingestion Security
- **File Signature Inspection:** Enforces `%PDF-` magic byte headers; browser MIME types are never trusted.
- **Size & Page Limits:** Default 25 MB file size and 500-page thresholds prevent memory denial of service.
- **Path Traversal Protection:** Internal storage names use random UUID strings (`<uuid>.pdf`). Original filenames are retained purely as display metadata.
- **Scanned PDF Detection:** Rejects image-only PDFs lacking embedded text to avoid empty chunk indexing.

## 4. Operational Boundaries
- **No Internet Access for Tools:** Agent tools are strictly allowlisted and execute locally against the user's uploaded vector index.
- **No Arbitrary Code Execution:** The LLM cannot execute shell scripts or arbitrary Python.
- **Redaction of Secrets:** API keys and sensitive credentials are never reflected in logs or API payloads.
