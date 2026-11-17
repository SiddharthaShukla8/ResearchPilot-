"""Persistent background worker loop with safe claiming and heartbeats."""
import asyncio
import logging
import os
import signal
import uuid

from researchpilot.core.config import get_settings
from researchpilot.db.session import async_session_factory
from researchpilot.repositories.job_repo import JobRepository
from researchpilot.services.ai_provider import get_ai_provider
from researchpilot.services.ingestion_service import DocumentIngestionService
from researchpilot.services.storage import LocalFileStorage

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [Worker] %(message)s",
)
logger = logging.getLogger("worker")


class BackgroundWorker:
    """Consumes and executes background processing jobs."""

    def __init__(self):
        self.worker_id = f"worker-{os.getpid()}-{uuid.uuid4().hex[:8]}"
        self.running = False
        self.settings = get_settings()
        self.storage = LocalFileStorage()
        self.ai_provider = get_ai_provider()

    async def run(self):
        """Worker event loop."""
        self.running = True
        logger.info("Worker %s started and listening for jobs...", self.worker_id)

        while self.running:
            try:
                processed_any = await self.process_one_job()
                if not processed_any:
                    # Sleep when no work is available
                    await asyncio.sleep(2.0)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in worker main loop: %s", str(e), exc_info=True)
                await asyncio.sleep(5.0)

        logger.info("Worker %s gracefully stopped.", self.worker_id)

    async def process_one_job(self) -> bool:
        """Claim and execute a single job."""
        async with async_session_factory() as session:
            repo = JobRepository(session)
            job = await repo.claim_next_job(self.worker_id)
            if not job:
                return False

            logger.info("Claimed job %s (type: %s, target: %s)", job.id, job.job_type, job.target_id)
            job_id = job.id
            job_type = job.job_type
            target_id = job.target_id
            await session.commit()

        # Execute claimed job
        try:
            if job_type == "ingest_document":
                async with async_session_factory() as proc_session:
                    service = DocumentIngestionService(
                        session=proc_session,
                        storage=self.storage,
                        ai_provider=self.ai_provider,
                    )
                    await service.process_document(target_id)

            elif job_type == "execute_research":
                from researchpilot.agents.orchestrator import ResearchOrchestrator
                async with async_session_factory() as proc_session:
                    orchestrator = ResearchOrchestrator(
                        session=proc_session,
                        ai_provider=self.ai_provider,
                    )
                    await orchestrator.run_pipeline(target_id)

            else:
                logger.warning("Unknown job type: %s", job_type)

            # Mark completed
            async with async_session_factory() as session:
                repo = JobRepository(session)
                await repo.complete_job(job_id)
                await session.commit()
            logger.info("Successfully finished job %s", job_id)
            return True

        except Exception as e:
            logger.exception("Job %s failed with error: %s", job_id, str(e))
            async with async_session_factory() as session:
                repo = JobRepository(session)
                # Retry if transient
                await repo.fail_job(job_id, error_msg=str(e), retryable=False)
                await session.commit()
            return True


def main():
    """CLI Entry point for running the background worker."""
    worker = BackgroundWorker()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    def shutdown():
        logger.info("Shutdown signal received.")
        worker.running = False

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, shutdown)
        except NotImplementedError:
            pass

    try:
        loop.run_until_complete(worker.run())
    finally:
        loop.close()


if __name__ == "__main__":
    main()
