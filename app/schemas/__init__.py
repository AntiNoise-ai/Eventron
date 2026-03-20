"""Pydantic request/response schemas."""

from app.schemas.approval import ApprovalCreate, ApprovalDecision, ApprovalResponse
from app.schemas.attendee import AttendeeCreate, AttendeeResponse, AttendeeUpdate
from app.schemas.event import EventCreate, EventResponse, EventUpdate
from app.schemas.seat import AutoAssignRequest, SeatCreate, SeatResponse, SeatUpdate

__all__ = [
    "EventCreate",
    "EventUpdate",
    "EventResponse",
    "AttendeeCreate",
    "AttendeeUpdate",
    "AttendeeResponse",
    "SeatCreate",
    "SeatUpdate",
    "SeatResponse",
    "AutoAssignRequest",
    "ApprovalCreate",
    "ApprovalDecision",
    "ApprovalResponse",
]
