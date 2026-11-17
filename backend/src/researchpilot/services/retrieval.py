"""Hybrid retrieval engine combining vector similarity and full-text keyword search."""
import math
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from researchpilot.db.models import Document, DocumentChunk
from researchpilot.services.ai_provider import AIProvider


@dataclass
class RetrievedEvidence:
    """Standardized evidence object grounded in an uploaded document."""
    document_id: str
    chunk_id: str
    document_title: str
    page_start: int
    page_end: int
    text: str
    token_count: int
    score: float
    retrieval_method: str  # "vector", "keyword", or "hybrid_rrf"


def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    """Compute cosine similarity between two float vectors."""
    dot = sum(a * b for a, b in zip(v1, v2))
    norm_a = math.sqrt(sum(a * a for a in v1))
    norm_b = math.sqrt(sum(b * b for b in v2))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class RetrievalEngine:
    """Performs hybrid dense vector and keyword retrieval with Reciprocal Rank Fusion."""

    def __init__(self, session: AsyncSession, ai_provider: AIProvider):
        self.session = session
        self.ai_provider = ai_provider

    async def search(
        self,
        query: str,
        owner_id: str,
        selected_document_ids: list[str],
        limit: int = 10,
        token_budget: int = 4000,
    ) -> list[RetrievedEvidence]:
        """Execute hybrid search over the selected uploaded corpus."""
        if not selected_document_ids or not query.strip():
            return []

        # 1. Fetch chunks belonging strictly to owner and selected documents
        stmt = (
            select(DocumentChunk)
            .join(Document, DocumentChunk.document_id == Document.id)
            .options(selectinload(DocumentChunk.document))
            .where(
                DocumentChunk.owner_id == owner_id,
                DocumentChunk.document_id.in_(selected_document_ids),
                Document.processing_status == "ready",
            )
        )
        result = await self.session.execute(stmt)
        chunks = list(result.scalars().all())

        if not chunks:
            return []

        # 2. Vector Dense Scoring
        query_embeddings = await self.ai_provider.get_embeddings([query])
        query_vec = query_embeddings[0] if query_embeddings else None

        vector_scores: list[tuple[DocumentChunk, float]] = []
        if query_vec:
            for chunk in chunks:
                if chunk.embedding:
                    # In SQLite or memory, chunk.embedding might be a list or vector
                    emb = list(chunk.embedding)
                    sim = cosine_similarity(query_vec, emb)
                    vector_scores.append((chunk, sim))
            vector_scores.sort(key=lambda x: x[1], reverse=True)

        # 3. Keyword BM25/Lexical Scoring (token matching frequency)
        query_terms = [t.lower() for t in query.split() if len(t) > 2]
        keyword_scores: list[tuple[DocumentChunk, float]] = []
        for chunk in chunks:
            text_lower = chunk.text.lower()
            match_count = sum(text_lower.count(term) for term in query_terms)
            if match_count > 0:
                keyword_scores.append((chunk, float(match_count)))
        keyword_scores.sort(key=lambda x: x[1], reverse=True)

        # 4. Reciprocal Rank Fusion (RRF): RRF_score = sum(1.0 / (k + rank))
        rrf_k = 60
        rrf_map: dict[str, dict[str, Any]] = {}

        for rank, (chunk, _) in enumerate(vector_scores):
            if chunk.id not in rrf_map:
                rrf_map[chunk.id] = {"chunk": chunk, "score": 0.0, "vector_rank": rank + 1}
            rrf_map[chunk.id]["score"] += 1.0 / (rrf_k + rank + 1)

        for rank, (chunk, _) in enumerate(keyword_scores):
            if chunk.id not in rrf_map:
                rrf_map[chunk.id] = {"chunk": chunk, "score": 0.0, "keyword_rank": rank + 1}
            rrf_map[chunk.id]["score"] += 1.0 / (rrf_k + rank + 1)

        # Fallback if no specific matches found: default to all chunks
        if not rrf_map:
            for rank, chunk in enumerate(chunks[:limit]):
                rrf_map[chunk.id] = {"chunk": chunk, "score": 1.0 / (rrf_k + rank + 1)}

        # Sort aggregated results
        sorted_rrf = sorted(rrf_map.values(), key=lambda x: x["score"], reverse=True)

        # 5. Pack results within token budget and limit
        evidence_list: list[RetrievedEvidence] = []
        accumulated_tokens = 0

        for item in sorted_rrf:
            chunk: DocumentChunk = item["chunk"]
            if accumulated_tokens + chunk.token_count > token_budget and evidence_list:
                break

            doc_title = chunk.document.title or chunk.document.original_filename if chunk.document else "Document"

            evidence_list.append(
                RetrievedEvidence(
                    document_id=chunk.document_id,
                    chunk_id=chunk.id,
                    document_title=doc_title,
                    page_start=chunk.page_start,
                    page_end=chunk.page_end,
                    text=chunk.text,
                    token_count=chunk.token_count,
                    score=item["score"],
                    retrieval_method="hybrid_rrf",
                )
            )
            accumulated_tokens += chunk.token_count

            if len(evidence_list) >= limit:
                break

        return evidence_list
