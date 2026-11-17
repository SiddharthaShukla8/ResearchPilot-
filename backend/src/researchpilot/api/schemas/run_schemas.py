"""Pydantic schemas for Research Run endpoints."""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ResearchRunCreateRequest(BaseModel):
    """Payload to initiate a research run."""
    research_question: str = Field(min_length=5, max_length=2000)
    selected_document_ids: list[str] = Field(min_length=1)
    citation_style: str = "numbered"
    user_instructions: str | None = None
    quick_run: bool = False  # Auto-approve plan if true


class ResearchPlanUpdateRequest(BaseModel):
    """Payload to update an editable plan before approval."""
    objective: str
    sub_questions: list[str]
    steps: list[dict[str, Any]]


class ResearchRunResponse(BaseModel):
    """Research run state and report summary."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    owner_id: str
    research_question: str
    selected_document_ids: list[str]
    citation_style: str
    status: str
    plan_json: dict[str, Any] | None
    report_json: dict[str, Any] | None
    error_code: str | None
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class AgentEventResponse(BaseModel):
    """Event representation in the timeline."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    run_id: str
    sequence: int
    event_type: str
    safe_summary: str
    metadata_json: dict[str, Any] | None
    created_at: datetime
