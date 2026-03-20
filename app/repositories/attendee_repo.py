"""Attendee repository — all attendee-related DB queries."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.attendee import Attendee
from app.models.event import Event
from app.repositories.base import BaseRepository


class AttendeeRepository(BaseRepository[Attendee]):
    """Data access for Attendee entities."""

    model = Attendee

    async def get_by_event(self, event_id: uuid.UUID) -> list[Attendee]:
        """Fetch all attendees for an event."""
        stmt = select(Attendee).where(Attendee.event_id == event_id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_wecom_id(self, wecom_user_id: str) -> Attendee | None:
        """Look up attendee by WeChat Work user ID."""
        stmt = select(Attendee).where(Attendee.wecom_user_id == wecom_user_id)
        result = await self._session.execute(stmt)
        return result.scalars().first()

    async def find_by_wecom_id_in_active_event(
        self, wecom_user_id: str
    ) -> Attendee | None:
        """Find attendee bound to wecom_user_id in an active event.

        Eagerly loads the event relationship so caller can access event.name.
        """
        stmt = (
            select(Attendee)
            .join(Event, Attendee.event_id == Event.id)
            .options(joinedload(Attendee.event))
            .where(Attendee.wecom_user_id == wecom_user_id)
            .where(Event.status == "active")
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalars().first()

    async def fuzzy_match_in_active_events(
        self, name_fragment: str
    ) -> Attendee | None:
        """Fuzzy-match attendee by name across all active events.

        Returns the first match with its event eagerly loaded.
        """
        stmt = (
            select(Attendee)
            .join(Event, Attendee.event_id == Event.id)
            .options(joinedload(Attendee.event))
            .where(Attendee.name.ilike(f"%{name_fragment}%"))
            .where(Event.status == "active")
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalars().first()

    async def bind_wecom_id(
        self, attendee_id: uuid.UUID, wecom_user_id: str
    ) -> Attendee | None:
        """Bind a WeChat Work user ID to an attendee."""
        return await self.update(attendee_id, wecom_user_id=wecom_user_id)

    async def get_by_lark_id(self, lark_user_id: str) -> Attendee | None:
        """Look up attendee by Lark/Feishu user ID."""
        stmt = select(Attendee).where(Attendee.lark_user_id == lark_user_id)
        result = await self._session.execute(stmt)
        return result.scalars().first()

    async def fuzzy_match_by_name(
        self, event_id: uuid.UUID, name_fragment: str
    ) -> list[Attendee]:
        """Fuzzy-match attendees by name within an event."""
        stmt = (
            select(Attendee)
            .where(Attendee.event_id == event_id)
            .where(Attendee.name.ilike(f"%{name_fragment}%"))
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_role(
        self, event_id: uuid.UUID, role: str
    ) -> list[Attendee]:
        """Fetch all attendees with a specific role in an event."""
        stmt = (
            select(Attendee)
            .where(Attendee.event_id == event_id)
            .where(Attendee.role == role)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
