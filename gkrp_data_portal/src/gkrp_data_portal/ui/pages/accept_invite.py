from __future__ import annotations

import hashlib

from nicegui import ui
from sqlalchemy import select

from gkrp_data_portal.core.invitations import is_expired, verify_token
from gkrp_data_portal.db.session import session_scope
from gkrp_data_portal.models.auth import User


def _hash_password(pw: str) -> str:
    # parity-first simple hash; replace with bcrypt/argon later if desired
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()


@ui.page("/accept-invite")
def page_accept_invite() -> None:
    token_raw = ui.query.get("token", "")
    token_raw = (token_raw or "").strip()

    ui.label("Accept invitation").classes("text-h5")

    if not token_raw:
        ui.notify("Missing token", type="negative")
        ui.label("Invalid invitation link.")
        return

    with session_scope() as db:
        # find user row that matches token hash (do not store raw token)
        # brute force is avoided: we compute hash and match
        token_hash = hashlib.sha256(token_raw.encode("utf-8")).hexdigest()
        user = db.execute(select(User).where(User.invite_token_hash == token_hash)).scalar_one_or_none()

        if user is None:
            ui.notify("Invalid token", type="negative")
            ui.label("Invalid invitation.")
            return

        if is_expired(user.invite_expires_at):
            ui.notify("Invite expired", type="negative")
            ui.label("Invitation expired. Ask admin for a new one.")
            return

        # token matches already by lookup; verify constant-time anyway
        if not verify_token(token_raw, user.invite_token_hash):
            ui.notify("Invalid token", type="negative")
            ui.label("Invalid invitation.")
            return

    inp_username = ui.input("Choose username").props("autocomplete=off").classes("w-[420px]")
    inp_password = ui.input("Choose password", password=True).props("autocomplete=new-password").classes("w-[420px]")
    inp_password2 = ui.input("Repeat password", password=True).props("autocomplete=new-password").classes("w-[420px]")

    def do_accept() -> None:
        username = (inp_username.value or "").strip()
        pw1 = inp_password.value or ""
        pw2 = inp_password2.value or ""
        if not username:
            ui.notify("Username is required", type="negative")
            return
        if not pw1 or pw1 != pw2:
            ui.notify("Passwords do not match", type="negative")
            return

        token_hash = hashlib.sha256(token_raw.encode("utf-8")).hexdigest()

        with session_scope() as db:
            user2 = db.execute(select(User).where(User.invite_token_hash == token_hash)).scalar_one_or_none()
            if user2 is None:
                ui.notify("Invalid token", type="negative")
                return
            if is_expired(user2.invite_expires_at):
                ui.notify("Invite expired", type="negative")
                return

            user2.username = username
            user2.password_hash = _hash_password(pw1)
            user2.is_active = True
            user2.invite_token_hash = None
            user2.invite_expires_at = None
            db.add(user2)
            db.flush()

        ui.notify("Account activated. You can now log in.", type="positive")
        ui.navigate.to("/")

    ui.button("Activate account", on_click=do_accept).classes("mt-4")
