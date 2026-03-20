"""BadgeTemplate ORM model — reusable badge/tent card designs."""

from __future__ import annotations

from typing import Optional

from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class BadgeTemplate(Base, UUIDMixin, TimestampMixin):
    """A badge or tent card template.

    Templates are Jinja2 HTML+CSS stored in the DB for easy management.
    Built-in templates are seeded; users can create custom ones.
    """

    __tablename__ = "badge_templates"

    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    template_type: Mapped[str] = mapped_column(String(20), default="badge")
    # badge | tent_card
    html_template: Mapped[str] = mapped_column(Text)
    css: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    preview_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_builtin: Mapped[bool] = mapped_column(Boolean, default=False)
    style_category: Mapped[str] = mapped_column(String(30), default="business")
    # business | academic | government | custom
