"""Attendee API routes — thin layer, delegates to services."""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from app.deps import get_attendee_service, get_checkin_service
from app.schemas.attendee import (
    AttendeeCreate,
    AttendeeResponse,
    AttendeeUpdate,
)
from app.services.attendee_service import AttendeeService
from app.services.checkin_service import CheckinService
from app.services.exceptions import AttendeeNotFoundError, InvalidStateTransitionError

router = APIRouter()


@router.post("/{event_id}/attendees", response_model=AttendeeResponse, status_code=201)
async def create_attendee(
    event_id: uuid.UUID,
    body: AttendeeCreate,
    svc: AttendeeService = Depends(get_attendee_service),
):
    """Create a new attendee for an event."""
    attendee = await svc.create_attendee(event_id, **body.model_dump())
    return AttendeeResponse.model_validate(attendee)


@router.get("/{event_id}/attendees", response_model=list[AttendeeResponse])
async def list_attendees(
    event_id: uuid.UUID,
    role: Optional[str] = None,
    status: Optional[str] = None,
    svc: AttendeeService = Depends(get_attendee_service),
):
    """List attendees for an event, optionally filtered by role or status."""
    attendees = await svc.list_attendees_for_event(
        event_id, role=role, status=status
    )
    return [AttendeeResponse.model_validate(a) for a in attendees]


@router.get("/{event_id}/attendees/{attendee_id}", response_model=AttendeeResponse)
async def get_attendee(
    event_id: uuid.UUID,
    attendee_id: uuid.UUID,
    svc: AttendeeService = Depends(get_attendee_service),
):
    """Get a single attendee by ID."""
    try:
        attendee = await svc.get_attendee(attendee_id)
    except AttendeeNotFoundError:
        raise HTTPException(status_code=404, detail="Attendee not found")
    return AttendeeResponse.model_validate(attendee)


@router.patch("/{event_id}/attendees/{attendee_id}", response_model=AttendeeResponse)
async def update_attendee(
    event_id: uuid.UUID,
    attendee_id: uuid.UUID,
    body: AttendeeUpdate,
    svc: AttendeeService = Depends(get_attendee_service),
):
    """Partial update of an attendee."""
    try:
        attendee = await svc.update_attendee(
            attendee_id, **body.model_dump(exclude_unset=True)
        )
    except AttendeeNotFoundError:
        raise HTTPException(status_code=404, detail="Attendee not found")
    return AttendeeResponse.model_validate(attendee)


@router.delete("/{event_id}/attendees/{attendee_id}", status_code=204)
async def delete_attendee(
    event_id: uuid.UUID,
    attendee_id: uuid.UUID,
    svc: AttendeeService = Depends(get_attendee_service),
):
    """Delete an attendee."""
    try:
        await svc.delete_attendee(attendee_id)
    except AttendeeNotFoundError:
        raise HTTPException(status_code=404, detail="Attendee not found")


@router.post("/{event_id}/attendees/{attendee_id}/checkin")
async def checkin_attendee(
    event_id: uuid.UUID,
    attendee_id: uuid.UUID,
    svc: CheckinService = Depends(get_checkin_service),
):
    """Check in an attendee by ID."""
    try:
        result = await svc.checkin(attendee_id)
    except AttendeeNotFoundError:
        raise HTTPException(status_code=404, detail="Attendee not found")
    except InvalidStateTransitionError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return result


@router.get("/{event_id}/checkin-stats")
async def checkin_stats(
    event_id: uuid.UUID,
    svc: CheckinService = Depends(get_checkin_service),
):
    """Get check-in statistics for an event."""
    return await svc.get_checkin_stats(event_id)
