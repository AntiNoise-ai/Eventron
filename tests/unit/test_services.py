"""Unit tests for service layer — mock repositories, test business rules."""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.checkin_service import CheckinService
from app.services.event_service import EventService
from app.services.exceptions import (
    AttendeeNotFoundError,
    EventNotFoundError,
    InvalidStateTransitionError,
    SeatNotAvailableError,
)
from app.services.seating_service import SeatingService


# ── Helpers ──────────────────────────────────────────────────

def _mock_event(**overrides):
    """Create a mock Event ORM object."""
    ev = MagicMock()
    ev.id = overrides.get("id", uuid.uuid4())
    ev.name = overrides.get("name", "Test Event")
    ev.status = overrides.get("status", "draft")
    ev.venue_rows = overrides.get("venue_rows", 5)
    ev.venue_cols = overrides.get("venue_cols", 5)
    return ev


def _mock_attendee(**overrides):
    """Create a mock Attendee ORM object."""
    att = MagicMock()
    att.id = overrides.get("id", uuid.uuid4())
    att.name = overrides.get("name", "张三")
    att.role = overrides.get("role", "attendee")
    att.department = overrides.get("department", "Engineering")
    att.status = overrides.get("status", "confirmed")
    att.title = overrides.get("title", "工程师")
    att.organization = overrides.get("organization", "Acme")
    return att


def _mock_seat(**overrides):
    """Create a mock Seat ORM object."""
    seat = MagicMock()
    seat.id = overrides.get("id", uuid.uuid4())
    seat.row_num = overrides.get("row_num", 1)
    seat.col_num = overrides.get("col_num", 1)
    seat.label = overrides.get("label", "A1")
    seat.seat_type = overrides.get("seat_type", "normal")
    seat.attendee_id = overrides.get("attendee_id", None)
    return seat


# ── EventService Tests ───────────────────────────────────────

class TestEventService:
    """Business rules for event lifecycle."""

    @pytest.fixture
    def repo(self):
        return AsyncMock()

    @pytest.fixture
    def svc(self, repo):
        return EventService(repo)

    async def test_create_defaults_to_draft(self, svc, repo):
        repo.create.return_value = _mock_event(status="draft")
        await svc.create_event(name="Test")
        repo.create.assert_called_once()
        kwargs = repo.create.call_args.kwargs
        assert kwargs["status"] == "draft"

    async def test_get_event_not_found_raises(self, svc, repo):
        repo.get_by_id.return_value = None
        with pytest.raises(EventNotFoundError):
            await svc.get_event(uuid.uuid4())

    async def test_valid_transition_draft_to_active(self, svc, repo):
        repo.get_by_id.return_value = _mock_event(status="draft")
        repo.update.return_value = _mock_event(status="active")
        result = await svc.activate_event(uuid.uuid4())
        assert result.status == "active"

    async def test_invalid_transition_completed_to_active(self, svc, repo):
        repo.get_by_id.return_value = _mock_event(status="completed")
        with pytest.raises(InvalidStateTransitionError):
            await svc.update_event(uuid.uuid4(), status="active")

    async def test_delete_only_draft(self, svc, repo):
        repo.get_by_id.return_value = _mock_event(status="active")
        with pytest.raises(InvalidStateTransitionError, match="Only draft"):
            await svc.delete_event(uuid.uuid4())

    async def test_delete_draft_succeeds(self, svc, repo):
        repo.get_by_id.return_value = _mock_event(status="draft")
        repo.delete.return_value = True
        result = await svc.delete_event(uuid.uuid4())
        assert result is True

    async def test_cancel_from_draft(self, svc, repo):
        repo.get_by_id.return_value = _mock_event(status="draft")
        repo.update.return_value = _mock_event(status="cancelled")
        result = await svc.cancel_event(uuid.uuid4())
        assert result.status == "cancelled"


# ── SeatingService Tests ─────────────────────────────────────

