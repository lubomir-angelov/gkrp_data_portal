from __future__ import annotations

from typing import Optional

from nicegui import app
from sqlalchemy.orm import Session

from gkrp_data_portal.db.session import session_scope
from gkrp_data_portal.models.auth import User


SESSION_USER_KEY = "user_id"


def get_current_user(db: Session) -> Optional[User]:
    user_id = app.storage.user.get(SESSION_USER_KEY)
    if not user_id:
        return None
    return db.get(User, int(user_id))


def require_user() -> User:
    with session_scope() as db:
        user = get_current_user(db)
        if user is None or not user.is_active:
            raise PermissionError("Not authenticated or inactive user")
        return user


def require_admin() -> User:
    with session_scope() as db:
        user = get_current_user(db)
        if user is None or not user.is_active:
            raise PermissionError("Not authenticated or inactive user")
        if user.role != "admin":
            raise PermissionError("Admin privileges required")
        return user
