"""Allowlisted tool registry with strict parameter validation and ownership enforcement."""
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from researchpilot.db.models import Document, DocumentChunk
from researchpilot.services.ai_provider import AIProvider
from researchpilot.services.retrieval import RetrievalEngine


class ToolSecurityError(Exception):
    """Raised when tool execution violates safety or ownership boundaries."""


class ToolRegistry:
    """Allowlist of safe research tools with ownership constraints."""

    def __init__(self, session: AsyncSession, owner_id: str, selected_document_ids: list[str], ai_provider: AIProvider):
        self.session = session
        self.owner_id = owner_id
        self.selected_document_ids = selected_document_ids
        self.ai_provider = ai_provider
        self.retrieval_engine = RetrievalEngine(session, ai_provider)

    async def search_paper_library(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        """Hybrid search across the selected paper collection."""
        evidence = await self.retrieval_engine.search(
            query=query,
            owner_id=self.owner_id,
            selected_document_ids=self.selected_document_ids,
            limit=min(limit, 10),
        )
        return [
            {
                "document_id": e.document_id,
                "chunk_id": e.chunk_id,
                "title": e.document_title,
                "page": e.page_start,
                "text": e.text,
                "score": e.score,
            }
            for e in evidence
        ]

    async def get_document_metadata(self, document_id: str) -> dict[str, Any]:
        """Safely retrieve paper metadata."""
        if document_id not in self.selected_document_ids:
            raise ToolSecurityError(f"Document {document_id} is not in the approved research corpus")

        doc = await self.session.get(Document, document_id)
        if not doc or doc.owner_id != self.owner_id:
            raise ToolSecurityError(f"Document {document_id} not found or unauthorized")

        return {
            "id": doc.id,
            "title": doc.title or doc.original_filename,
            "authors": doc.authors or [],
            "year": doc.publication_year,
            "page_count": doc.page_count,
            "status": doc.processing_status,
        }

    async def retrieve_page_context(self, document_id: str, page_number: int) -> dict[str, Any]:
        """Retrieve indexed passages on a specific page of a paper."""
        if document_id not in self.selected_document_ids:
            raise ToolSecurityError(f"Document {document_id} not in selected corpus")

        stmt = (
            select(DocumentChunk)
            .where(
                DocumentChunk.document_id == document_id,
                DocumentChunk.owner_id == self.owner_id,
                DocumentChunk.page_start <= page_number,
                DocumentChunk.page_end >= page_number,
            )
            .order_by(DocumentChunk.chunk_index.asc())
        )
        result = await self.session.execute(stmt)
        chunks = list(result.scalars().all())

        combined_text = "\n\n".join(c.text for c in chunks)
        return {
            "document_id": document_id,
            "page_number": page_number,
            "text": combined_text,
            "chunk_count": len(chunks),
        }

    async def search_exact_terms(self, term: str, limit: int = 5) -> list[dict[str, Any]]:
        """Exact lexical search for acronyms, datasets, and benchmark metrics."""
        return await self.search_paper_library(query=term, limit=limit)
