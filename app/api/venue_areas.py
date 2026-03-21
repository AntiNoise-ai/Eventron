"""Venue area CRUD + seat layout generation per area."""

import uuid

from fastapi import APIRouter, Depends, HTTPException

from app.deps import get_event_service, get_seating_service
from app.schemas.seat import SeatResponse
from app.schemas.venue_area import (
    VenueAreaCreate,
    VenueAreaResponse,
    VenueAreaUpdate,
)
from app.services.event_service import EventService
from app.services.exceptions import EventNotFoundError
from app.services.seating_service import SeatingService

router = APIRouter()


# ── CRUD ──────────────────────────────────────────────────────

@router.get(
    "/{event_id}/areas",
    response_model=list[VenueAreaResponse],
)
async def list_areas(
    event_id: uuid.UUID,
    svc: SeatingService = Depends(get_seating_service),
):
    """List all venue areas for an event."""
    areas = await svc.list_areas(event_id)
    results = []
    for a in areas:
        resp = VenueAreaResponse.model_validate(a)
        resp.seat_count = len(a.seats) if hasattr(a, "seats") else 0
        results.append(resp)
    return results


@router.post(
    "/{event_id}/areas",
    response_model=VenueAreaResponse,
    status_code=201,
)
async def create_area(
    event_id: uuid.UUID,
    body: VenueAreaCreate,
    event_svc: EventService = Depends(get_event_service),
    svc: SeatingService = Depends(get_seating_service),
):
    """Create a new venue area."""
    try:
        await event_svc.get_event(event_id)
    except EventNotFoundError:
        raise HTTPException(status_code=404, detail="Event not found")

    area = await svc.create_area(event_id, **body.model_dump())
    return VenueAreaResponse.model_validate(area)


@router.patch(
    "/{event_id}/areas/{area_id}",
    response_model=VenueAreaResponse,
)
async def update_area(
    event_id: uuid.UUID,
    area_id: uuid.UUID,
    body: VenueAreaUpdate,
    svc: SeatingService = Depends(get_seating_service),
):
    """Update a venue area."""
    area = await svc.update_area(area_id, **body.model_dump(exclude_unset=True))
    if not area:
        raise HTTPException(status_code=404, detail="Area not found")
    return VenueAreaResponse.model_validate(area)


@router.delete("/{event_id}/areas/{area_id}", status_code=204)
async def delete_area(
    event_id: uuid.UUID,
    area_id: uuid.UUID,
    svc: SeatingService = Depends(get_seating_service),
):
    """Delete a venue area and all its seats."""
    deleted = await svc.delete_area(area_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Area not found")


# ── Generate layout within an area ────────────────────────────

@router.post(
    "/{event_id}/areas/{area_id}/layout",
    response_model=list[SeatResponse],
)
async def generate_area_layout(
    event_id: uuid.UUID,
    area_id: uuid.UUID,
    svc: SeatingService = Depends(get_seating_service),
):
    """Generate seat layout within an area using the area's layout_type,
    rows, and cols. Replaces existing seats in this area.
    """
    seats = await svc.generate_area_layout(event_id, area_id)
    return [SeatResponse.model_validate(s) for s in seats]
