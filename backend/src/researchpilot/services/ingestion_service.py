"""Document ingestion pipeline orchestrating extraction, chunking, and embedding."""
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from researchpilot.core.config import get_settings
from researchpilot.db.models import Document
from researchpilot.repositories.document_repo import DocumentRepository
from researchpilot.services.ai_provider import AIProvider
from researchpilot.services.pdf_parser import PDFParser, PDFValidationError
from researchpilot.services.storage import StorageBackend

logger = logging.getLogger(__name__)


class DocumentIngestionService:
    """Orchestrates end-to-end ingestion and indexing of uploaded PDFs."""

    def __init__(
        self,
        session: AsyncSession,
        storage: StorageBackend,
        ai_provider: AIProvider,
        parser: PDFParser | None = None,
    ):
        self.session = session
        self.storage = storage
        self.ai_provider = ai_provider
        self.settings = get_settings()
        self.parser = parser or PDFParser(
            max_mb=self.settings.max_upload_mb,
            max_pages=self.settings.max_pdf_pages,
        )
        self.doc_repo = DocumentRepository(session)

    async def process_document(self, document_id: str) -> None:
        """Execute full ingestion pipeline for a document."""
        # 1. Fetch document record
        stmt_doc = await self.session.get(Document, document_id)
        if not stmt_doc:
            logger.error("Document %s not found for processing", document_id)
            return

        doc = stmt_doc
        logger.info("Starting ingestion for document %s (%s)", doc.id, doc.original_filename)

        try:
            # 2. Update status -> extracting
            await self.doc_repo.update_status(doc.id, status="extracting")
            await self.session.commit()

            # Read raw bytes from private storage
            pdf_bytes = await self.storage.read(doc.private_storage_key)

            # Validate and open with PyMuPDF
            pdf_doc = self.parser.validate_and_open(pdf_bytes)

            # Extract metadata and pages
            metadata = self.parser.extract_metadata(pdf_doc)
            pages = self.parser.extract_pages(pdf_doc)

            # 3. Update status -> chunking
            await self.doc_repo.update_status(
                doc.id,
                status="chunking",
                page_count=metadata.page_count,
                title=metadata.title or doc.original_filename,
                authors=metadata.authors,
                year=metadata.year,
            )
            await self.session.commit()

            # Generate semantic chunks
            chunks = self.parser.create_chunks(
                pages,
                chunk_size_tokens=self.settings.chunk_size_tokens,
                chunk_overlap_tokens=self.settings.chunk_overlap_tokens,
            )
            logger.info("Document %s partitioned into %d chunks", doc.id, len(chunks))

            # 4. Update status -> embedding
            await self.doc_repo.update_status(doc.id, status="embedding")
            await self.session.commit()

            # Batch generate embeddings
            chunk_texts = [c.text for c in chunks]
            embeddings = await self.ai_provider.get_embeddings(chunk_texts)

            # 5. Update status -> indexing
            await self.doc_repo.update_status(doc.id, status="indexing")
            await self.session.commit()

            chunks_data = []
            for i, chunk in enumerate(chunks):
                emb = embeddings[i] if i < len(embeddings) else None
                chunks_data.append({
                    "chunk_index": chunk.chunk_index,
                    "page_start": chunk.page_start,
                    "page_end": chunk.page_end,
                    "text": chunk.text,
                    "token_count": chunk.token_count,
                    "content_hash": chunk.content_hash,
                    "embedding": emb,
                })

            # Idempotently persist chunks
            await self.doc_repo.save_chunks(doc, chunks_data)

            # 6. Mark ready
            await self.doc_repo.update_status(doc.id, status="ready")
            await self.session.commit()
            logger.info("Document %s processing completed successfully", doc.id)

        except PDFValidationError as pve:
            logger.warning("Document %s failed validation: %s", doc.id, str(pve))
            await self.doc_repo.update_status(doc.id, status="failed", error=str(pve))
            await self.session.commit()
            raise

        except Exception as e:
            logger.exception("Unexpected error processing document %s", doc.id)
            await self.doc_repo.update_status(doc.id, status="failed", error=f"Internal processing error: {e!s}")
            await self.session.commit()
            raise
