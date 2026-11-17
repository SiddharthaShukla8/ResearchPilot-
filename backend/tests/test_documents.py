"""Unit and integration tests for PDF upload, storage, parsing, and ingestion."""
import io
import fitz
import pytest
from httpx import ASGITransport, AsyncClient
from researchpilot.main import app
from researchpilot.services.pdf_parser import PDFParser, PDFValidationError


def create_sample_pdf(text: str, page_count: int = 1) -> bytes:
    """Helper to generate a real, in-memory PDF with text."""
    doc = fitz.open()
    for _ in range(page_count):
        page = doc.new_page()
        page.insert_text((50, 50), text)
    pdf_bytes = doc.write()
    doc.close()
    return pdf_bytes


def test_pdf_parser_validation():
    """Verify parser enforces PDF signature, page bounds, and text content."""
    parser = PDFParser(max_mb=5, max_pages=10)

    # 1. Reject non-PDF bytes
    with pytest.raises(PDFValidationError, match="Invalid file signature"):
        parser.validate_and_open(b"This is a plain text file, not a PDF.")

    # 2. Reject empty/corrupt PDF header
    with pytest.raises(PDFValidationError, match="Corrupt or unreadable PDF"):
        parser.validate_and_open(b"%PDF-1.4\n%corrupt-stream-content")

    # 3. Reject oversized page count
    over_bytes = create_sample_pdf("Page content", page_count=15)
    with pytest.raises(PDFValidationError, match="exceeds limit"):
        parser.validate_and_open(over_bytes)

    # 4. Valid PDF extraction
    valid_bytes = create_sample_pdf(
        "Abstract: Deep convolutional neural networks achieve 94.5% accuracy on Brain Tumor segmentation.",
        page_count=2,
    )
    doc = parser.validate_and_open(valid_bytes)
    assert len(doc) == 2
    pages = parser.extract_pages(doc)
    assert len(pages) == 2
    assert pages[0].page_number == 1
    assert "Deep convolutional" in pages[0].text

    # 5. Chunk generation
    chunks = parser.create_chunks(pages, chunk_size_tokens=50, chunk_overlap_tokens=10)
    assert len(chunks) >= 1
    assert chunks[0].page_start == 1


@pytest.mark.asyncio
async def test_document_upload_and_deduplication():
    """Verify document upload, validation, duplicate prevention, and download access."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Register user
        reg_res = await client.post(
            "/api/v1/auth/register",
            json={
                "name": "Prof. Smith",
                "email": "smith@test.edu",
                "password": "Password123!",
            },
        )
        token = reg_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create project
        proj_res = await client.post(
            "/api/v1/projects",
            headers=headers,
            json={"title": "AI in Oncology"},
        )
        project_id = proj_res.json()["id"]

        # Generate sample PDF
        pdf_content = create_sample_pdf("Evaluation of CNN vs Vision Transformers on BraTS dataset.")

        # Upload valid PDF
        upload_res = await client.post(
            f"/api/v1/projects/{project_id}/documents",
            headers=headers,
            files={"files": ("paper1.pdf", io.BytesIO(pdf_content), "application/pdf")},
        )
        assert upload_res.status_code == 200
        data = upload_res.json()
        assert len(data["uploaded"]) == 1
        assert len(data["duplicates"]) == 0
        doc_id = data["uploaded"][0]["id"]

        # Attempt to upload duplicate in same project
        dup_res = await client.post(
            f"/api/v1/projects/{project_id}/documents",
            headers=headers,
            files={"files": ("paper1_copy.pdf", io.BytesIO(pdf_content), "application/pdf")},
        )
        assert dup_res.status_code == 200
        dup_data = dup_res.json()
        assert len(dup_data["uploaded"]) == 0
        assert "paper1_copy.pdf" in dup_data["duplicates"]

        # Check document status
        status_res = await client.get(
            f"/api/v1/documents/{doc_id}/status",
            headers=headers,
        )
        assert status_res.status_code == 200
        assert status_res.json()["status"] in ["uploaded", "queued", "parsing", "ready", "error"]

        # Trigger reprocess
        reproc_res = await client.post(
            f"/api/v1/documents/{doc_id}/reprocess",
            headers=headers,
        )
        assert reproc_res.status_code == 200
        assert reproc_res.json()["processing_status"] in ["uploaded", "queued", "parsing", "ready", "error"]

        # Download document
        down_res = await client.get(
            f"/api/v1/documents/{doc_id}/download",
            headers=headers,
        )
        assert down_res.status_code == 200
        assert down_res.headers["content-type"] == "application/pdf"
        assert len(down_res.content) == len(pdf_content)

        # Delete document
        del_res = await client.delete(
            f"/api/v1/documents/{doc_id}",
            headers=headers,
        )
        assert del_res.status_code == 200

        # Verify 404 after deletion
        get_res = await client.get(
            f"/api/v1/documents/{doc_id}",
            headers=headers,
        )
        assert get_res.status_code == 404
