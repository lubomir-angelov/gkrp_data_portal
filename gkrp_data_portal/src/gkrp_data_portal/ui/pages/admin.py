"""
This page:

Always shows the link for manual sending

Attempts SMTP if configured, but does not require it
"""


from __future__ import annotations

from nicegui import ui

from gkrp_data_portal.auth.deps import require_admin
from gkrp_data_portal.core.email import maybe_send_invite_email
from gkrp_data_portal.core.invitations import new_invite_token
from gkrp_data_portal.core.settings import get_app_base_url, get_invite_ttl_hours
from gkrp_data_portal.db.session import session_scope
from gkrp_data_portal.ui.repository.admin_repo import create_invite_for_email, list_users, set_user_active


@ui.page("/admin")
def page_admin() -> None:
    # Guard: raise if not admin. NiceGUI will show error; you can add friendly redirect later.
    require_admin()

    ui.label("Admin").classes("text-h5")

    invite_link_label = ui.label("").classes("text-sm")
    invite_link_copy = ui.input("Invite link").props("readonly").classes("w-full")
    invite_link_copy.set_visibility(False)

    ui.separator()

    ui.label("Create invite").classes("text-h6")
    with ui.row().classes("w-full items-end"):
        inp_email = ui.input("Email").classes("w-[420px]")
        sel_role = ui.select(["user", "admin"], value="user", label="Role").classes("w-[180px]")
        btn_create = ui.button("Create invite")

    def do_create_invite() -> None:
        email = (inp_email.value or "").strip()
        if not email:
            ui.notify("Email is required", type="negative")
            return

        token = new_invite_token()
        ttl = get_invite_ttl_hours()

        with session_scope() as db:
            create_invite_for_email(db, email=email, token=token, ttl_hours=ttl, role=sel_role.value)

        base = get_app_base_url()
        link = f"{base}/accept-invite?token={token.raw}"

        invite_link_label.text = "Invite created. Copy and send this link:"
        invite_link_copy.value = link
        invite_link_copy.set_visibility(True)

        # optional SMTP (will no-op if not configured)
        sent = maybe_send_invite_email(
            to_email=email,
            subject="Invitation to GKR Portal",
            body=f"You have been invited.\n\nOpen this link to activate your account:\n{link}\n\nThis link expires in {ttl} hours.",
        )
        if sent:
            ui.notify("Invite email sent via SMTP", type="positive")
        else:
            ui.notify("SMTP not configured; link shown for manual sending", type="warning")

        refresh_users()

    btn_create.on_click(do_create_invite)

    ui.separator()

    ui.label("Users").classes("text-h6")
    users_table = ui.table(
        columns=[
            {"name": "id", "label": "ID", "field": "id", "sortable": True},
            {"name": "username", "label": "Username", "field": "username"},
            {"name": "email", "label": "Email", "field": "email"},
            {"name": "role", "label": "Role", "field": "role"},
            {"name": "is_active", "label": "Active", "field": "is_active"},
            {"name": "invited_at", "label": "Invited", "field": "invited_at"},
            {"name": "invite_expires_at", "label": "Invite Expires", "field": "invite_expires_at"},
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
            ui.label(f"User {uid} actions").classes("text-h6")
            ui.label(f"Email: {row.get('email')}")
            ui.label(f"Username: {row.get('username')}")
            ui.label(f"Role: {row.get('role')}")
            ui.label(f"Active: {row.get('is_active')}")

            with ui.row().classes("w-full justify-end"):
                ui.button("Close", on_click=dialog.close)
                if row.get("is_active"):
                    ui.button("Disable", on_click=lambda: (toggle_user(int(uid), False), dialog.close()))
                else:
                    ui.button("Activate", on_click=lambda: (toggle_user(int(uid), True), dialog.close()))

        dialog.open()

    users_table.on("rowClick", on_row_click)

    refresh_users()
