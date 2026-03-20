"""Event repository — all event-related DB queries."""

from sqlalchemy import select

from app.models.event import Event
from app.repositories.base import BaseRepository


class EventRepository(BaseRepository[Event]):
    """Data access for Event entities."""

    model = Event

    async def get_by_status(self, status: str) -> list[Event]:
        """Fetch all events with a given status."""
        stmt = select(Event).where(Event.status == status)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_active_events(self) -> list[Event]:
        """Shortcut for fetching all active events."""
        return await self.get_by_status("active")
