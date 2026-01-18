"""Add indexes for performance.

Revision ID: 0005_performance_indexes
Revises: 0004_tblfinds
Create Date: 2026-01-18

Indexes are added for common joins and filters:
- tblfragments.locationid
- tblornaments.fragmentid
- frequent filter columns (recordenteredon, site/sector/square)
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0005_performance_indexes"
down_revision = "0004_tblfinds"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())

    def index_exists(table_name: str, index_name: str) -> bool:
        return any(ix.get("name") == index_name for ix in inspector.get_indexes(table_name))

    # Join performance
    if not index_exists("tblfragments", "ix_tblfragments_locationid"):
        op.create_index("ix_tblfragments_locationid", "tblfragments", ["locationid"])
    if not index_exists("tblornaments", "ix_tblornaments_fragmentid"):
        op.create_index("ix_tblornaments_fragmentid", "tblornaments", ["fragmentid"])

    # Frequent filters
    if not index_exists("tbllayers", "ix_tbllayers_recordenteredon"):
        op.create_index("ix_tbllayers_recordenteredon", "tbllayers", ["recordenteredon"])
    if not index_exists("tblfragments", "ix_tblfragments_recordenteredon"):
        op.create_index("ix_tblfragments_recordenteredon", "tblfragments", ["recordenteredon"])
    if not index_exists("tblornaments", "ix_tblornaments_recordenteredon"):
        op.create_index("ix_tblornaments_recordenteredon", "tblornaments", ["recordenteredon"])
    if inspector.has_table("tblfinds") and not index_exists("tblfinds", "ix_tblfinds_recordenteredon"):
        op.create_index("ix_tblfinds_recordenteredon", "tblfinds", ["recordenteredon"])

    if not index_exists("tbllayers", "ix_tbllayers_site_sector_square"):
        op.create_index("ix_tbllayers_site_sector_square", "tbllayers", ["site", "sector", "square"])

    # Optional: speed up lookups in finds
    if inspector.has_table("tblfinds") and not index_exists("tblfinds", "ix_tblfinds_layerid"):
        op.create_index("ix_tblfinds_layerid", "tblfinds", ["layerid"])
    if inspector.has_table("tblfinds") and not index_exists("tblfinds", "ix_tblfinds_fragmentid"):
        op.create_index("ix_tblfinds_fragmentid", "tblfinds", ["fragmentid"])
    if inspector.has_table("tblfinds") and not index_exists("tblfinds", "ix_tblfinds_ornamentid"):
        op.create_index("ix_tblfinds_ornamentid", "tblfinds", ["ornamentid"])


def downgrade() -> None:
    op.drop_index("ix_tblfinds_ornamentid", table_name="tblfinds")
    op.drop_index("ix_tblfinds_fragmentid", table_name="tblfinds")
    op.drop_index("ix_tblfinds_layerid", table_name="tblfinds")

    op.drop_index("ix_tbllayers_site_sector_square", table_name="tbllayers")

    op.drop_index("ix_tblfinds_recordenteredon", table_name="tblfinds")
    op.drop_index("ix_tblornaments_recordenteredon", table_name="tblornaments")
    op.drop_index("ix_tblfragments_recordenteredon", table_name="tblfragments")
    op.drop_index("ix_tbllayers_recordenteredon", table_name="tbllayers")

    op.drop_index("ix_tblornaments_fragmentid", table_name="tblornaments")
    op.drop_index("ix_tblfragments_locationid", table_name="tblfragments")
