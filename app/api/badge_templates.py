"""Badge template API routes — CRUD for badge/tent card templates."""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from app.deps import get_badge_template_service
from app.schemas.badge_template import (
    BadgeTemplateCreate,
    BadgeTemplateResponse,
    BadgeTemplateUpdate,
)
from app.services.badge_template_service import BadgeTemplateService
from app.services.exceptions import TemplateNotFoundError

router = APIRouter()


@router.post("/", response_model=BadgeTemplateResponse, status_code=201)
async def create_template(
    body: BadgeTemplateCreate,
    svc: BadgeTemplateService = Depends(get_badge_template_service),
):
    """Create a new badge/tent card template."""
    tmpl = await svc.create_template(**body.model_dump())
    return BadgeTemplateResponse.model_validate(tmpl)


@router.get("/", response_model=list[BadgeTemplateResponse])
async def list_templates(
    template_type: Optional[str] = None,
    svc: BadgeTemplateService = Depends(get_badge_template_service),
):
    """List templates, optionally filtered by type."""
    templates = await svc.list_templates(template_type=template_type)
    return [BadgeTemplateResponse.model_validate(t) for t in templates]


@router.get("/builtins", response_model=list[BadgeTemplateResponse])
async def list_builtins(
    svc: BadgeTemplateService = Depends(get_badge_template_service),
):
    """List all built-in templates."""
    templates = await svc.list_builtins()
    return [BadgeTemplateResponse.model_validate(t) for t in templates]


@router.get("/{template_id}", response_model=BadgeTemplateResponse)
async def get_template(
    template_id: uuid.UUID,
    svc: BadgeTemplateService = Depends(get_badge_template_service),
):
    """Get a single template by ID."""
    try:
        tmpl = await svc.get_template(template_id)
    except TemplateNotFoundError:
        raise HTTPException(status_code=404, detail="Template not found")
    return BadgeTemplateResponse.model_validate(tmpl)


@router.patch("/{template_id}", response_model=BadgeTemplateResponse)
async def update_template(
    template_id: uuid.UUID,
    body: BadgeTemplateUpdate,
    svc: BadgeTemplateService = Depends(get_badge_template_service),
):
    """Update a custom template. Built-in templates cannot be modified."""
    try:
        tmpl = await svc.update_template(
            template_id, **body.model_dump(exclude_unset=True)
        )
    except TemplateNotFoundError:
        raise HTTPException(status_code=404, detail="Template not found")
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))
    return BadgeTemplateResponse.model_validate(tmpl)


@router.delete("/{template_id}", status_code=204)
async def delete_template(
    template_id: uuid.UUID,
    svc: BadgeTemplateService = Depends(get_badge_template_service),
):
    """Delete a custom template. Built-in templates cannot be deleted."""
    try:
        await svc.delete_template(template_id)
    except TemplateNotFoundError:
        raise HTTPException(status_code=404, detail="Template not found")
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))
