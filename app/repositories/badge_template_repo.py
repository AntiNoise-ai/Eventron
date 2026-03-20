"""BadgeTemplate repository — badge/tent card template queries."""

from sqlalchemy import select

from app.models.badge_template import BadgeTemplate
from app.repositories.base import BaseRepository


class BadgeTemplateRepository(BaseRepository[BadgeTemplate]):
    """Data access for BadgeTemplate entities."""

    model = BadgeTemplate

    async def get_by_type(self, template_type: str) -> list[BadgeTemplate]:
        """Fetch all templates of a given type (badge/tent_card)."""
        stmt = (
            select(BadgeTemplate)
            .where(BadgeTemplate.template_type == template_type)
            .order_by(BadgeTemplate.is_builtin.desc(), BadgeTemplate.name)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_builtins(self) -> list[BadgeTemplate]:
        """Fetch all built-in templates."""
        stmt = (
            select(BadgeTemplate)
            .where(BadgeTemplate.is_builtin.is_(True))
            .order_by(BadgeTemplate.name)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
