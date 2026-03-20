"""Organizer repository — all organizer-related DB queries."""

from sqlalchemy import select

from app.models.organizer import Organizer
from app.repositories.base import BaseRepository


class OrganizerRepository(BaseRepository[Organizer]):
    """Data access for Organizer entities."""

    model = Organizer

    async def get_by_email(self, email: str) -> Organizer | None:
        """Look up organizer by email (for login)."""
        stmt = select(Organizer).where(Organizer.email == email)
        result = await self._session.execute(stmt)
        return result.scalars().first()

    async def email_exists(self, email: str) -> bool:
        """Check if email is already registered."""
        org = await self.get_by_email(email)
        return org is not None
