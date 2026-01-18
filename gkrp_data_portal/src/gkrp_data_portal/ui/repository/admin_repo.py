from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from gkrp_data_portal.core.invitations import InviteToken, compute_expiry
from gkrp_data_portal.models.auth import User


def list_users(db: Session) -> list[User]:
    return list(db.execute(select(User).order_by(User.id.asc())).scalars().all())


def set_user_active(db: Session, user_id: int, is_active: bool) -> None:
    user = db.get(User, user_id)
    if user is None:
        raise ValueError("User not found")
    user.is_active = is_active
    db.add(user)
    db.flush()


def create_invite_for_email(
    db: Session,
    *,
    email: str,
    token: InviteToken,
    ttl_hours: int,
    role: str = "user",
) -> User:
    """Create or update a user row with invitation fields set.

    We follow "backup as truth": allow nullable username, email unique.
    """
    # Normalize email lightly
    email_norm = email.strip()
    if not email_norm:
        raise ValueError("email is required")

    existing = db.execute(select(User).where(User.email == email_norm)).scalar_one_or_none()
    user = existing if existing else User(email=email_norm)

    user.role = role
    user.is_active = False
    user.invited_at = datetime.utcnow()
    user.invite_token_hash = token.hashed
    user.invite_expires_at = compute_expiry(ttl_hours)

    db.add(user)
    db.flush()
    db.refresh(user)
    return user


def accept_invite(
    db: Session,
    *,
    token_hash: str,
    username: str,
    password_hash: str,
) -> None:
    """Finalize invitation: set username/password and activate."""
    user = db.execute(select(User).where(User.invite_token_hash == token_hash)).scalar_one_or_none()
    if user is None:
        raise ValueError("Invalid invite")

    user.username = username
    user.password_hash = password_hash
    user.is_active = True

    # burn token
    user.invite_token_hash = None
    user.invite_expires_at = None

    db.add(user)
    db.flush()
