from __future__ import annotations

from nicegui import app, ui
from sqlalchemy import select

from gkrp_data_portal.db.session import session_scope
from gkrp_data_portal.models.auth import User

SESSION_USER_KEY = "user_id"


@ui.page("/dev-login")
def page_dev_login() -> None:
    ui.label("DEV Login (sets session user_id)").classes("text-h5")

    with session_scope() as db:
        rows = db.execute(
            select(
                User.id,
                User.email,
                User.username,
                User.role,
                User.is_active,
            ).order_by(User.id.asc())
        ).all()

    if not rows:
        ui.notify("No users found in tblregistered", type="warning")
        ui.label("Create a user (or invite) first, then come back.")
        return

    options = {
        f"{uid} | {email or ''} | {username or ''} | role={role} | active={is_active}": uid
        for (uid, email, username, role, is_active) in rows
    }

    sel = ui.select(options=list(options.keys()), label="Select user to become").classes("w-full")

    def do_login() -> None:
        key = sel.value
        if not key:
            ui.notify("Select a user", type="negative")
            return
        user_id = int(options[key])
        app.storage.user[SESSION_USER_KEY] = user_id
        ui.notify(f"Session set: user_id={user_id}", type="positive")
        ui.navigate.to("/admin")

    def do_logout() -> None:
        app.storage.user.pop(SESSION_USER_KEY, None)
        ui.notify("Session cleared", type="positive")

    with ui.row().classes("gap-2"):
        ui.button("Login as selected user", on_click=do_login)
        ui.button("Logout (clear session)", on_click=do_logout)

    ui.markdown("After logging in, open **/admin** to test admin features.").classes("text-sm")
