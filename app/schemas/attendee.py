"""Pydantic schemas for Attendee API."""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class AttendeeCreate(BaseModel):
    """Request body for adding an attendee."""

    name: str = Field(..., max_length=100)
    title: Optional[str] = Field(None, max_length=200)
    organization: Optional[str] = Field(None, max_length=200)
    department: Optional[str] = Field(None, max_length=100)
    role: str = Field("attendee", pattern=r"^(attendee|vip|speaker|organizer|staff)$")
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=200)
    attrs: dict = Field(default_factory=dict)


class AttendeeUpdate(BaseModel):
    """Request body for partial attendee update."""

    name: Optional[str] = Field(None, max_length=100)
    title: Optional[str] = Field(None, max_length=200)
    organization: Optional[str] = Field(None, max_length=200)
    department: Optional[str] = Field(None, max_length=100)
    role: Optional[str] = Field(None, pattern=r"^(attendee|vip|speaker|organizer|staff)$")
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=200)
    status: Optional[str] = Field(
        None, pattern=r"^(pending|confirmed|checked_in|absent|cancelled)$"
    )
    attrs: Optional[dict] = None


class AttendeeResponse(BaseModel):
    """Response body for attendee data."""

    model_config = {"from_attributes": True}

    id: uuid.UUID
    event_id: uuid.UUID
    name: str
    title: Optional[str]
    organization: Optional[str]
    department: Optional[str]
    role: str
    phone: Optional[str]
    email: Optional[str]
    attrs: dict
    status: str
    wecom_user_id: Optional[str]
    lark_user_id: Optional[str]
    created_at: datetime
    updated_at: datetime
