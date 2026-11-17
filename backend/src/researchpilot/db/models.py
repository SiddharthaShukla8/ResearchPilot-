"""SQLAlchemy 2 database models for ResearchPilot."""
import uuid
from datetime import UTC, datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from researchpilot.db.session import Base


def utcnow() -> datetime:
    """Return current timestamp in UTC timezone."""
    return datetime.now(UTC)


class User(Base):
    """Registered user entity."""
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )

    projects: Mapped[list["Project"]] = relationship("Project", back_populates="owner", cascade="all, delete-orphan")
    refresh_sessions: Mapped[list["RefreshSession"]] = relationship("RefreshSession", back_populates="user", cascade="all, delete-orphan")


class RefreshSession(Base):
    """User refresh token tracking session."""
    __tablename__ = "refresh_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    hashed_refresh_token: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="refresh_sessions")


class Project(Base):
    """Research project/workspace owned by a user."""
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )

    owner: Mapped["User"] = relationship("User", back_populates="projects")
    documents: Mapped[list["Document"]] = relationship("Document", back_populates="project", cascade="all, delete-orphan")
    research_runs: Mapped[list["ResearchRun"]] = relationship("ResearchRun", back_populates="project", cascade="all, delete-orphan")


class Document(Base):
    """Uploaded PDF document metadata and ingestion status."""
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    owner_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    private_storage_key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    mime_type: Mapped[str] = mapped_column(String(100), default="application/pdf", nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    page_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    authors: Mapped[list | dict | None] = mapped_column(JSONB, nullable=True)
    publication_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    doi: Mapped[str | None] = mapped_column(String(255), nullable=True)
    processing_status: Mapped[str] = mapped_column(String(50), default="uploaded", nullable=False, index=True)
    processing_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    project: Mapped["Project"] = relationship("Project", back_populates="documents")
    chunks: Mapped[list["DocumentChunk"]] = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_doc_project_sha256", "project_id", "sha256"),
    )


class DocumentChunk(Base):
    """Page-aware indexed chunk of text from an uploaded document."""
    __tablename__ = "document_chunks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id: Mapped[str] = mapped_column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    owner_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    page_start: Mapped[int] = mapped_column(Integer, nullable=False)
    page_end: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int] = mapped_column(Integer, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536), nullable=True)
    tsv: Mapped[str | None] = mapped_column(TSVECTOR, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    document: Mapped["Document"] = relationship("Document", back_populates="chunks")

    __table_args__ = (
        Index("idx_chunk_doc_index", "document_id", "chunk_index"),
    )


class ProcessingJob(Base):
    """Persistent background job for PDF ingestion or research agent execution."""
    __tablename__ = "processing_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=True, index=True)
    target_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)  # document_id or run_id
    job_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # ingest_document, execute_research
    status: Mapped[str] = mapped_column(String(50), default="queued", nullable=False, index=True)  # queued, processing, completed, failed, cancelled
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    available_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    locked_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    __table_args__ = (
        Index("idx_jobs_claim", "status", "available_at", "attempts"),
    )


class ResearchRun(Base):
    """Research run entity tracking a user's question, plan, and synthesis report."""
    __tablename__ = "research_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    owner_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    research_question: Mapped[str] = mapped_column(Text, nullable=False)
    selected_document_ids: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    citation_style: Mapped[str] = mapped_column(String(50), default="numbered", nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="queued", nullable=False, index=True)
    plan_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    report_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    report_markdown: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    project: Mapped["Project"] = relationship("Project", back_populates="research_runs")
    steps: Mapped[list["ResearchStep"]] = relationship("ResearchStep", back_populates="run", cascade="all, delete-orphan")
    events: Mapped[list["AgentEvent"]] = relationship("AgentEvent", back_populates="run", cascade="all, delete-orphan")
    citations: Mapped[list["ReportCitation"]] = relationship("ReportCitation", back_populates="run", cascade="all, delete-orphan")


class ResearchStep(Base):
    """Individual plan step executed by the research orchestrator."""
    __tablename__ = "research_steps"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id: Mapped[str] = mapped_column(String(36), ForeignKey("research_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    step_order: Mapped[int] = mapped_column(Integer, nullable=False)
    step_type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    input_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    output_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    run: Mapped["ResearchRun"] = relationship("ResearchRun", back_populates="steps")


class AgentEvent(Base):
    """Observable operational activity event log for a research run."""
    __tablename__ = "agent_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id: Mapped[str] = mapped_column(String(36), ForeignKey("research_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    safe_summary: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    run: Mapped["ResearchRun"] = relationship("ResearchRun", back_populates="events")

    __table_args__ = (
        Index("idx_events_run_seq", "run_id", "sequence"),
    )


class ReportCitation(Base):
    """Verified citation linkage mapping a claim to an actual document chunk & page."""
    __tablename__ = "report_citations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id: Mapped[str] = mapped_column(String(36), ForeignKey("research_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    citation_key: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g., "[1]"
    document_id: Mapped[str] = mapped_column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("document_chunks.id", ondelete="SET NULL"), nullable=True)
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    exact_excerpt: Mapped[str] = mapped_column(Text, nullable=False)
    source_metadata_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    verification_status: Mapped[str] = mapped_column(String(50), default="verified", nullable=False)

    run: Mapped["ResearchRun"] = relationship("ResearchRun", back_populates="citations")
