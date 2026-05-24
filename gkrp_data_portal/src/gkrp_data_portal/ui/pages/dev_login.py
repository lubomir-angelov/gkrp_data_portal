from __future__ import annotations

from nicegui import app, ui
from sqlalchemy import select

from gkrp_data_portal.db.session import session_scope
from gkrp_data_portal.models.auth import User
from gkrp_data_portal.ui.lang import t

SESSION_USER_KEY = "user_id"


@ui.page("/dev-login")
def page_dev_login() -> None:
    ui.label(t("title_dev_login")).classes("text-h5")

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
        ui.notify(t("notify_no_users"), type="warning")
        ui.label(t("other_create_user_first"))
        return

    options = {
        f"{uid} | {email or ''} | {username or ''} | role={role} | active={is_active}": uid
        for (uid, email, username, role, is_active) in rows
    }

    sel = ui.select(options=list(options.keys()), label=t("label_select_user")).classes("w-full")

    def do_login() -> None:
        key = sel.value
        if not key:
            ui.notify(t("notify_select_user"), type="negative")
            return
        user_id = int(options[key])
        app.storage.user[SESSION_USER_KEY] = user_id
        ui.notify(t("notify_session_set").format(user_id=user_id), type="positive")
        ui.navigate.to("/admin")

    def do_logout() -> None:
        app.storage.user.pop(SESSION_USER_KEY, None)
        ui.notify(t("notify_session_cleared"), type="positive")

    with ui.row().classes("gap-2"):
        ui.button(t("btn_login"), on_click=do_login)
        ui.button(t("btn_logout"), on_click=do_logout)

    ui.markdown(t("title_dev_login_text")).classes("text-sm")
