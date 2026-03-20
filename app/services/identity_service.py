"""Identity resolution — matches IM users to attendee records.

This service handles the bridge between IM platform user IDs and
the attendee roster. It does NOT import from channels/ or agents/.
"""

from __future__ import annotations

import logging
import uuid

from app.models.attendee import Attendee
from app.repositories.attendee_repo import AttendeeRepository
from app.services.exceptions import AttendeeNotFoundError

logger = logging.getLogger(__name__)


# ── Profile dict builder (plain dict, no ORM leakage) ────────

def _build_profile(attendee: Attendee) -> dict:
    """Convert an Attendee ORM object (with event loaded) to a profile dict."""
    return {
        "attendee_id": str(attendee.id),
        "name": attendee.name,
        "title": attendee.title,
        "organization": attendee.organization,
        "role": attendee.role,
        "event_id": str(attendee.event_id),
        "event_name": attendee.event.name if attendee.event else None,
    }


# ── Pure helper functions (no DB, no IO) ─────────────────────

# Common command words that should NOT be treated as names
_COMMAND_WORDS = {
    "签到", "查看", "座位", "排座", "换座", "请假", "帮助",
    "胸牌", "名牌", "导航", "位置", "审批", "退出", "取消",
    "查看座位", "查看位置", "查看导航", "查看审批",
}


def _is_command(text: str) -> bool:
    """Check if text is a known command word/phrase."""
    return text in _COMMAND_WORDS


def looks_like_identity(content: str) -> bool:
    """Check if the message looks like a self-introduction."""
    prefixes = ["我是", "我叫", "i am", "i'm", "this is"]
    lower = content.strip().lower()
    for p in prefixes:
        if lower.startswith(p):
            return True
    # Short Chinese text (2-4 chars) could be just a name,
    # but exclude common command words
    stripped = content.strip()
    if (
        2 <= len(stripped) <= 4
        and all("\u4e00" <= ch <= "\u9fff" for ch in stripped)
        and not _is_command(stripped)
    ):
        return True
    return False


def extract_name(content: str) -> str | None:
    """Extract name from a self-introduction message."""
    prefixes = ["我是", "我叫", "i am ", "i'm ", "this is "]
    lower = content.strip().lower()
    for p in prefixes:
        if lower.startswith(p):
            name = content.strip()[len(p):].strip()
            if name:
                return name
    stripped = content.strip()
    if (
        2 <= len(stripped) <= 4
        and all("\u4e00" <= ch <= "\u9fff" for ch in stripped)
        and not _is_command(stripped)
    ):
        return stripped
    return None


# ── Service class ─────────────────────────────────────────────

class IdentityService:
    """Business logic for resolving IM user identity to attendee records.

    All DB access goes through AttendeeRepository.
    """

    def __init__(self, attendee_repo: AttendeeRepository):
        self._attendee_repo = attendee_repo

    async def auto_identify(self, wecom_user_id: str) -> dict | None:
        """Try to find an attendee already bound to this wecom user ID.

        Returns a profile dict if found, None otherwise.
        """
        attendee = await self._attendee_repo.find_by_wecom_id_in_active_event(
            wecom_user_id
        )
        if attendee is None:
            return None
        return _build_profile(attendee)

    async def identify_by_name(
        self, name: str, wecom_user_id: str
    ) -> dict | None:
        """Fuzzy-match attendee by name, then bind the wecom user ID.

        Returns a profile dict if matched and bound, None if no match.
        """
        attendee = await self._attendee_repo.fuzzy_match_in_active_events(name)
        if attendee is None:
            return None

        # Bind the IM identity for future auto-identification
        await self._attendee_repo.bind_wecom_id(attendee.id, wecom_user_id)
        logger.info(f"Bound wecom {wecom_user_id} -> {attendee.name}")

        return _build_profile(attendee)
