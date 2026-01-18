"""Auth extensions (roles, activation, invitations).

Revision ID: 0002_auth_extensions
Revises: 0001_base_schema
Create Date: 2026-01-18

Adds:
- role (admin/user)
- is_active
- invitation fields (invited_at, invite_token_hash, invite_expires_at)
- last_login_at
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

from gkrp_data_portal.models.constants import USER_ROLE_VALUES


revision = "0002_auth_extensions"
down_revision = "0001_base_schema"
branch_labels = None
depends_on = None


def _in_list(values: tuple[str, ...]) -> str:
    return ", ".join(f"'{v}'" for v in values)


def _column_exists(table_name: str, column_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return any(col["name"] == column_name for col in inspector.get_columns(table_name))


def _check_exists(table_name: str, constraint_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return any(
        ck.get("name") == constraint_name for ck in inspector.get_check_constraints(table_name)
    )


def upgrade() -> None:
    if not _column_exists("tblregistered", "role"):
        op.add_column(
            "tblregistered",
            sa.Column("role", sa.String(length=16), nullable=False, server_default="user"),
        )
    if not _column_exists("tblregistered", "is_active"):
        op.add_column(
            "tblregistered",
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        )
    if not _column_exists("tblregistered", "invited_at"):
        op.add_column(
            "tblregistered",
            sa.Column("invited_at", sa.DateTime(timezone=True), nullable=True),
        )
    if not _column_exists("tblregistered", "invite_token_hash"):
        op.add_column(
            "tblregistered",
            sa.Column("invite_token_hash", sa.String(length=128), nullable=True),
        )
    if not _column_exists("tblregistered", "invite_expires_at"):
        op.add_column(
            "tblregistered",
            sa.Column("invite_expires_at", sa.DateTime(timezone=True), nullable=True),
        )
    if not _column_exists("tblregistered", "last_login_at"):
        op.add_column(
            "tblregistered",
            sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        )

    if not _check_exists("tblregistered", "ck_tblregistered_role_allowed"):
        op.create_check_constraint(
            "ck_tblregistered_role_allowed",
            "tblregistered",
            f"role IN ({_in_list(USER_ROLE_VALUES)})",
        )


def downgrade() -> None:
    op.drop_constraint("ck_tblregistered_role_allowed", "tblregistered", type_="check")
    op.drop_column("tblregistered", "last_login_at")
    op.drop_column("tblregistered", "invite_expires_at")
    op.drop_column("tblregistered", "invite_token_hash")
    op.drop_column("tblregistered", "invited_at")
    op.drop_column("tblregistered", "is_active")
    op.drop_column("tblregistered", "role")
