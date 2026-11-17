"""Evidence retrieval and viewer API routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from researchpilot.api.deps import get_current_user
from researchpilot.api.schemas.retrieval_schemas import (
    EvidenceQueryRequest,
    EvidenceResponse,
)
from researchpilot.db.models import Document, DocumentChunk, User
from researchpilot.db.session import get_db_session
from researchpilot.services.ai_provider import get_ai_provider
from researchpilot.services.retrieval import RetrievalEngine

router = APIRouter(prefix="/retrieval", tags=["Retrieval & Evidence"])


@router.post("/search", response_model=list[EvidenceResponse])
async def search_evidence(
    payload: EvidenceQueryRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Perform hybrid vector and keyword search over the user's selected documents."""
    ai_provider = get_ai_provider()
    engine = RetrievalEngine(session, ai_provider)
    results = await engine.search(
        query=payload.query,
        owner_id=current_user.id,
        selected_document_ids=payload.selected_document_ids,
        limit=payload.limit,
    )
    return [
        EvidenceResponse(
            document_id=r.document_id,
            chunk_id=r.chunk_id,
            document_title=r.document_title,
            page_start=r.page_start,
            page_end=r.page_end,
            text=r.text,
            token_count=r.token_count,
            score=r.score,
            retrieval_method=r.retrieval_method,
        )
        for r in results
    ]


@router.get("/evidence/chunk/{chunk_id}")
async def get_chunk_evidence(
    chunk_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Retrieve full context of a cited chunk for the evidence viewer."""
    chunk = await session.get(DocumentChunk, chunk_id)
    if not chunk or chunk.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Chunk not found or unauthorized")

    doc = await session.get(Document, chunk.document_id)
    return {
        "chunk_id": chunk.id,
        "document_id": chunk.document_id,
        "document_title": doc.title if doc else "Document",
        "page_start": chunk.page_start,
        "page_end": chunk.page_end,
        "text": chunk.text,
        "publication_year": doc.publication_year if doc else None,
        "authors": doc.authors if doc else None,
    }
