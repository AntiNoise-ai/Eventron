"""Unit tests for Pydantic schemas — validate request/response shapes."""

import uuid

import pytest
from pydantic import ValidationError

from app.schemas.attendee import AttendeeCreate
from app.schemas.event import EventCreate, EventResponse, EventUpdate
from app.schemas.seat import AutoAssignRequest, SeatCreate


class TestEventSchemas:
    """Validation rules for event schemas."""

    def test_create_minimal(self):
        """Only name is required."""
        ev = EventCreate(name="Test Event")
        assert ev.name == "Test Event"
        assert ev.layout_type == "theater"
        assert ev.venue_rows == 0

    def test_create_full(self):
        """All fields set."""
        ev = EventCreate(
            name="Gala",
            description="Annual gala",
            venue_rows=10,
            venue_cols=5,
            layout_type="banquet",
            config={"allow_self_checkin": True},
        )
        assert ev.venue_rows == 10
        assert ev.config["allow_self_checkin"] is True

    def test_invalid_layout_type_rejected(self):
        """Unknown layout type should fail validation."""
        with pytest.raises(ValidationError):
            EventCreate(name="Bad", layout_type="stadium")

    def test_negative_rows_rejected(self):
        """Negative venue dimensions should fail."""
        with pytest.raises(ValidationError):
            EventCreate(name="Bad", venue_rows=-1)

    def test_update_partial(self):
        """Update schema allows partial fields."""
        upd = EventUpdate(name="New Name")
        assert upd.name == "New Name"
        assert upd.venue_rows is None

    def test_update_invalid_status(self):
        """Invalid status should fail."""
        with pytest.raises(ValidationError):
            EventUpdate(status="bogus")


class TestAttendeeSchemas:
    """Validation rules for attendee schemas."""

    def test_create_minimal(self):
        att = AttendeeCreate(name="张三")
        assert att.role == "attendee"
        assert att.attrs == {}

    def test_create_vip(self):
        att = AttendeeCreate(name="李四", role="vip", title="CEO")
        assert att.role == "vip"
        assert att.title == "CEO"

    def test_invalid_role_rejected(self):
        with pytest.raises(ValidationError):
            AttendeeCreate(name="Bad", role="admin")

    def test_attrs_accepts_any_dict(self):
        att = AttendeeCreate(
            name="王五",
            attrs={"dietary": "vegetarian", "language": "zh"},
        )
        assert att.attrs["dietary"] == "vegetarian"


class TestSeatSchemas:
    """Validation rules for seat schemas."""

    def test_create_basic(self):
        s = SeatCreate(row_num=1, col_num=3)
        assert s.seat_type == "normal"

    def test_create_vip(self):
        s = SeatCreate(row_num=1, col_num=1, seat_type="vip", label="VIP-01")
        assert s.label == "VIP-01"

    def test_invalid_type_rejected(self):
        with pytest.raises(ValidationError):
            SeatCreate(row_num=1, col_num=1, seat_type="throne")

    def test_zero_row_rejected(self):
        with pytest.raises(ValidationError):
            SeatCreate(row_num=0, col_num=1)

    def test_auto_assign_defaults(self):
        req = AutoAssignRequest()
        assert req.strategy == "random"
        assert "vip" in req.vip_roles

    def test_auto_assign_custom(self):
        req = AutoAssignRequest(strategy="vip_first", vip_roles=["vip"])
        assert req.strategy == "vip_first"
