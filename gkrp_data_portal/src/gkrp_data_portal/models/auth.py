"""Authentication and authorization ORM models."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    CHAR,
    CheckConstraint,
    DateTime,
    Identity,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import text

from gkrp_data_portal.db.base import Base
from gkrp_data_portal.models.constants import USER_ROLE_VALUES


def _in_list(values: tuple[str, ...]) -> str:
    """Return a SQL IN-list with quoted literals."""
    return ", ".join(f"'{v}'" for v in values)


class User(Base):
    """Registered user.

    This is a minimal extension of the legacy ceramics `tblregistered` table.
    Role and invitation fields are added in a later migration.
    """

    __tablename__ = "tblregistered"
    __table_args__ = (
        CheckConstraint(
            f"role IN ({_in_list(USER_ROLE_VALUES)})",
            name="role_allowed",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)

    # Backup-aligned base columns
    username: Mapped[Optional[str]] = mapped_column(CHAR(25), unique=True, nullable=True)
    email: Mapped[Optional[str]] = mapped_column(Text, unique=True, nullable=True)
    password_hash: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)

    # Auth extensions (added in later migration)
    role: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        server_default=text("'user'"),
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("false"),
    )

    invited_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    invite_token_hash: Mapped[Optional[str]] = mapped_column(String(128))
    invite_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
