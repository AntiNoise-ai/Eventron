"""Event ORM model."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.attendee import Attendee
    from app.models.seat import Seat


class Event(Base, UUIDMixin, TimestampMixin):
    """An event with a venue layout and attendees."""

    __tablename__ = "events"

    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    event_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    location: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    venue_rows: Mapped[int] = mapped_column(Integer, default=0)
    venue_cols: Mapped[int] = mapped_column(Integer, default=0)
    layout_type: Mapped[str] = mapped_column(String(30), default="theater")
    # theater | classroom | roundtable | banquet | u_shape
    status: Mapped[str] = mapped_column(String(20), default="draft")
    # draft | active | completed | cancelled
    created_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Flexible config — JSONB
    config: Mapped[dict] = mapped_column(JSONB, default=dict)

    # Relationships
    attendees: Mapped[list[Attendee]] = relationship(
        back_populates="event", cascade="all, delete-orphan"
    )
    seats: Mapped[list[Seat]] = relationship(
        back_populates="event", cascade="all, delete-orphan"
    )
