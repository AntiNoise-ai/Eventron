"""VenueArea repository — all venue-area-related DB queries."""

import uuid

from sqlalchemy import select

from app.models.venue_area import VenueArea
from app.repositories.base import BaseRepository


class VenueAreaRepository(BaseRepository[VenueArea]):
    """Data access for VenueArea entities."""

    model = VenueArea

    async def get_by_event(
        self, event_id: uuid.UUID
    ) -> list[VenueArea]:
        """Fetch all areas for an event, ordered by display_order."""
        stmt = (
            select(VenueArea)
            .where(VenueArea.event_id == event_id)
            .order_by(VenueArea.display_order)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
