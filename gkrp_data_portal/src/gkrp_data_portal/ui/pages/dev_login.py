from __future__ import annotations

from nicegui import app, ui
from sqlalchemy import select

from gkrp_data_portal.db.session import session_scope
from gkrp_data_portal.models.auth import User
from .analytics_common import LOCALE

SESSION_USER_KEY = "user_id"


@ui.page("/dev-login")
def page_dev_login() -> None:
    ui.label(LOCALE["title_dev_login"]).classes("text-h5")

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
        ui.notify(LOCALE["notify_no_users"], type="warning")
        ui.label(LOCALE["other_create_user_first"])
        return

    options = {
        f"{uid} | {email or ''} | {username or ''} | role={role} | active={is_active}": uid
        for (uid, email, username, role, is_active) in rows
    }

    sel = ui.select(options=list(options.keys()), label=LOCALE["label_select_user"]).classes("w-full")

    def do_login() -> None:
        key = sel.value
        if not key:
            ui.notify(LOCALE["notify_select_user"], type="negative")
            return
        user_id = int(options[key])
        app.storage.user[SESSION_USER_KEY] = user_id
        ui.notify(LOCALE["notify_session_set"].format(user_id=user_id), type="positive")
        ui.navigate.to("/admin")

    def do_logout() -> None:
        app.storage.user.pop(SESSION_USER_KEY, None)
        ui.notify(LOCALE["notify_session_cleared"], type="positive")

    with ui.row().classes("gap-2"):
        ui.button(LOCALE["btn_login"], on_click=do_login)
        ui.button(LOCALE["btn_logout"], on_click=do_logout)

    ui.markdown(LOCALE["title_dev_login_text"]).classes("text-sm")
