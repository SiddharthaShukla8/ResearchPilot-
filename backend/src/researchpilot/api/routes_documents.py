"""Document management API routes."""
import hashlib
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from researchpilot.api.deps import get_current_user
from researchpilot.api.schemas.document_schemas import (
    DocumentResponse,
    DocumentUploadBatchResponse,
)
from researchpilot.core.config import get_settings
from researchpilot.db.models import User
from researchpilot.db.session import get_db_session
from researchpilot.repositories.document_repo import DocumentRepository
from researchpilot.repositories.job_repo import JobRepository
from researchpilot.repositories.project_repo import ProjectRepository
from researchpilot.services.storage import LocalFileStorage

router = APIRouter(tags=["Documents"])


@router.get("/projects/{project_id}/documents", response_model=list[DocumentResponse])
async def list_documents(
    project_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """List all documents uploaded to a project."""
    proj_repo = ProjectRepository(session)
    project = await proj_repo.get_by_id_and_owner(project_id, current_user.id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found or unauthorized")

    doc_repo = DocumentRepository(session)
    docs = await doc_repo.list_by_project(project_id, current_user.id)
    return docs


@router.post("/projects/{project_id}/documents", response_model=DocumentUploadBatchResponse)
async def upload_documents(
    project_id: str,
    files: list[UploadFile],
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Upload one or more PDF documents to a research project."""
    proj_repo = ProjectRepository(session)
    project = await proj_repo.get_by_id_and_owner(project_id, current_user.id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found or unauthorized")

    settings = get_settings()
    storage = LocalFileStorage()
    doc_repo = DocumentRepository(session)
    job_repo = JobRepository(session)

    uploaded: list[DocumentResponse] = []
    duplicates: list[str] = []
    failed: list[dict[str, str]] = []

    for file in files:
        filename = file.filename or "document.pdf"
        try:
            content = await file.read()
            size = len(content)

            # Limit size
            if size > settings.max_upload_mb * 1024 * 1024:
                failed.append({"filename": filename, "error": f"File exceeds {settings.max_upload_mb} MB limit"})
                continue

            # Check magic bytes
            if not content.startswith(b"%PDF-"):
                failed.append({"filename": filename, "error": "Invalid file format: must be a valid PDF"})
                continue

            # Compute SHA-256
            file_hash = hashlib.sha256(content).hexdigest()

            # Prevent duplicate uploads in same project
            existing = await doc_repo.find_by_hash(project_id, file_hash)
            if existing:
                duplicates.append(filename)
                continue

            # Save to private storage with random internal key
            storage_key = f"{uuid.uuid4().hex}.pdf"
            await storage.save(storage_key, content)

            # Create document record
            doc = await doc_repo.create(
                project_id=project_id,
                owner_id=current_user.id,
                original_filename=filename,
                private_storage_key=storage_key,
                sha256=file_hash,
                file_size=size,
            )

            # Enqueue background ingestion job
            await job_repo.enqueue(
                owner_id=current_user.id,
                project_id=project_id,
                target_id=doc.id,
                job_type="ingest_document",
            )

            uploaded.append(DocumentResponse.model_validate(doc))

        except Exception as e:
            failed.append({"filename": filename, "error": str(e)})

    await session.commit()
    return DocumentUploadBatchResponse(
        uploaded=uploaded,
        duplicates=duplicates,
        failed=failed,
    )


@router.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Retrieve document metadata and status."""
    repo = DocumentRepository(session)
    doc = await repo.get_by_id_and_owner(document_id, current_user.id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found or unauthorized")
    return doc


@router.get("/documents/{document_id}/download")
async def download_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Download the original uploaded PDF (authenticated)."""
    repo = DocumentRepository(session)
    doc = await repo.get_by_id_and_owner(document_id, current_user.id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found or unauthorized")

    storage = LocalFileStorage()
    try:
        content = await storage.read(doc.private_storage_key)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Underlying document file not found")

    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{doc.original_filename}"'},
    )


@router.delete("/documents/{document_id}", status_code=status.HTTP_200_OK)
async def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Delete a document, its indexed chunks, and its private file."""
    repo = DocumentRepository(session)
    doc = await repo.delete(document_id, current_user.id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found or unauthorized")

    storage = LocalFileStorage()
    await storage.delete(doc.private_storage_key)
    await session.commit()
    return {"message": "Document deleted successfully"}
