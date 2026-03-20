"""Seat repository — all seat-related DB queries."""

import uuid

from sqlalchemy import select

from app.models.seat import Seat
from app.repositories.base import BaseRepository


class SeatRepository(BaseRepository[Seat]):
    """Data access for Seat entities."""

    model = Seat

    async def get_by_event(self, event_id: uuid.UUID) -> list[Seat]:
        """Fetch all seats for an event, ordered by row then col."""
        stmt = (
            select(Seat)
            .where(Seat.event_id == event_id)
            .order_by(Seat.row_num, Seat.col_num)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_available_seats(self, event_id: uuid.UUID) -> list[Seat]:
        """Fetch seats that have no attendee assigned and are not disabled/aisle."""
        stmt = (
            select(Seat)
            .where(Seat.event_id == event_id)
            .where(Seat.attendee_id.is_(None))
            .where(Seat.seat_type.notin_(["disabled", "aisle"]))
            .order_by(Seat.row_num, Seat.col_num)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def assign_attendee(
        self, seat_id: uuid.UUID, attendee_id: uuid.UUID
    ) -> Seat | None:
        """Assign an attendee to a seat."""
        return await self.update(seat_id, attendee_id=attendee_id)

    async def unassign(self, seat_id: uuid.UUID) -> Seat | None:
        """Remove attendee from a seat."""
        return await self.update(seat_id, attendee_id=None)

    async def swap_seats(
        self, seat_a_id: uuid.UUID, seat_b_id: uuid.UUID
    ) -> tuple[Seat | None, Seat | None]:
        """Swap the attendees of two seats atomically."""
        seat_a = await self.get_by_id(seat_a_id)
        seat_b = await self.get_by_id(seat_b_id)
        if seat_a is None or seat_b is None:
            return (None, None)

        seat_a.attendee_id, seat_b.attendee_id = seat_b.attendee_id, seat_a.attendee_id
        await self._session.flush()
        await self._session.refresh(seat_a)
        await self._session.refresh(seat_b)
        return (seat_a, seat_b)

    async def bulk_create_grid(
        self, event_id: uuid.UUID, rows: int, cols: int
    ) -> list[Seat]:
        """Create a full seat grid for an event."""
        seats = []
        for r in range(1, rows + 1):
            for c in range(1, cols + 1):
                seat = Seat(
                    event_id=event_id,
                    row_num=r,
                    col_num=c,
                    label=f"{chr(64 + r)}{c}",
                    seat_type="normal",
                )
                self._session.add(seat)
                seats.append(seat)
        await self._session.flush()
        for s in seats:
            await self._session.refresh(s)
        return seats

    async def get_by_attendee(self, attendee_id: uuid.UUID) -> Seat | None:
        """Find the seat assigned to a specific attendee."""
        stmt = select(Seat).where(Seat.attendee_id == attendee_id)
        result = await self._session.execute(stmt)
        return result.scalars().first()