class TestSeatingService:
    """Business rules for seat assignment."""

    @pytest.fixture
    def seat_repo(self):
        return AsyncMock()

    @pytest.fixture
    def att_repo(self):
        return AsyncMock()

    @pytest.fixture
    def svc(self, seat_repo, att_repo):
        return SeatingService(seat_repo, att_repo)

    async def test_assign_seat_success(self, svc, seat_repo, att_repo):
        seat = _mock_seat(attendee_id=None, seat_type="normal")
        seat_repo.get_by_id.return_value = seat
        att_repo.get_by_id.return_value = _mock_attendee()
        seat_repo.get_by_attendee.return_value = None
        seat_repo.assign_attendee.return_value = seat

        result = await svc.assign_seat(seat.id, uuid.uuid4())
        assert result is not None

    async def test_assign_occupied_seat_raises(self, svc, seat_repo, att_repo):
        seat = _mock_seat(attendee_id=uuid.uuid4())
        seat_repo.get_by_id.return_value = seat

        with pytest.raises(SeatNotAvailableError, match="already occupied"):
            await svc.assign_seat(seat.id, uuid.uuid4())

    async def test_assign_disabled_seat_raises(self, svc, seat_repo, att_repo):
        seat = _mock_seat(seat_type="disabled", attendee_id=None)
        seat_repo.get_by_id.return_value = seat

        with pytest.raises(SeatNotAvailableError, match="disabled"):
            await svc.assign_seat(seat.id, uuid.uuid4())

    async def test_assign_nonexistent_attendee_raises(self, svc, seat_repo, att_repo):
        seat = _mock_seat(attendee_id=None)
        seat_repo.get_by_id.return_value = seat
        att_repo.get_by_id.return_value = None

        with pytest.raises(AttendeeNotFoundError):
            await svc.assign_seat(seat.id, uuid.uuid4())

    async def test_auto_assign_random(self, svc, seat_repo, att_repo):
        """Auto-assign with random strategy."""
        att_repo.get_by_event.return_value = [
            _mock_attendee(id=uuid.uuid4()),
            _mock_attendee(id=uuid.uuid4()),
        ]
        seat_repo.get_available_seats.return_value = [
            _mock_seat(id=uuid.uuid4(), row_num=1, col_num=1),
            _mock_seat(id=uuid.uuid4(), row_num=1, col_num=2),
            _mock_seat(id=uuid.uuid4(), row_num=2, col_num=1),
        ]
        seat_repo.assign_attendee.return_value = _mock_seat()

        result = await svc.auto_assign(uuid.uuid4(), strategy="random")
        assert len(result) == 2
        assert seat_repo.assign_attendee.call_count == 2


# ── CheckinService Tests ─────────────────────────────────────

class TestCheckinService:
    """Business rules for check-in."""

    @pytest.fixture
    def att_repo(self):
        return AsyncMock()

    @pytest.fixture
    def seat_repo(self):
        return AsyncMock()

    @pytest.fixture
    def svc(self, att_repo, seat_repo):
        return CheckinService(att_repo, seat_repo)

    async def test_checkin_success(self, svc, att_repo, seat_repo):
        att = _mock_attendee(status="confirmed")
        att_repo.get_by_id.return_value = att
        seat_repo.get_by_attendee.return_value = _mock_seat(label="A3")
        att_repo.update.return_value = att

        result = await svc.checkin(att.id)
        assert result["name"] == "张三"
        assert result["seat_label"] == "A3"
        assert result["already_checked_in"] is False

    async def test_checkin_idempotent(self, svc, att_repo, seat_repo):
        """Checking in twice returns success without error."""
        att = _mock_attendee(status="checked_in")
        att_repo.get_by_id.return_value = att
        seat_repo.get_by_attendee.return_value = _mock_seat(label="B2")

        result = await svc.checkin(att.id)
        assert result["already_checked_in"] is True

    async def test_checkin_cancelled_raises(self, svc, att_repo, seat_repo):
        att = _mock_attendee(status="cancelled")
        att_repo.get_by_id.return_value = att

        with pytest.raises(InvalidStateTransitionError, match="Cancelled"):
            await svc.checkin(att.id)

    async def test_checkin_not_found_raises(self, svc, att_repo, seat_repo):
        att_repo.get_by_id.return_value = None
        with pytest.raises(AttendeeNotFoundError):
            await svc.checkin(uuid.uuid4())

    async def test_checkin_stats(self, svc, att_repo, seat_repo):
        att_repo.get_by_event.return_value = [
            _mock_attendee(status="checked_in"),
            _mock_attendee(status="confirmed"),
            _mock_attendee(status="checked_in"),
        ]
        stats = await svc.get_checkin_stats(uuid.uuid4())
        assert stats["total"] == 3
        assert stats["checked_in"] == 2
        assert stats["rate"] == 66.7

    async def test_checkin_by_name_unique(self, svc, att_repo, seat_repo):
        att = _mock_attendee(status="confirmed")
        att_repo.fuzzy_match_by_name.return_value = [att]
        att_repo.get_by_id.return_value = att
        seat_repo.get_by_attendee.return_value = _mock_seat(label="C1")
        att_repo.update.return_value = att

        result = await svc.checkin_by_name(uuid.uuid4(), "张三")
        assert isinstance(result, dict)
        assert result["name"] == "张三"

    async def test_checkin_by_name_ambiguous(self, svc, att_repo, seat_repo):
        att_repo.fuzzy_match_by_name.return_value = [
            _mock_attendee(name="张三丰"),
            _mock_attendee(name="张三"),
        ]
        result = await svc.checkin_by_name(uuid.uuid4(), "张三")
        assert isinstance(result, list)
        assert len(result) == 2
