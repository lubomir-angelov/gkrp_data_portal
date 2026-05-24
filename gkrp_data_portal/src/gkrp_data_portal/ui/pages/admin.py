"""
This page:

Always shows the link for manual sending

Attempts SMTP if configured, but does not require it
"""


from __future__ import annotations

from nicegui import ui

from gkrp_data_portal.auth.deps import require_admin
from gkrp_data_portal.ui.lang import t
from gkrp_data_portal.core.email import maybe_send_invite_email
from gkrp_data_portal.core.invitations import new_invite_token
from gkrp_data_portal.core.settings import get_app_base_url, get_invite_ttl_hours
from gkrp_data_portal.db.session import session_scope
from gkrp_data_portal.ui.repository.admin_repo import create_invite_for_email, list_users, set_user_active


@ui.page("/admin")
def page_admin() -> None:
    # Guard: raise if not admin. NiceGUI will show error; you can add friendly redirect later.
    require_admin()

    ui.label(t("title_admin")).classes("text-h5 text-blue-600")

    invite_link_label = ui.label("").classes("text-sm")
    invite_link_copy = ui.input(t("label_invite_link")).props("readonly").classes("w-full")
    invite_link_copy.set_visibility(False)

    ui.separator()

    ui.label(t("btn_create_invite")).classes("text-h6 text-blue-600")
    with ui.row().classes("w-full items-end"):
        inp_email = ui.input(t("label_email")).classes("w-[420px]")
        sel_role = ui.select(["user", "admin"], value="user", label=t("label_role")).classes("w-[180px]")
        btn_create = ui.button(t("btn_create_invite"))

    def do_create_invite() -> None:
        email = (inp_email.value or "").strip()
        if not email:
            ui.notify(t("notify_email_required"), type="negative")
            return

        token = new_invite_token()
        ttl = get_invite_ttl_hours()

        with session_scope() as db:
            create_invite_for_email(db, email=email, token=token, ttl_hours=ttl, role=sel_role.value)

        base = get_app_base_url()
        link = f"{base}/accept-invite?token={token.raw}"

        invite_link_label.text = t("notify_invite_created")
        invite_link_copy.value = link
        invite_link_copy.set_visibility(True)

        # optional SMTP (will no-op if not configured)
        sent = maybe_send_invite_email(
            to_email=email,
            subject=t("other_invite_created_text"),
            body=t("other_invite_body").format(link=link, ttl=ttl),
        )
        if sent:
            ui.notify(t("notify_invite_email_sent"), type="positive")
        else:
            ui.notify(t("notify_smtp_not_configured"), type="warning")

        refresh_users()

    btn_create.on_click(do_create_invite)

    ui.separator()

    ui.label(t("admin_users")).classes("text-h6 text-blue-600")
    users_table = ui.table(
        columns=[
            {"name": "id", "label": t("col_id"), "field": "id", "sortable": True},
            {"name": "username", "label": t("col_username"), "field": "username"},
            {"name": "email", "label": t("admin_email"), "field": "email"},
            {"name": "role", "label": t("admin_role"), "field": "role"},
            {"name": "is_active", "label": t("admin_active"), "field": "is_active"},
            {"name": "invited_at", "label": t("col_invited"), "field": "invited_at"},
            {"name": "invite_expires_at", "label": t("col_invite_expires"), "field": "invite_expires_at"},
        ],
        rows=[],
        row_key="id",
        pagination=25,
    ).classes("w-full")

    def refresh_users() -> None:
        with session_scope() as db:
            users = list_users(db)
        users_table.rows = [
            {
                "id": u.id,
                "username": u.username,
                "email": u.email,
                "role": u.role,
                "is_active": u.is_active,
                "invited_at": str(u.invited_at) if u.invited_at else "",
                "invite_expires_at": str(u.invite_expires_at) if u.invite_expires_at else "",
            }
            for u in users
        ]
        users_table.update()

    def toggle_user(user_id: int, active: bool) -> None:
        with session_scope() as db:
            set_user_active(db, user_id, active)
        refresh_users()

    def on_row_click(e) -> None:
        row = e.args.get("row") or {}
        uid = row.get("id")
        if not uid:
            return

        dialog = ui.dialog()
        with dialog, ui.card().classes("w-[520px]"):
            ui.label(t("dialog_user_actions").format(uid=uid)).classes("text-h6 text-blue-600")
            ui.label(f"{t('admin_email')}: {row.get('email')}")
            ui.label(f"{t('admin_username')}: {row.get('username')}")
            ui.label(f"{t('admin_role')}: {row.get('role')}")
            ui.label(f"{t('admin_active')}: {row.get('is_active')}")

            with ui.row().classes("w-full justify-end"):
                ui.button(t("btn_close"), on_click=dialog.close)
                if row.get("is_active"):
                    ui.button(t("btn_disable"), on_click=lambda: (toggle_user(int(uid), False), dialog.close()))
                else:
                    ui.button(t("btn_activate"), on_click=lambda: (toggle_user(int(uid), True), dialog.close()))

        dialog.open()

    users_table.on("rowClick", on_row_click)

    refresh_users()
