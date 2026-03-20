"""Approval API routes — thin layer, delegates to ApprovalService."""

import uuid

from fastapi import APIRouter, Depends, HTTPException

from app.deps import get_approval_service
from app.schemas.approval import ApprovalDecision, ApprovalResponse
from app.services.approval_service import ApprovalService
from app.services.exceptions import InvalidStateTransitionError, NotFoundError

router = APIRouter()


@router.get("/{event_id}/approvals", response_model=list[ApprovalResponse])
async def list_pending_approvals(
    event_id: uuid.UUID,
    svc: ApprovalService = Depends(get_approval_service),
):
    """List all pending approval requests for an event."""
    reqs = await svc.get_pending(event_id)
    return [ApprovalResponse.model_validate(r) for r in reqs]


@router.post("/approvals/{request_id}/decide", response_model=ApprovalResponse)
async def decide_approval(
    request_id: uuid.UUID,
    body: ApprovalDecision,
    svc: ApprovalService = Depends(get_approval_service),
):
    """Approve or reject an approval request."""
    try:
        if body.status == "approved":
            result = await svc.approve(request_id, body.reviewer_id, body.review_note)
        else:
            result = await svc.reject(request_id, body.reviewer_id, body.review_note)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Approval request not found")
    except InvalidStateTransitionError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return ApprovalResponse.model_validate(result)
