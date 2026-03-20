"""Badge template management — CRUD + listing for badge/tent card templates."""

from __future__ import annotations

import uuid

from app.models.badge_template import BadgeTemplate
from app.repositories.badge_template_repo import BadgeTemplateRepository
from app.services.exceptions import TemplateNotFoundError


class BadgeTemplateService:
    """Business logic for badge template operations."""

    def __init__(self, badge_template_repo: BadgeTemplateRepository):
        self._repo = badge_template_repo

    async def create_template(self, **kwargs) -> BadgeTemplate:
        """Create a new badge template."""
        kwargs.setdefault("is_builtin", False)
        kwargs.setdefault("template_type", "badge")
        kwargs.setdefault("style_category", "custom")
        return await self._repo.create(**kwargs)

    async def get_template(self, template_id: uuid.UUID) -> BadgeTemplate:
        """Fetch a template by ID, raise if not found."""
        tmpl = await self._repo.get_by_id(template_id)
        if tmpl is None:
            raise TemplateNotFoundError(f"Template {template_id} not found")
        return tmpl

    async def list_templates(
        self, template_type: str | None = None
    ) -> list[BadgeTemplate]:
        """List templates, optionally filtered by type."""
        if template_type:
            return await self._repo.get_by_type(template_type)
        return await self._repo.list_all()

    async def list_builtins(self) -> list[BadgeTemplate]:
        """List all built-in templates."""
        return await self._repo.get_builtins()

    async def update_template(
        self, template_id: uuid.UUID, **kwargs
    ) -> BadgeTemplate:
        """Update template fields. Built-in templates cannot be edited."""
        tmpl = await self.get_template(template_id)
        if tmpl.is_builtin:
            raise ValueError("Built-in templates cannot be modified")
        result = await self._repo.update(template_id, **kwargs)
        if result is None:
            raise TemplateNotFoundError(f"Template {template_id} not found")
        return result

    async def delete_template(self, template_id: uuid.UUID) -> bool:
        """Delete a custom template. Built-in templates cannot be deleted."""
        tmpl = await self.get_template(template_id)
        if tmpl.is_builtin:
            raise ValueError("Built-in templates cannot be deleted")
        return await self._repo.delete(template_id)
