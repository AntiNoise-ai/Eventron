"""Add pos_x, pos_y, rotation to seats for free-form layouts.

Revision ID: d4f8a1b2c396
Revises: c3a7d8e2f195
Create Date: 2026-03-21
"""

from alembic import op
import sqlalchemy as sa

revision = "d4f8a1b2c396"
down_revision = "c3a7d8e2f195"
branch_labels = None
depends_on = None

SPACING = 60.0  # default grid spacing in virtual canvas units


def upgrade() -> None:
    op.add_column("seats", sa.Column("pos_x", sa.Float(), nullable=True))
    op.add_column("seats", sa.Column("pos_y", sa.Float(), nullable=True))
    op.add_column(
        "seats",
        sa.Column("rotation", sa.Float(), nullable=True, server_default="0"),
    )

    # Back-fill pos_x/pos_y from row_num/col_num for existing seats.
    op.execute(
        f"UPDATE seats SET pos_x = (col_num - 1) * {SPACING}, "
        f"pos_y = (row_num - 1) * {SPACING}, rotation = 0 "
        "WHERE pos_x IS NULL"
    )


def downgrade() -> None:
    op.drop_column("seats", "rotation")
    op.drop_column("seats", "pos_y")
    op.drop_column("seats", "pos_x")
