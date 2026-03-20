"""Seat assignment algorithms — pure functions, no DB, no IO.

All functions take plain dicts (not ORM objects) and return assignment lists.
The calling agent is responsible for fetching data from services and passing it in.
"""

import random
from typing import Any


def assign_seats_random(
    attendees: list[dict[str, Any]],
    seats: list[dict[str, Any]],
) -> list[dict[str, str]]:
    """Random assignment using Fisher-Yates shuffle.

    Args:
        attendees: List of attendee dicts with at least 'id' key.
        seats: List of seat dicts with at least 'id' key.

    Returns:
        List of {attendee_id, seat_id} assignment dicts.

    Raises:
        ValueError: If more attendees than available seats.
    """
    if len(attendees) > len(seats):
        raise ValueError(
            f"Not enough seats: {len(attendees)} attendees, {len(seats)} seats"
        )
    if not attendees:
        return []

    shuffled_seats = seats.copy()
    random.shuffle(shuffled_seats)

    return [
        {"attendee_id": att["id"], "seat_id": shuffled_seats[i]["id"]}
        for i, att in enumerate(attendees)
    ]


def assign_seats_vip_first(
    attendees: list[dict[str, Any]],
    seats: list[dict[str, Any]],
    vip_roles: tuple[str, ...] = ("vip", "speaker"),
) -> list[dict[str, str]]:
    """VIP-priority assignment: VIPs get front-row center seats first.

    Seats are scored by priority: lower row_num is better, center col is better.
    VIP attendees get the best seats, then remaining attendees fill the rest.

    Args:
        attendees: List of attendee dicts with 'id' and 'role' keys.
        seats: List of seat dicts with 'id', 'row_num', 'col_num' keys.
        vip_roles: Tuple of role strings considered VIP.

    Returns:
        List of {attendee_id, seat_id} assignment dicts.

    Raises:
        ValueError: If more attendees than available seats.
    """
    if len(attendees) > len(seats):
        raise ValueError(
            f"Not enough seats: {len(attendees)} attendees, {len(seats)} seats"
        )
    if not attendees:
        return []

    # Sort seats by priority: front row first, then center column
    max_col = max(s["col_num"] for s in seats) if seats else 1
    center = (max_col + 1) / 2

    sorted_seats = sorted(
        seats,
        key=lambda s: (s["row_num"], abs(s["col_num"] - center)),
    )

    # Split into VIPs and non-VIPs
    vips = [a for a in attendees if a.get("role") in vip_roles]
    non_vips = [a for a in attendees if a.get("role") not in vip_roles]

    assignments = []
    seat_idx = 0

    for att in vips + non_vips:
        assignments.append({
            "attendee_id": att["id"],
            "seat_id": sorted_seats[seat_idx]["id"],
        })
        seat_idx += 1

    return assignments


def assign_seats_by_department(
    attendees: list[dict[str, Any]],
    seats: list[dict[str, Any]],
) -> list[dict[str, str]]:
    """Group attendees by department, assign adjacent seats per group.

    Same-department attendees sit in consecutive seats (row-major order).

    Args:
        attendees: List of attendee dicts with 'id' and 'department' keys.
        seats: List of seat dicts with 'id', 'row_num', 'col_num' keys.

    Returns:
        List of {attendee_id, seat_id} assignment dicts.

    Raises:
        ValueError: If more attendees than available seats.
    """
    if len(attendees) > len(seats):
        raise ValueError(
            f"Not enough seats: {len(attendees)} attendees, {len(seats)} seats"
        )
    if not attendees:
        return []

    # Sort seats in row-major order
    sorted_seats = sorted(seats, key=lambda s: (s["row_num"], s["col_num"]))

    # Group attendees by department, keep groups together
    dept_groups: dict[str, list[dict]] = {}
    for att in attendees:
        dept = att.get("department") or "未分组"
        dept_groups.setdefault(dept, []).append(att)

    # Flatten groups into ordered list
    ordered_attendees = []
    for dept_members in dept_groups.values():
        ordered_attendees.extend(dept_members)

    return [
        {"attendee_id": att["id"], "seat_id": sorted_seats[i]["id"]}
        for i, att in enumerate(ordered_attendees)
    ]


def generate_seat_labels(
    rows: int, cols: int, style: str = "alpha"
) -> list[dict[str, Any]]:
    """Generate seat label metadata for a venue grid.

    Args:
        rows: Number of rows.
        cols: Number of columns.
        style: 'alpha' (A1, A2...) or 'numeric' (1-1, 1-2...).

    Returns:
        List of {row_num, col_num, label} dicts.
    """
    labels = []
    for r in range(1, rows + 1):
        for c in range(1, cols + 1):
            if style == "alpha":
                label = f"{chr(64 + r)}{c}"
            else:
                label = f"{r}-{c}"
            labels.append({"row_num": r, "col_num": c, "label": label})
    return labels
