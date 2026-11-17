"""Processing Job queue repository with row-level locking."""
from datetime import UTC, datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from researchpilot.db.models import ProcessingJob


class JobRepository:
    """PostgreSQL row-level locking queue (SELECT ... FOR UPDATE SKIP LOCKED)."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def enqueue(
        self,
        owner_id: str,
        project_id: str | None,
        target_id: str,
        job_type: str,
    ) -> ProcessingJob:
        """Enqueue a background processing job."""
        job = ProcessingJob(
            owner_id=owner_id,
            project_id=project_id,
            target_id=target_id,
            job_type=job_type,
            status="queued",
            attempts=0,
            available_at=datetime.now(UTC),
        )
        self.session.add(job)
        await self.session.flush()
        return job

    async def claim_next_job(self, worker_id: str) -> ProcessingJob | None:
        """Atomically claim the next ready job."""
        now = datetime.now(UTC)
        # Check dialect: if postgresql use with_for_update(skip_locked=True)
        stmt = (
            select(ProcessingJob)
            .where(
                ProcessingJob.status == "queued",
                ProcessingJob.available_at <= now,
                ProcessingJob.attempts < ProcessingJob.max_attempts,
            )
            .order_by(ProcessingJob.created_at.asc())
            .limit(1)
        )
        try:
            # Attempt lock
            stmt = stmt.with_for_update(skip_locked=True)
        except Exception:
            pass

        result = await self.session.execute(stmt)
        job = result.scalar_one_or_none()
        if job:
            job.status = "processing"
            job.locked_at = now
            job.locked_by = worker_id
            job.heartbeat_at = now
            job.attempts += 1
            await self.session.flush()
        return job

    async def heartbeat(self, job_id: str) -> None:
        """Record worker heartbeat."""
        stmt = (
            update(ProcessingJob)
            .where(ProcessingJob.id == job_id)
            .values(heartbeat_at=datetime.now(UTC))
        )
        await self.session.execute(stmt)

    async def complete_job(self, job_id: str) -> None:
        """Mark job successfully completed."""
        stmt = (
            update(ProcessingJob)
            .where(ProcessingJob.id == job_id)
            .values(status="completed", locked_at=None, locked_by=None)
        )
        await self.session.execute(stmt)

    async def fail_job(self, job_id: str, error_msg: str, retryable: bool = False) -> None:
        """Record failure and handle exponential backoff retry or terminal fail."""
        job_stmt = select(ProcessingJob).where(ProcessingJob.id == job_id)
        res = await self.session.execute(job_stmt)
        job = res.scalar_one_or_none()
        if not job:
            return

        job.last_error = error_msg
        job.locked_at = None
        job.locked_by = None

        if retryable and job.attempts < job.max_attempts:
            # Exponential backoff: 2s, 4s, 8s
            backoff_secs = 2 ** job.attempts
            job.status = "queued"
            job.available_at = datetime.now(UTC) + timedelta(seconds=backoff_secs)
        else:
            job.status = "failed"
        await self.session.flush()
