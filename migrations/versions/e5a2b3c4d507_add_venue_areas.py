"""Add venue_areas table and seat.area_id FK.

Revision ID: e5a2b3c4d507
Revises: d4f8a1b2c396
Create Date: 2026-03-22
"""

from alembic import op
import sqlalchemy as sa

revision = "e5a2b3c4d507"
down_revision = "d4f8a1b2c396"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "venue_areas",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("event_id", sa.Uuid(), sa.ForeignKey("events.id"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("layout_type", sa.String(30), server_default="grid"),
        sa.Column("rows", sa.Integer(), server_default="0"),
        sa.Column("cols", sa.Integer(), server_default="0"),
        sa.Column("display_order", sa.Integer(), server_default="0"),
        sa.Column("offset_x", sa.Float(), server_default="0"),
        sa.Column("offset_y", sa.Float(), server_default="0"),
        sa.Column("stage_label", sa.String(50), nullable=True),
    )

    op.add_column(
        "seats",
        sa.Column("area_id", sa.Uuid(), sa.ForeignKey("venue_areas.id"), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("seats", "area_id")
    op.drop_table("venue_areas")
