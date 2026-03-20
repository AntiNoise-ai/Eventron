"""Seat API routes — thin layer, delegates to SeatingService."""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from app.deps import get_seating_service
from app.schemas.seat import AutoAssignRequest, SeatResponse
from app.services.exceptions import (
    DuplicateAssignmentError,
    SeatNotAvailableError,
    SeatNotFoundError,
)
from app.services.seating_service import SeatingService

router = APIRouter()


@router.get("/{event_id}/seats", response_model=list[SeatResponse])
async def list_seats(
    event_id: uuid.UUID,
    svc: SeatingService = Depends(get_seating_service),
):
    """List all seats for an event."""
    seats = await svc.get_seats(event_id)
    return [SeatResponse.model_validate(s) for s in seats]


@router.post("/{event_id}/seats/grid", response_model=list[SeatResponse], status_code=201)
async def create_seat_grid(
    event_id: uuid.UUID,
    rows: int,
    cols: int,
    svc: SeatingService = Depends(get_seating_service),
):
    """Create a full seat grid for an event."""
    seats = await svc.create_venue_grid(event_id, rows, cols)
    return [SeatResponse.model_validate(s) for s in seats]


@router.post("/{event_id}/seats/auto-assign")
async def auto_assign(
    event_id: uuid.UUID,
    body: AutoAssignRequest,
    svc: SeatingService = Depends(get_seating_service),
):
    """Run auto-assignment algorithm."""
    try:
        assignments = await svc.auto_assign(
            event_id, strategy=body.strategy, vip_roles=tuple(body.vip_roles)
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return {"assignments": assignments, "count": len(assignments)}


@router.post("/{event_id}/seats/{seat_id}/assign", response_model=SeatResponse)
async def assign_seat(
    event_id: uuid.UUID,
    seat_id: uuid.UUID,
    attendee_id: uuid.UUID,
    svc: SeatingService = Depends(get_seating_service),
):
    """Manually assign an attendee to a seat."""
    try:
        seat = await svc.assign_seat(seat_id, attendee_id)
    except SeatNotFoundError:
        raise HTTPException(status_code=404, detail="Seat not found")
    except (SeatNotAvailableError, DuplicateAssignmentError) as e:
        raise HTTPException(status_code=422, detail=str(e))
    return SeatResponse.model_validate(seat)


@router.post("/{event_id}/seats/swap")
async def swap_seats(
    event_id: uuid.UUID,
    seat_a_id: uuid.UUID,
    seat_b_id: uuid.UUID,
    svc: SeatingService = Depends(get_seating_service),
):
    """Swap attendees between two seats."""
    try:
        a, b = await svc.swap_seats(seat_a_id, seat_b_id)
    except SeatNotFoundError:
        raise HTTPException(status_code=404, detail="Seat not found")
    return {
        "seat_a": SeatResponse.model_validate(a),
        "seat_b": SeatResponse.model_validate(b),
    }
