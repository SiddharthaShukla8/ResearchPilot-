"""Project repository for user-scoped workspace CRUD."""
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from researchpilot.db.models import Project


class ProjectRepository:
    """Ownership-scoped repository for research projects."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_by_owner(self, owner_id: str) -> list[Project]:
        """List all projects owned by a user."""
        stmt = (
            select(Project)
            .options(selectinload(Project.documents))
            .where(Project.owner_id == owner_id)
            .order_by(Project.updated_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id_and_owner(self, project_id: str, owner_id: str) -> Project | None:
        """Fetch project ensuring ownership isolation."""
        stmt = (
            select(Project)
            .options(selectinload(Project.documents))
            .where(Project.id == project_id, Project.owner_id == owner_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, owner_id: str, title: str, description: str | None = None) -> Project:
        """Create a new project for a user."""
        project = Project(
            owner_id=owner_id,
            title=title.strip(),
            description=description.strip() if description else None,
        )
        self.session.add(project)
        await self.session.flush()
        return project

    async def update(
        self, project_id: str, owner_id: str, title: str | None = None, description: str | None = None
    ) -> Project | None:
        """Update project title or description with ownership enforcement."""
        project = await self.get_by_id_and_owner(project_id, owner_id)
        if not project:
            return None
        if title is not None:
            project.title = title.strip()
        if description is not None:
            project.description = description.strip() if description else None
        await self.session.flush()
        return project

    async def delete(self, project_id: str, owner_id: str) -> bool:
        """Delete project ensuring ownership isolation."""
        stmt = delete(Project).where(Project.id == project_id, Project.owner_id == owner_id)
        result = await self.session.execute(stmt)
        return result.rowcount > 0
