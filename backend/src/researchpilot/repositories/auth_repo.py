"""Authentication and User management repository."""
from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from researchpilot.core.security import hash_password, hash_token
from researchpilot.db.models import RefreshSession, User


class AuthRepository:
    """Database operations for users and authentication sessions."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user_by_email(self, email: str) -> User | None:
        """Fetch user by normalized email."""
        stmt = select(User).where(User.email == email.lower().strip())
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: str) -> User | None:
        """Fetch user by primary ID."""
        stmt = select(User).where(User.id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_user(self, name: str, email: str, password: str) -> User:
        """Create and persist a new user."""
        user = User(
            name=name.strip(),
            email=email.lower().strip(),
            password_hash=hash_password(password),
        )
        self.session.add(user)
        await self.session.flush()
        return user

    async def create_refresh_session(
        self, user_id: str, raw_refresh_token: str, expires_at: datetime
    ) -> RefreshSession:
        """Store hashed refresh session token."""
        session = RefreshSession(
            user_id=user_id,
            hashed_refresh_token=hash_token(raw_refresh_token),
            expires_at=expires_at,
        )
        self.session.add(session)
        await self.session.flush()
        return session

    async def get_active_refresh_session(self, raw_refresh_token: str) -> RefreshSession | None:
        """Retrieve valid unrevoked and unexpired refresh session."""
        hashed = hash_token(raw_refresh_token)
        now = datetime.now(UTC)
        stmt = select(RefreshSession).where(
            RefreshSession.hashed_refresh_token == hashed,
            RefreshSession.revoked_at.is_(None),
            RefreshSession.expires_at > now,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def revoke_refresh_session(self, raw_refresh_token: str) -> bool:
        """Revoke a refresh session token."""
        hashed = hash_token(raw_refresh_token)
        stmt = (
            update(RefreshSession)
            .where(RefreshSession.hashed_refresh_token == hashed)
            .values(revoked_at=datetime.now(UTC))
        )
        result = await self.session.execute(stmt)
        return result.rowcount > 0
