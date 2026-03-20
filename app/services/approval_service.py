"""Approval workflow logic — manages change request lifecycle."""

import uuid

from app.models.approval import ApprovalRequest
from app.repositories.approval_repo import ApprovalRepository
from app.services.exceptions import InvalidStateTransitionError, NotFoundError


class ApprovalService:
    """Business logic for the approval workflow."""

    def __init__(self, approval_repo: ApprovalRepository):
        self._repo = approval_repo

    async def create_request(
        self,
        event_id: uuid.UUID,
        requester_id: uuid.UUID,
        change_type: str,
        change_detail: dict,
        lg_thread_id: str | None = None,
    ) -> ApprovalRequest:
        """Create a new approval request."""
        return await self._repo.create(
            event_id=event_id,
            requester_id=requester_id,
            change_type=change_type,
            change_detail=change_detail,
            status="pending",
            lg_thread_id=lg_thread_id,
        )

    async def get_request(self, request_id: uuid.UUID) -> ApprovalRequest:
        """Get an approval request by ID."""
        req = await self._repo.get_by_id(request_id)
        if req is None:
            raise NotFoundError(f"ApprovalRequest {request_id} not found")
        return req

    async def get_pending(self, event_id: uuid.UUID) -> list[ApprovalRequest]:
        """Get all pending approval requests for an event."""
        return await self._repo.get_pending_by_event(event_id)

    async def approve(
        self,
        request_id: uuid.UUID,
        reviewer_id: str,
        note: str | None = None,
    ) -> ApprovalRequest:
        """Approve a request."""
        return await self._decide(request_id, "approved", reviewer_id, note)

    async def reject(
        self,
        request_id: uuid.UUID,
        reviewer_id: str,
        note: str | None = None,
    ) -> ApprovalRequest:
        """Reject a request."""
        return await self._decide(request_id, "rejected", reviewer_id, note)

    async def _decide(
        self,
        request_id: uuid.UUID,
        new_status: str,
        reviewer_id: str,
        note: str | None,
    ) -> ApprovalRequest:
        """Apply an approval decision."""
        req = await self.get_request(request_id)
        if req.status != "pending":
            raise InvalidStateTransitionError(
                f"Cannot {new_status} a request that is '{req.status}'"
            )
        result = await self._repo.update(
            request_id,
            status=new_status,
            reviewer_id=reviewer_id,
            review_note=note,
        )
        if result is None:
            raise NotFoundError(f"ApprovalRequest {request_id} not found")
        return result

    async def get_by_thread(self, thread_id: str) -> ApprovalRequest | None:
        """Look up approval by LangGraph thread (for HITL resume)."""
        return await self._repo.get_by_thread_id(thread_id)
