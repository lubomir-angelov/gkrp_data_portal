"""Add image_url to tblfragments.

Revision ID: 0003_fragment_image_url
Revises: 0002_auth_extensions
Create Date: 2026-01-18

Adds a URL column that points to externally hosted images of fragments.
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0003_fragment_image_url"
down_revision = "0002_auth_extensions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if any(col["name"] == "image_url" for col in inspector.get_columns("tblfragments")):
        return
    op.add_column("tblfragments", sa.Column("image_url", sa.String(length=2048), nullable=True))


def downgrade() -> None:
    op.drop_column("tblfragments", "image_url")
