from __future__ import annotations

from nicegui import ui

from gkrp_data_portal.ui.lang import t


@ui.page("/register")
def page_register() -> None:
    ui.label(t("title_register")).classes("text-h5")
    ui.markdown(t("other_access_by_invite"))
