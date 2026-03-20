"""Unit tests for seating_engine — pure function tests, no DB."""

import pytest

from tests.factories import make_attendee, make_seat_grid
from tools.seating_engine import (
    assign_seats_by_department,
    assign_seats_random,
    assign_seats_vip_first,
    generate_seat_labels,
)


class TestAssignSeatsRandom:
    """Tests for random seat assignment."""

    def test_happy_path_all_assigned(self):
        """All attendees get a seat."""
        attendees = [make_attendee(id=f"a{i}") for i in range(5)]
        seats = make_seat_grid(2, 3)  # 6 seats
        result = assign_seats_random(attendees, seats)
        assert len(result) == 5
        assert all("attendee_id" in r and "seat_id" in r for r in result)

    def test_empty_attendees_returns_empty(self):
        """No attendees → empty result."""
        seats = make_seat_grid(2, 2)
        result = assign_seats_random([], seats)
        assert result == []

    def test_more_attendees_than_seats_raises(self):
        """Should raise ValueError when overflow."""
        attendees = [make_attendee(id=f"a{i}") for i in range(10)]
        seats = make_seat_grid(1, 3)  # 3 seats
        with pytest.raises(ValueError, match="Not enough seats"):
            assign_seats_random(attendees, seats)

    def test_exact_fit(self):
        """Exactly as many attendees as seats."""
        attendees = [make_attendee(id=f"a{i}") for i in range(4)]
        seats = make_seat_grid(2, 2)
        result = assign_seats_random(attendees, seats)
        assert len(result) == 4
        # All seat IDs should be unique
        seat_ids = [r["seat_id"] for r in result]
        assert len(set(seat_ids)) == 4

    def test_no_duplicate_seat_assignments(self):
        """Each seat is assigned to at most one attendee."""
        attendees = [make_attendee(id=f"a{i}") for i in range(6)]
        seats = make_seat_grid(3, 3)  # 9 seats
        result = assign_seats_random(attendees, seats)
        seat_ids = [r["seat_id"] for r in result]
        assert len(seat_ids) == len(set(seat_ids))


class TestAssignSeatsVipFirst:
    """Tests for VIP-priority assignment."""

    def test_vip_gets_front_row_center(self):
        """VIP should get the best seats (front row, center)."""
        attendees = [
            make_attendee(id="vip1", role="vip"),
            make_attendee(id="reg1", role="attendee"),
            make_attendee(id="reg2", role="attendee"),
        ]
        seats = make_seat_grid(3, 3)  # 9 seats
        result = assign_seats_vip_first(attendees, seats)

        # VIP should be first in assignments (gets best seat)
        assert result[0]["attendee_id"] == "vip1"

    def test_speaker_treated_as_vip(self):
        """Speaker role is VIP by default."""
        attendees = [
            make_attendee(id="spk1", role="speaker"),
            make_attendee(id="reg1", role="attendee"),
        ]
        seats = make_seat_grid(2, 2)
        result = assign_seats_vip_first(attendees, seats)
        assert result[0]["attendee_id"] == "spk1"

    def test_all_vip_fills_front_to_back(self):
        """When everyone is VIP, seats fill front-to-back."""
        attendees = [make_attendee(id=f"v{i}", role="vip") for i in range(4)]
        seats = make_seat_grid(2, 2)
        result = assign_seats_vip_first(attendees, seats)
        assert len(result) == 4

    def test_empty_attendees(self):
        result = assign_seats_vip_first([], make_seat_grid(2, 2))
        assert result == []

    def test_overflow_raises(self):
        attendees = [make_attendee(id=f"a{i}") for i in range(5)]
        seats = make_seat_grid(1, 2)
        with pytest.raises(ValueError):
            assign_seats_vip_first(attendees, seats)

    def test_custom_vip_roles(self):
        """Custom vip_roles parameter is respected."""
        attendees = [
            make_attendee(id="org1", role="organizer"),
            make_attendee(id="reg1", role="attendee"),
        ]
        seats = make_seat_grid(2, 2)
        result = assign_seats_vip_first(
            attendees, seats, vip_roles=("organizer",)
        )
        assert result[0]["attendee_id"] == "org1"


class TestAssignSeatsByDepartment:
    """Tests for department-grouped assignment."""

    def test_same_department_sits_together(self):
        """Members of the same department should be in consecutive seats."""
        attendees = [
            make_attendee(id="a1", department="Sales"),
            make_attendee(id="a2", department="Engineering"),
            make_attendee(id="a3", department="Sales"),
        ]
        seats = make_seat_grid(1, 3)
        result = assign_seats_by_department(attendees, seats)

        # Sales people (a1, a3) should be adjacent
        sales_indices = [
            i for i, r in enumerate(result) if r["attendee_id"] in ("a1", "a3")
        ]
        assert abs(sales_indices[0] - sales_indices[1]) == 1

    def test_empty_attendees(self):
        result = assign_seats_by_department([], make_seat_grid(2, 2))
        assert result == []

    def test_no_department_falls_to_default_group(self):
        """Attendees without department go to a default group."""
        attendees = [
            make_attendee(id="a1", department=None),
            make_attendee(id="a2", department=None),
        ]
        seats = make_seat_grid(1, 2)
        result = assign_seats_by_department(attendees, seats)
        assert len(result) == 2


class TestGenerateSeatLabels:
    """Tests for seat label generation."""

    def test_alpha_labels(self):
        labels = generate_seat_labels(2, 3, style="alpha")
        assert len(labels) == 6
        assert labels[0] == {"row_num": 1, "col_num": 1, "label": "A1"}
        assert labels[5] == {"row_num": 2, "col_num": 3, "label": "B3"}

    def test_numeric_labels(self):
        labels = generate_seat_labels(2, 2, style="numeric")
        assert labels[0]["label"] == "1-1"
        assert labels[3]["label"] == "2-2"

    def test_single_seat(self):
        labels = generate_seat_labels(1, 1)
        assert len(labels) == 1
        assert labels[0]["label"] == "A1"
