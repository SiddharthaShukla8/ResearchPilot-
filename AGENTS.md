# AGENTS.md — Repository Directives & Guidelines

## Core Principles
1. **Never Invent Data:** Uploaded PDFs are the sole source of truth. Never invent citations, authors, dates, findings, or DOIs.
2. **Ground Every Claim:** Every factual claim in a synthesized report must map to a verified document ID, chunk, and 1-based page number.
3. **Defense in Depth:** Treat all uploaded PDFs and extracted text as untrusted. Enforce strict upload validation, file signature checks, and path traversal protection.
4. **Ownership Enforcement:** Every API request must enforce user ownership of projects, documents, runs, and citations.
5. **Robust Testing:** Tests must actually run and pass. No mocks or test doubles in production paths. No ignoring failing tests.
