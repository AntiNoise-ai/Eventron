"""Pydantic schemas for Excel import preview."""

from typing import Optional

from pydantic import BaseModel, Field


class ColumnMapping(BaseModel):
    """Maps an Excel column header to an attendee field."""

    excel_header: str
    mapped_to: Optional[str] = None  # attendee field name or None (skip)
    confidence: float = 0.0  # 0-1 confidence of auto-mapping


class ImportPreviewResponse(BaseModel):
    """Response from import-preview endpoint."""

    total_rows: int
    column_mappings: list[ColumnMapping]
    sample_rows: list[dict]  # first 5 rows as raw dicts
    warnings: list[str] = Field(default_factory=list)
    # e.g. ["3 rows missing name field", "Possible duplicate: 张三 (Acme Corp)"]


class ImportConfirmRequest(BaseModel):
    """Confirm import with user-adjusted field mappings."""

    column_mappings: dict[str, str]
    # e.g. {"姓名": "name", "职位": "title", "公司": "organization"}
    skip_duplicates: bool = True
