from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


@dataclass(frozen=True)
class InviteToken:
    """Represents a raw invite token plus its stored hash."""
    raw: str
    hashed: str


def _hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def new_invite_token() -> InviteToken:
    # URL-safe, high-entropy token
    raw = secrets.token_urlsafe(32)
    return InviteToken(raw=raw, hashed=_hash_token(raw))


def is_expired(expires_at: datetime | None) -> bool:
    if not expires_at:
        return True
    if expires_at.tzinfo is None:
        # treat naive as UTC for safety
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) >= expires_at


def compute_expiry(hours: int) -> datetime:
    return datetime.now(timezone.utc) + timedelta(hours=hours)


def verify_token(raw: str, stored_hash: str | None) -> bool:
    if not stored_hash:
        return False
    return secrets.compare_digest(_hash_token(raw), stored_hash)
