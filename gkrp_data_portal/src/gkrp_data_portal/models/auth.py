"""Authentication and authorization ORM models."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, CheckConstraint, DateTime, Identity, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

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
    username: Mapped[Optional[str]] = mapped_column(String(25), unique=True)
    email: Mapped[Optional[str]] = mapped_column(String, unique=True)
    password_hash: Mapped[Optional[str]] = mapped_column(String)

    # Added in a later migration.
    role: Mapped[str] = mapped_column(String(16), server_default="user", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="false", nullable=False)

    invited_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    invite_token_hash: Mapped[Optional[str]] = mapped_column(String(128))
    invite_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
