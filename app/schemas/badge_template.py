"""Pydantic schemas for BadgeTemplate API."""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class BadgeTemplateCreate(BaseModel):
    """Request body for creating a badge template."""

    name: str = Field(..., max_length=100)
    description: Optional[str] = Field(None, max_length=300)
    template_type: str = Field("badge", pattern=r"^(badge|tent_card)$")
    html_template: str
    css: Optional[str] = None
    style_category: str = Field(
        "custom", pattern=r"^(business|academic|government|custom)$"
    )


class BadgeTemplateUpdate(BaseModel):
    """Request body for partial template update."""

    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=300)
    html_template: Optional[str] = None
    css: Optional[str] = None
    style_category: Optional[str] = Field(
        None, pattern=r"^(business|academic|government|custom)$"
    )


class BadgeTemplateResponse(BaseModel):
    """Response body for badge template data."""

    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    description: Optional[str]
    template_type: str
    html_template: str
    css: Optional[str]
    preview_url: Optional[str]
    is_builtin: bool
    style_category: str
    created_at: datetime
    updated_at: datetime
