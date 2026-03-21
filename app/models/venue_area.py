"""VenueArea ORM model — a distinct spatial region within an event venue."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDMixin

if TYPE_CHECKING:
    from app.models.event import Event
    from app.models.seat import Seat


class VenueArea(Base, UUIDMixin):
    """A distinct area in an event venue (e.g. 观众席, 贵宾区, 贵宾室).

    Each event can have multiple areas. Seats belong to one area.
    Areas are rendered as separate groups on the seat map canvas,
    offset by (offset_x, offset_y) from the global origin.
    """

    __tablename__ = "venue_areas"

    event_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("events.id"))
    name: Mapped[str] = mapped_column(String(100))
    layout_type: Mapped[str] = mapped_column(String(30), default="grid")
    # grid | theater | classroom | roundtable | banquet | u_shape
    rows: Mapped[int] = mapped_column(Integer, default=0)
    cols: Mapped[int] = mapped_column(Integer, default=0)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    # Canvas offset for multi-area rendering
    offset_x: Mapped[float] = mapped_column(Float, default=0.0)
    offset_y: Mapped[float] = mapped_column(Float, default=0.0)
    # Optional label rendered at the top of the area (e.g. "舞台", "背景牆")
    stage_label: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )

    # Relationships
    event: Mapped[Event] = relationship(back_populates="areas")
    seats: Mapped[list[Seat]] = relationship(
        back_populates="area", cascade="all, delete-orphan"
    )
