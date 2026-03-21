"""Pydantic schemas for VenueArea API."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Optional

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    pass


class VenueAreaCreate(BaseModel):
    """Request body for creating a venue area."""

    name: str = Field(..., max_length=100)
    layout_type: str = Field(
        "grid",
        pattern=r"^(grid|theater|classroom|roundtable|banquet|u_shape)$",
    )
    rows: int = Field(0, ge=0)
    cols: int = Field(0, ge=0)
    display_order: int = 0
    offset_x: float = 0.0
    offset_y: float = 0.0
    stage_label: Optional[str] = Field(None, max_length=50)


class VenueAreaUpdate(BaseModel):
    """Request body for updating a venue area."""

    name: Optional[str] = Field(None, max_length=100)
    layout_type: Optional[str] = Field(
        None,
        pattern=r"^(grid|theater|classroom|roundtable|banquet|u_shape)$",
    )
    rows: Optional[int] = Field(None, ge=0)
    cols: Optional[int] = Field(None, ge=0)
    display_order: Optional[int] = None
    offset_x: Optional[float] = None
    offset_y: Optional[float] = None
    stage_label: Optional[str] = Field(None, max_length=50)


class VenueAreaResponse(BaseModel):
    """Response body for venue area data."""

    model_config = {"from_attributes": True}

    id: uuid.UUID
    event_id: uuid.UUID
    name: str
    layout_type: str
    rows: int
    cols: int
    display_order: int
    offset_x: float
    offset_y: float
    stage_label: Optional[str] = None
    seat_count: int = 0


class VenueAreaWithSeats(VenueAreaResponse):
    """Area response including its seats."""

    seats: list["SeatResponse"] = []

    @classmethod
    def model_rebuild_with_seats(cls) -> None:
        from app.schemas.seat import SeatResponse  # noqa: F811
        cls.model_rebuild()


# Deferred rebuild to resolve forward reference
from app.schemas.seat import SeatResponse  # noqa: E402, F401
VenueAreaWithSeats.model_rebuild()
