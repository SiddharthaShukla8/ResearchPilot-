# Agent Workflow & Hallucination Controls — ResearchPilot

## 1. Research Run State Machine

```
[queued] ──> [planning] ──> [awaiting_approval]
                                   │
                                   ├──> [cancelled]
                                   │
                              (Approved)
                                   ▼
[retrieving] ──> [analysing] ──> [synthesising] ──> [verifying] ──> [completed]
                                                          │
                                                          └──> [failed]
```

## 2. Hallucination Control Protocols

1. **Untrusted Evidence Boundary:** All text extracted from uploaded PDFs is treated as untrusted data. Document text cannot override system prompts or grant additional tool privileges.
2. **Deterministic Provenance Verification:**
   - Every citation must map to an existing `document_id` in the approved user corpus.
   - The cited chunk must physically exist in the database.
   - The cited page number must fall within the chunk's `page_start` and `page_end`.
   - The cited excerpt must match actual text extracted from that document chunk.
3. **No Hallucinated Metadata:** If publication year, DOI, or authors are not extracted from the PDF, they remain `Unknown` / `None`.
4. **Comparability Labeling:** The agent does not declare unilateral model superiority across non-comparable datasets. Rows are explicitly labeled as `directly_comparable`, `partially_comparable`, or `not_directly_comparable`.
5. **Corpus Scoped Gaps:** Candidate research gaps are explicitly tagged as observed within the uploaded papers only, avoiding false claims regarding the entirety of human knowledge.
