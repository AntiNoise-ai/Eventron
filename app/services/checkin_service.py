"""Check-in processing — business logic for attendee check-in."""

import uuid

from app.repositories.attendee_repo import AttendeeRepository
from app.repositories.seat_repo import SeatRepository
from app.services.exceptions import (
    AttendeeNotFoundError,
    InvalidStateTransitionError,
)


class CheckinService:
    """Business logic for attendee check-in operations."""

    def __init__(
        self,
        attendee_repo: AttendeeRepository,
        seat_repo: SeatRepository,
    ):
        self._attendee_repo = attendee_repo
        self._seat_repo = seat_repo

    async def checkin(self, attendee_id: uuid.UUID) -> dict:
        """Process check-in for an attendee.

        Returns a dict with check-in result including seat info.

        Raises:
            AttendeeNotFoundError: If attendee doesn't exist.
            InvalidStateTransitionError: If attendee can't check in (cancelled, etc).
        """
        attendee = await self._attendee_repo.get_by_id(attendee_id)
        if attendee is None:
            raise AttendeeNotFoundError(f"Attendee {attendee_id} not found")

        if attendee.status == "cancelled":
            raise InvalidStateTransitionError(
                f"Cancelled attendee {attendee.name} cannot check in"
            )
        if attendee.status == "checked_in":
            # Idempotent — already checked in, return current info
            seat = await self._seat_repo.get_by_attendee(attendee_id)
            return {
                "attendee_id": str(attendee.id),
                "name": attendee.name,
                "already_checked_in": True,
                "seat_label": seat.label if seat else None,
                "seat_row": seat.row_num if seat else None,
                "seat_col": seat.col_num if seat else None,
            }

        # Update status to checked_in
        await self._attendee_repo.update(attendee.id, status="checked_in")

        # Find assigned seat
        seat = await self._seat_repo.get_by_attendee(attendee_id)

        return {
            "attendee_id": str(attendee.id),
            "name": attendee.name,
            "already_checked_in": False,
            "seat_label": seat.label if seat else None,
            "seat_row": seat.row_num if seat else None,
            "seat_col": seat.col_num if seat else None,
        }

    async def checkin_by_name(
        self, event_id: uuid.UUID, name: str
    ) -> dict | list[dict]:
        """Check in by name within an event.

        Returns check-in result if unique match, or list of candidates if ambiguous.
        """
        matches = await self._attendee_repo.fuzzy_match_by_name(event_id, name)

        if not matches:
            raise AttendeeNotFoundError(
                f"No attendee matching '{name}' found in this event"
            )

        if len(matches) == 1:
            return await self.checkin(matches[0].id)

        # Ambiguous — return candidates for clarification
        return [
            {
                "attendee_id": str(a.id),
                "name": a.name,
                "title": a.title,
                "organization": a.organization,
            }
            for a in matches
        ]

    async def get_checkin_stats(self, event_id: uuid.UUID) -> dict:
        """Get check-in statistics for an event."""
        attendees = await self._attendee_repo.get_by_event(event_id)
        total = len(attendees)
        checked_in = sum(1 for a in attendees if a.status == "checked_in")
        return {
            "total": total,
            "checked_in": checked_in,
            "remaining": total - checked_in,
            "rate": round(checked_in / total * 100, 1) if total > 0 else 0,
        }
