from __future__ import annotations

from nicegui import ui

from .analytics_common import LOCALE


@ui.page("/register")
def page_register() -> None:
    ui.label(LOCALE["title_register"]).classes("text-h5")
    ui.markdown(LOCALE["other_access_by_invite"])
