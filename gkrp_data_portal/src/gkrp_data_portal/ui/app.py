"""NiceGUI application entrypoint (parity-first)."""

from __future__ import annotations

from nicegui import ui

from .analytics_common import LOCALE

# Import pages to register routes
from gkrp_data_portal.ui.pages.layers import page_layers  # noqa: F401
from gkrp_data_portal.ui.pages.fragments import page_fragments  # noqa: F401
from gkrp_data_portal.ui.pages.ornaments import page_ornaments  # noqa: F401
from gkrp_data_portal.ui.pages.admin import page_admin  # noqa: F401
from gkrp_data_portal.ui.pages.accept_invite import page_accept_invite  # noqa: F401
from gkrp_data_portal.ui.pages.dev_login import page_dev_login  # noqa: F401
from gkrp_data_portal.ui.pages.analytics_chart import page_analytics_index, page_analytics_chart  # noqa: F401
from gkrp_data_portal.ui.pages.analytics_table import page_analytics_table  # noqa: F401


# settings
from gkrp_data_portal.core.settings import get_storage_secret


@ui.page("/")
def index() -> None:
    with ui.row().classes("w-full"):
        with ui.column().classes("w-64"):
            ui.label(LOCALE["nav_navigation"]).classes("text-h6 text-blue-600")
            ui.link(LOCALE["nav_layers"], "/layers")
            ui.link(LOCALE["nav_fragments"], "/fragments")
            ui.link(LOCALE["nav_ornaments"], "/ornaments")
            ui.link(LOCALE["nav_admin"], "/admin")
            ui.link(LOCALE["nav_analytics"], "/analytics")

        with ui.column().classes("grow"):
            ui.label(LOCALE["nav_welcome_title"]).classes("text-h5 text-blue-600")
            ui.markdown(LOCALE["nav_welcome_text"])


def run() -> None:
    ui.run(
        title="GKR Data Portal", 
        reload=False,
        storage_secret=get_storage_secret(),
        host='0.0.0.0',
        port=8080,
        )
