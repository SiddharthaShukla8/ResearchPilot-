"""Pydantic schemas for Project endpoints."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ProjectCreateRequest(BaseModel):
    """Payload to create a new research project."""
    title: str = Field(min_length=2, max_length=255)
    description: str | None = Field(default=None, max_length=2000)


class ProjectUpdateRequest(BaseModel):
    """Payload to update an existing research project."""
    title: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = Field(default=None, max_length=2000)


class ProjectResponse(BaseModel):
    """Project representation response."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    owner_id: str
    title: str
    description: str | None
    created_at: datetime
    updated_at: datetime
    document_count: int = 0
