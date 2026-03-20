"""Export API routes — Excel download for attendees and seat maps."""

import uuid
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from app.deps import get_attendee_service, get_event_service, get_seating_service
from app.services.attendee_service import AttendeeService
from app.services.event_service import EventService
from app.services.exceptions import EventNotFoundError
from app.services.seating_service import SeatingService
from tools.excel_io import export_attendees_to_excel, export_seatmap_to_excel

router = APIRouter()


def _make_content_disposition(filename: str) -> str:
    """Build Content-Disposition with RFC 5987 UTF-8 encoding.

    Handles non-ASCII filenames (Chinese, etc.) correctly across
    all browsers.
    """
    ascii_name = filename.encode("ascii", errors="replace").decode()
    encoded = quote(filename, safe="")
    return (
        f'attachment; filename="{ascii_name}"; '
        f"filename*=UTF-8''{encoded}"
    )


@router.get("/events/{event_id}/export/attendees")
async def export_attendees(
    event_id: uuid.UUID,
    att_svc: AttendeeService = Depends(get_attendee_service),
    seat_svc: SeatingService = Depends(get_seating_service),
    event_svc: EventService = Depends(get_event_service),
):
    """Export attendees as Excel, or a blank import template if none exist."""
    try:
        event = await event_svc.get_event(event_id)
    except EventNotFoundError:
        raise HTTPException(status_code=404, detail="Event not found")

    attendees = await att_svc.list_attendees_for_event(event_id)
    seats = await seat_svc.get_seats(event_id)

    att_dicts = [
        {
            "id": str(a.id),
            "name": a.name,
            "title": a.title,
            "organization": a.organization,
            "department": a.department,
            "role": a.role,
            "phone": a.phone,
            "email": a.email,
            "status": a.status,
        }
        for a in attendees
    ]
    seat_dicts = [
        {
            "attendee_id": str(s.attendee_id) if s.attendee_id else None,
            "label": s.label,
            "row_num": s.row_num,
            "col_num": s.col_num,
        }
        for s in seats
    ]

    # No attendees → generate import template with example row
    if not att_dicts:
        att_dicts = [
            {
                "name": "(示例) 张三",
                "title": "产品经理",
                "organization": "示例公司",
                "department": "产品部",
                "role": "attendee",
                "phone": "13800138000",
                "email": "zhangsan@example.com",
                "status": "pending",
            }
        ]
        filename = f"{event.name}_导入模板.xlsx"
    else:
        filename = f"{event.name}_参会人员.xlsx"

    xlsx_bytes = export_attendees_to_excel(att_dicts, seat_dicts)

    return Response(
        content=xlsx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": _make_content_disposition(filename)},
    )


@router.get("/events/{event_id}/export/seatmap")
async def export_seatmap(
    event_id: uuid.UUID,
    seat_svc: SeatingService = Depends(get_seating_service),
    event_svc: EventService = Depends(get_event_service),
    att_svc: AttendeeService = Depends(get_attendee_service),
):
    """Export seat map as Excel file."""
    try:
        event = await event_svc.get_event(event_id)
    except EventNotFoundError:
        raise HTTPException(status_code=404, detail="Event not found")

    seats = await seat_svc.get_seats(event_id)

    if not seats:
        raise HTTPException(
            status_code=404,
            detail="该活动还没有座位，请先生成座位网格",
        )

    attendees = await att_svc.list_attendees_for_event(event_id)
    att_lookup = {str(a.id): a.name for a in attendees}

    seat_dicts = [
        {
            "row_num": s.row_num,
            "col_num": s.col_num,
            "seat_type": s.seat_type,
            "attendee_name": att_lookup.get(str(s.attendee_id), ""),
        }
        for s in seats
    ]

    xlsx_bytes = export_seatmap_to_excel(
        seat_dicts, event.venue_rows, event.venue_cols
    )
    filename = f"{event.name}_座位图.xlsx"

    return Response(
        content=xlsx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": _make_content_disposition(filename)},
    )
