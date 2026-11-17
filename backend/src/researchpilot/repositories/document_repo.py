"""Document repository for managing PDF assets and indexed chunks."""
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from researchpilot.db.models import Document, DocumentChunk


class DocumentRepository:
    """Ownership-scoped database operations for documents and indexed chunks."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_by_project(self, project_id: str, owner_id: str) -> list[Document]:
        """List all documents for a project owned by a user."""
        stmt = (
            select(Document)
            .where(Document.project_id == project_id, Document.owner_id == owner_id)
            .order_by(Document.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id_and_owner(self, document_id: str, owner_id: str) -> Document | None:
        """Get document with chunks loaded."""
        stmt = (
            select(Document)
            .options(selectinload(Document.chunks))
            .where(Document.id == document_id, Document.owner_id == owner_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_hash(self, project_id: str, sha256_hash: str) -> Document | None:
        """Find duplicate upload in the same project."""
        stmt = select(Document).where(
            Document.project_id == project_id,
            Document.sha256 == sha256_hash,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(
        self,
        project_id: str,
        owner_id: str,
        original_filename: str,
        private_storage_key: str,
        sha256: str,
        file_size: int,
        mime_type: str = "application/pdf",
    ) -> Document:
        """Create new uploaded document record in initial status."""
        doc = Document(
            project_id=project_id,
            owner_id=owner_id,
            original_filename=original_filename,
            private_storage_key=private_storage_key,
            sha256=sha256,
            file_size=file_size,
            mime_type=mime_type,
            processing_status="uploaded",
        )
        self.session.add(doc)
        await self.session.flush()
        return doc

    async def update_status(
        self,
        document_id: str,
        status: str,
        error: str | None = None,
        page_count: int | None = None,
        title: str | None = None,
        authors: list[str] | None = None,
        year: int | None = None,
    ) -> None:
        """Update processing status and extracted metadata."""
        stmt = select(Document).where(Document.id == document_id)
        result = await self.session.execute(stmt)
        doc = result.scalar_one_or_none()
        if doc:
            doc.processing_status = status
            doc.processing_error = error
            if page_count is not None:
                doc.page_count = page_count
            if title is not None:
                doc.title = title
            if authors is not None:
                doc.authors = authors
            if year is not None:
                doc.publication_year = year
            await self.session.flush()

    async def save_chunks(self, document: Document, chunks_data: list[dict]) -> None:
        """Idempotently replace all chunks for a document."""
        # Delete existing chunks first to guarantee idempotency
        del_stmt = delete(DocumentChunk).where(DocumentChunk.document_id == document.id)
        await self.session.execute(del_stmt)

        for item in chunks_data:
            chunk = DocumentChunk(
                document_id=document.id,
                owner_id=document.owner_id,
                chunk_index=item["chunk_index"],
                page_start=item["page_start"],
                page_end=item["page_end"],
                text=item["text"],
                token_count=item["token_count"],
                content_hash=item["content_hash"],
                embedding=item.get("embedding"),
            )
            self.session.add(chunk)
        await self.session.flush()

    async def delete(self, document_id: str, owner_id: str) -> Document | None:
        """Delete document and return record for storage cleanup."""
        doc = await self.get_by_id_and_owner(document_id, owner_id)
        if doc:
            await self.session.delete(doc)
            await self.session.flush()
        return doc
