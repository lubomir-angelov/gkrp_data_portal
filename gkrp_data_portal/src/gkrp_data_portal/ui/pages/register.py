from __future__ import annotations

from nicegui import ui


@ui.page("/register")
def page_register() -> None:
    ui.label("Registration disabled").classes("text-h5")
    ui.markdown("Access is by invitation only. Please contact the administrator.")
