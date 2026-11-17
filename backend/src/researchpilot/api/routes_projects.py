"""Project workspace API routes."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from researchpilot.api.deps import get_current_user
from researchpilot.api.schemas.project_schemas import (
    ProjectCreateRequest,
    ProjectResponse,
    ProjectUpdateRequest,
)
from researchpilot.db.models import User
from researchpilot.db.session import get_db_session
from researchpilot.repositories.project_repo import ProjectRepository

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.get("", response_model=list[ProjectResponse])
async def list_projects(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """List all research projects owned by the authenticated user."""
    repo = ProjectRepository(session)
    projects = await repo.list_by_owner(current_user.id)
    return [
        ProjectResponse(
            id=p.id,
            owner_id=p.owner_id,
            title=p.title,
            description=p.description,
            created_at=p.created_at,
            updated_at=p.updated_at,
            document_count=len(p.documents) if hasattr(p, "documents") and p.documents else 0,
        )
        for p in projects
    ]


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    payload: ProjectCreateRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Create a new research project workspace."""
    repo = ProjectRepository(session)
    project = await repo.create(current_user.id, payload.title, payload.description)
    return ProjectResponse(
        id=project.id,
        owner_id=project.owner_id,
        title=project.title,
        description=project.description,
        created_at=project.created_at,
        updated_at=project.updated_at,
        document_count=0,
    )


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Retrieve project details by ID with ownership isolation."""
    repo = ProjectRepository(session)
    project = await repo.get_by_id_and_owner(project_id, current_user.id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or unauthorized",
        )
    return ProjectResponse(
        id=project.id,
        owner_id=project.owner_id,
        title=project.title,
        description=project.description,
        created_at=project.created_at,
        updated_at=project.updated_at,
        document_count=len(project.documents) if project.documents else 0,
    )


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    payload: ProjectUpdateRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Update project details."""
    repo = ProjectRepository(session)
    project = await repo.update(
        project_id=project_id,
        owner_id=current_user.id,
        title=payload.title,
        description=payload.description,
    )
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or unauthorized",
        )
    return ProjectResponse(
        id=project.id,
        owner_id=project.owner_id,
        title=project.title,
        description=project.description,
        created_at=project.created_at,
        updated_at=project.updated_at,
        document_count=len(project.documents) if hasattr(project, "documents") and project.documents else 0,
    )


@router.delete("/{project_id}", status_code=status.HTTP_200_OK)
async def delete_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Delete a research project workspace."""
    repo = ProjectRepository(session)
    deleted = await repo.delete(project_id, current_user.id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or unauthorized",
        )
    return {"message": "Project deleted successfully"}
