"""Integration and benchmark tests for the Hybrid Retrieval Engine."""
import fitz
import pytest
from researchpilot.db.models import Document, DocumentChunk, Project, User
from researchpilot.services.ai_provider import MockAIProvider
from researchpilot.services.retrieval import RetrievalEngine


def create_pdf_text(text: str) -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), text)
    b = doc.write()
    doc.close()
    return b


@pytest.mark.asyncio
async def test_hybrid_retrieval_ranking_and_isolation(db_session):
    """Verify hybrid search ranks relevant passages and respects ownership and document selection."""
    ai = MockAIProvider(dimensions=1536)

    # 1. Create User A and User B
    user_a = User(name="User A", email="a@test.com", password_hash="hash")
    user_b = User(name="User B", email="b@test.com", password_hash="hash")
    db_session.add_all([user_a, user_b])
    await db_session.flush()

    # 2. Create Project and Documents for User A
    proj_a = Project(owner_id=user_a.id, title="Brain Tumor Research")
    db_session.add(proj_a)
    await db_session.flush()

    doc1 = Document(
        project_id=proj_a.id,
        owner_id=user_a.id,
        original_filename="cnn_tumors.pdf",
        private_storage_key="k1.pdf",
        sha256="hash1",
        file_size=1000,
        title="CNN Architectures for Glioblastoma",
        processing_status="ready",
    )
    doc2 = Document(
        project_id=proj_a.id,
        owner_id=user_a.id,
        original_filename="transformers.pdf",
        private_storage_key="k2.pdf",
        sha256="hash2",
        file_size=1000,
        title="Vision Transformers in Neuroimaging",
        processing_status="ready",
    )
    db_session.add_all([doc1, doc2])
    await db_session.flush()

    # Chunks for doc1 and doc2
    chunk1_text = "ResNet-50 demonstrates a 94.2% Dice similarity coefficient on BraTS 2020."
    emb1 = (await ai.get_embeddings([chunk1_text]))[0]
    c1 = DocumentChunk(
        document_id=doc1.id,
        owner_id=user_a.id,
        chunk_index=0,
        page_start=3,
        page_end=3,
        text=chunk1_text,
        token_count=15,
        content_hash="h1",
        embedding=emb1,
    )

    chunk2_text = "Vision Transformers require substantial pretraining and achieve 91.8% Dice."
    emb2 = (await ai.get_embeddings([chunk2_text]))[0]
    c2 = DocumentChunk(
        document_id=doc2.id,
        owner_id=user_a.id,
        chunk_index=0,
        page_start=1,
        page_end=1,
        text=chunk2_text,
        token_count=13,
        content_hash="h2",
        embedding=emb2,
    )

    # Chunk for User B (must never leak)
    doc_b = Document(
        project_id=proj_a.id,
        owner_id=user_b.id,
        original_filename="secret_b.pdf",
        private_storage_key="kb.pdf",
        sha256="hashb",
        file_size=500,
        title="Secret Document",
        processing_status="ready",
    )
    db_session.add(doc_b)
    await db_session.flush()

    c_b = DocumentChunk(
        document_id=doc_b.id,
        owner_id=user_b.id,
        chunk_index=0,
        page_start=1,
        page_end=1,
        text="User B confidential information regarding ResNet.",
        token_count=8,
        content_hash="hb",
        embedding=emb1,
    )

    db_session.add_all([c1, c2, c_b])
    await db_session.commit()

    # 3. Perform Hybrid Search as User A
    engine = RetrievalEngine(db_session, ai)
    results = await engine.search(
        query="ResNet Dice coefficient BraTS",
        owner_id=user_a.id,
        selected_document_ids=[doc1.id, doc2.id],
        limit=5,
    )

    assert len(results) > 0
    # Top result should be chunk1 because of exact keyword & semantic match
    top = results[0]
    assert top.chunk_id == c1.id
    assert "94.2% Dice" in top.text
    assert top.page_start == 3

    # Ensure User B's chunk was never retrieved
    retrieved_chunk_ids = [r.chunk_id for r in results]
    assert c_b.id not in retrieved_chunk_ids

    # 4. Search with only doc2 selected -> doc1 must not be included
    doc2_only_results = await engine.search(
        query="ResNet Dice",
        owner_id=user_a.id,
        selected_document_ids=[doc2.id],
        limit=5,
    )
    assert all(r.document_id == doc2.id for r in doc2_only_results)
