"""Initial database migration for ResearchPilot models.

Revision ID: 0001_initial
Revises:
Create Date: 2026-11-18 00:54:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import pgvector

# revision identifiers, used by Alembic.
revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Ensure pgvector extension exists
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # users
    op.create_table(
        'users',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # refresh_sessions
    op.create_table(
        'refresh_sessions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('hashed_refresh_token', sa.String(length=255), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_refresh_sessions_hashed_refresh_token'), 'refresh_sessions', ['hashed_refresh_token'], unique=True)
    op.create_index(op.f('ix_refresh_sessions_user_id'), 'refresh_sessions', ['user_id'], unique=False)

    # projects
    op.create_table(
        'projects',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('owner_id', sa.String(length=36), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_projects_owner_id'), 'projects', ['owner_id'], unique=False)

    # documents
    op.create_table(
        'documents',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('project_id', sa.String(length=36), nullable=False),
        sa.Column('owner_id', sa.String(length=36), nullable=False),
        sa.Column('original_filename', sa.String(length=255), nullable=False),
        sa.Column('private_storage_key', sa.String(length=255), nullable=False),
        sa.Column('sha256', sa.String(length=64), nullable=False),
        sa.Column('mime_type', sa.String(length=100), nullable=False),
        sa.Column('file_size', sa.BigInteger(), nullable=False),
        sa.Column('page_count', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=True),
        sa.Column('authors', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('publication_year', sa.Integer(), nullable=True),
        sa.Column('doi', sa.String(length=255), nullable=True),
        sa.Column('processing_status', sa.String(length=50), nullable=False),
        sa.Column('processing_error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('private_storage_key')
    )
    op.create_index('idx_doc_project_sha256', 'documents', ['project_id', 'sha256'], unique=False)
    op.create_index(op.f('ix_documents_owner_id'), 'documents', ['owner_id'], unique=False)
    op.create_index(op.f('ix_documents_processing_status'), 'documents', ['processing_status'], unique=False)
    op.create_index(op.f('ix_documents_project_id'), 'documents', ['project_id'], unique=False)
    op.create_index(op.f('ix_documents_sha256'), 'documents', ['sha256'], unique=False)

    # document_chunks
    op.create_table(
        'document_chunks',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('document_id', sa.String(length=36), nullable=False),
        sa.Column('owner_id', sa.String(length=36), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('page_start', sa.Integer(), nullable=False),
        sa.Column('page_end', sa.Integer(), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('token_count', sa.Integer(), nullable=False),
        sa.Column('content_hash', sa.String(length=64), nullable=False),
        sa.Column('embedding', pgvector.sqlalchemy.Vector(1536), nullable=True),
        sa.Column('tsv', postgresql.TSVECTOR(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_chunk_doc_index', 'document_chunks', ['document_id', 'chunk_index'], unique=False)
    op.create_index(op.f('ix_document_chunks_document_id'), 'document_chunks', ['document_id'], unique=False)
    op.create_index(op.f('ix_document_chunks_owner_id'), 'document_chunks', ['owner_id'], unique=False)

    # processing_jobs
    op.create_table(
        'processing_jobs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('owner_id', sa.String(length=36), nullable=False),
        sa.Column('project_id', sa.String(length=36), nullable=True),
        sa.Column('target_id', sa.String(length=36), nullable=False),
        sa.Column('job_type', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('attempts', sa.Integer(), nullable=False),
        sa.Column('max_attempts', sa.Integer(), nullable=False),
        sa.Column('available_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('locked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('locked_by', sa.String(length=100), nullable=True),
        sa.Column('heartbeat_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_jobs_claim', 'processing_jobs', ['status', 'available_at', 'attempts'], unique=False)
    op.create_index(op.f('ix_processing_jobs_job_type'), 'processing_jobs', ['job_type'], unique=False)
    op.create_index(op.f('ix_processing_jobs_owner_id'), 'processing_jobs', ['owner_id'], unique=False)
    op.create_index(op.f('ix_processing_jobs_project_id'), 'processing_jobs', ['project_id'], unique=False)
    op.create_index(op.f('ix_processing_jobs_status'), 'processing_jobs', ['status'], unique=False)
    op.create_index(op.f('ix_processing_jobs_target_id'), 'processing_jobs', ['target_id'], unique=False)

    # research_runs
    op.create_table(
        'research_runs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('project_id', sa.String(length=36), nullable=False),
        sa.Column('owner_id', sa.String(length=36), nullable=False),
        sa.Column('research_question', sa.Text(), nullable=False),
        sa.Column('selected_document_ids', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('citation_style', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('plan_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('report_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('report_markdown', sa.Text(), nullable=True),
        sa.Column('error_code', sa.String(length=100), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_research_runs_owner_id'), 'research_runs', ['owner_id'], unique=False)
    op.create_index(op.f('ix_research_runs_project_id'), 'research_runs', ['project_id'], unique=False)
    op.create_index(op.f('ix_research_runs_status'), 'research_runs', ['status'], unique=False)

    # research_steps
    op.create_table(
        'research_steps',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('run_id', sa.String(length=36), nullable=False),
        sa.Column('step_order', sa.Integer(), nullable=False),
        sa.Column('step_type', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('instructions', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('input_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('output_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['run_id'], ['research_runs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_research_steps_run_id'), 'research_steps', ['run_id'], unique=False)

    # agent_events
    op.create_table(
        'agent_events',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('run_id', sa.String(length=36), nullable=False),
        sa.Column('sequence', sa.Integer(), nullable=False),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('safe_summary', sa.Text(), nullable=False),
        sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['run_id'], ['research_runs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_events_run_seq', 'agent_events', ['run_id', 'sequence'], unique=False)
    op.create_index(op.f('ix_agent_events_run_id'), 'agent_events', ['run_id'], unique=False)

    # report_citations
    op.create_table(
        'report_citations',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('run_id', sa.String(length=36), nullable=False),
        sa.Column('citation_key', sa.String(length=50), nullable=False),
        sa.Column('document_id', sa.String(length=36), nullable=False),
        sa.Column('chunk_id', sa.String(length=36), nullable=True),
        sa.Column('page_number', sa.Integer(), nullable=False),
        sa.Column('exact_excerpt', sa.Text(), nullable=False),
        sa.Column('source_metadata_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('verification_status', sa.String(length=50), nullable=False),
        sa.ForeignKeyConstraint(['chunk_id'], ['document_chunks.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['run_id'], ['research_runs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_report_citations_document_id'), 'report_citations', ['document_id'], unique=False)
    op.create_index(op.f('ix_report_citations_run_id'), 'report_citations', ['run_id'], unique=False)


def downgrade() -> None:
    op.drop_table('report_citations')
    op.drop_table('agent_events')
    op.drop_table('research_steps')
    op.drop_table('research_runs')
    op.drop_table('processing_jobs')
    op.drop_table('document_chunks')
    op.drop_table('documents')
    op.drop_table('projects')
    op.drop_table('refresh_sessions')
    op.drop_table('users')
