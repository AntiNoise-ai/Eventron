"""Pydantic schemas for ApprovalRequest API."""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ApprovalCreate(BaseModel):
    """Request body for creating an approval request."""

    requester_id: uuid.UUID
    change_type: str = Field(
        ..., pattern=r"^(swap|add_person|remove|reassign|bulk_change)$"
    )
    change_detail: dict


class ApprovalDecision(BaseModel):
    """Request body for approving or rejecting."""

    status: str = Field(..., pattern=r"^(approved|rejected)$")
    reviewer_id: str
    review_note: Optional[str] = None


class ApprovalResponse(BaseModel):
    """Response body for approval data."""

    model_config = {"from_attributes": True}

    id: uuid.UUID
    event_id: uuid.UUID
    requester_id: uuid.UUID
    change_type: str
    change_detail: dict
    status: str
    reviewer_id: Optional[str]
    review_note: Optional[str]
    lg_thread_id: Optional[str]
    created_at: datetime
    updated_at: datetime
