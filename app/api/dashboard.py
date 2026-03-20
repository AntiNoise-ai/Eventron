"""Dashboard API route — aggregated event stats for organizer portal."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException

from app.api.auth import get_current_organizer
from app.deps import get_dashboard_service
from app.schemas.dashboard import DashboardStats
from app.services.dashboard_service import DashboardService
from app.services.exceptions import EventNotFoundError

router = APIRouter()


@router.get("/{event_id}", response_model=DashboardStats)
async def event_dashboard(
    event_id: uuid.UUID,
    organizer=Depends(get_current_organizer),
    svc: DashboardService = Depends(get_dashboard_service),
):
    """Get aggregated dashboard stats for an event."""
    try:
        return await svc.get_event_stats(event_id)
    except EventNotFoundError:
        raise HTTPException(status_code=404, detail="Event not found")
