"""Pydantic schemas for Evidence Retrieval endpoints."""
from pydantic import BaseModel


class EvidenceResponse(BaseModel):
    """Retrieved evidence passage representation."""
    document_id: str
    chunk_id: str
    document_title: str
    page_start: int
    page_end: int
    text: str
    token_count: int
    score: float
    retrieval_method: str


class EvidenceQueryRequest(BaseModel):
    """Payload to search literature evidence."""
    query: str
    selected_document_ids: list[str]
    limit: int = 10
