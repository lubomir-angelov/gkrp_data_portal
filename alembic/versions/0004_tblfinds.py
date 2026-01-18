"""Add tblfinds (находки).

Revision ID: 0004_tblfinds
Revises: 0003_fragment_image_url
Create Date: 2026-01-18

Adds a new table for finds which can be linked to a layer, and optionally to a
fragment and/or ornament.
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0004_tblfinds"
down_revision = "0003_fragment_image_url"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if inspector.has_table("tblfinds"):
        return

    op.create_table(
        "tblfinds",
        sa.Column("findid", sa.Integer(), sa.Identity(), primary_key=True),
        sa.Column(
            "layerid",
            sa.Integer(),
            sa.ForeignKey("tbllayers.layerid", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "fragmentid",
            sa.Integer(),
            sa.ForeignKey("tblfragments.fragmentid", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "ornamentid",
            sa.Integer(),
            sa.ForeignKey("tblornaments.ornamentid", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("findtype", sa.String(length=100), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("inventory", sa.String(length=50), nullable=True),
        sa.Column("image_url", sa.String(length=2048), nullable=True),
        sa.Column("recordenteredby", sa.String(length=50), nullable=True),
        sa.Column(
            "recordenteredon",
            sa.TIMESTAMP(timezone=False),
            nullable=False,
            server_default=sa.text("now()"),
        )
    )


def downgrade() -> None:
    op.drop_table("tblfinds")
