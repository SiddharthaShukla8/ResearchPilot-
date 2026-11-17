"""Pydantic schemas for Document upload and management."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DocumentResponse(BaseModel):
    """Document metadata and status representation."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    owner_id: str
    original_filename: str
    sha256: str
    file_size: int
    page_count: int
    title: str | None
    authors: list[str] | dict | None
    publication_year: int | None
    doi: str | None
    processing_status: str
    processing_error: str | None
    created_at: datetime
    processed_at: datetime | None


class DocumentUploadBatchResponse(BaseModel):
    """Result summary of a multi-file upload."""
    uploaded: list[DocumentResponse]
    duplicates: list[str]
    failed: list[dict[str, str]]
