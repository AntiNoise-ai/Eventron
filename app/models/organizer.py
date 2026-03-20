"""Organizer ORM model — separate auth entity from Attendee."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class Organizer(Base, UUIDMixin, TimestampMixin):
    """An event organizer/planner account (Web portal user).

    Completely separate from Attendee — different auth system.
    Attendees authenticate via IM binding; Organizers via email+password.
    """

    __tablename__ = "organizers"

    email: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(200))
    name: Mapped[str] = mapped_column(String(100))
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    role: Mapped[str] = mapped_column(String(20), default="member")
    # role: admin | member
    is_active: Mapped[bool] = mapped_column(default=True)
