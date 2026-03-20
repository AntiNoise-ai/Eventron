"""ApprovalRequest ORM model."""

from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class ApprovalRequest(Base, UUIDMixin, TimestampMixin):
    """A change request that may need human approval."""

    __tablename__ = "approval_requests"

    event_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("events.id"))
    requester_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("attendees.id"))
    change_type: Mapped[str] = mapped_column(String(30))
    # swap | add_person | remove | reassign | bulk_change
    change_detail: Mapped[dict] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    # pending | approved | rejected | expired
    reviewer_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    review_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    lg_thread_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
