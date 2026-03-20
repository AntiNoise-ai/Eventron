"""Pydantic schemas for dashboard API."""

from pydantic import BaseModel


class DashboardStats(BaseModel):
    """Aggregated event dashboard data."""

    event_name: str
    event_status: str
    total_attendees: int
    checked_in_count: int
    pending_count: int
    confirmed_count: int
    absent_count: int
    cancelled_count: int
    checkin_rate: float
    seats_total: int
    seats_occupied: int
    seats_available: int
    seat_utilization_rate: float
    pending_approvals: int
    vip_count: int
    speaker_count: int
    vip_checked_in: int
