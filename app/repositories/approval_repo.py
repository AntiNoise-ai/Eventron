"""ApprovalRequest repository — all approval-related DB queries."""

import uuid

from sqlalchemy import select

from app.models.approval import ApprovalRequest
from app.repositories.base import BaseRepository


class ApprovalRepository(BaseRepository[ApprovalRequest]):
    """Data access for ApprovalRequest entities."""

    model = ApprovalRequest

    async def get_pending_by_event(self, event_id: uuid.UUID) -> list[ApprovalRequest]:
        """Fetch all pending approval requests for an event."""
        stmt = (
            select(ApprovalRequest)
            .where(ApprovalRequest.event_id == event_id)
            .where(ApprovalRequest.status == "pending")
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_thread_id(self, thread_id: str) -> ApprovalRequest | None:
        """Look up an approval request by LangGraph thread ID."""
        stmt = select(ApprovalRequest).where(
            ApprovalRequest.lg_thread_id == thread_id
        )
        result = await self._session.execute(stmt)
        return result.scalars().first()
