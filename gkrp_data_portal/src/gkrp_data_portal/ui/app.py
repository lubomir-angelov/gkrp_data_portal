"""NiceGUI application entrypoint (parity-first)."""

from __future__ import annotations

from nicegui import app, ui

from gkrp_data_portal.ui.lang import get_lang_button_label, toggle_lang, t
from gkrp_data_portal.ui.pages.analytics_common import LOCALE  # noqa: F401

# Import finds page to register route
from gkrp_data_portal.ui.pages.finds import page_finds  # noqa: F401

# Import pages to register routes
from gkrp_data_portal.ui.pages.layers import page_layers  # noqa: F401
from gkrp_data_portal.ui.pages.fragments import page_fragments  # noqa: F401
from gkrp_data_portal.ui.pages.ornaments import page_ornaments  # noqa: F401
from gkrp_data_portal.ui.pages.admin import page_admin  # noqa: F401
from gkrp_data_portal.ui.pages.accept_invite import page_accept_invite  # noqa: F401
from gkrp_data_portal.ui.pages.dev_login import page_dev_login  # noqa: F401
from gkrp_data_portal.ui.pages.analytics_chart import (
    page_analytics_index,  # noqa: F401
    page_analytics_chart,  # noqa: F401
)
from gkrp_data_portal.ui.pages.analytics_chart_fragments import (
    page_analytics_chart_fragments,  # noqa: F401
)
from gkrp_data_portal.ui.pages.analytics_chart_finds import page_analytics_chart_finds  # noqa: F401
from gkrp_data_portal.ui.pages.analytics_table import page_analytics_table  # noqa: F401


# settings
from gkrp_data_portal.core.settings import get_storage_secret


# Global: inject language-sync script on every page connection.
# When language changes, reload the page to pick up new translations.
@app.on_connect
def _handle_connect(_client) -> None:
    ui.run_javascript("""
        window.addEventListener('gkrp-lang-change', () => {
            setTimeout(() => window.location.reload(), 100);
        });
    """)


@ui.page("/")
def index() -> None:
    with ui.row().classes("w-full"):
        with ui.column().classes("w-64"):
            with ui.row().classes("w-full items-center justify-between"):
                ui.label(t("nav_navigation")).classes("text-h6 text-blue-600")
                ui.button(
                    get_lang_button_label(),
                    on_click=toggle_lang,
                    icon="translate",
                ).classes("text-xs cursor-pointer")

            ui.link(t("nav_layers"), "/layers")
            ui.link(t("nav_fragments"), "/fragments")
            ui.link(t("nav_ornaments"), "/ornaments")
            ui.link(t("nav_finds"), "/finds")
            ui.link(t("nav_admin"), "/admin")
            ui.link(t("nav_analytics"), "/analytics")

        with ui.column().classes("grow"):
            ui.label(t("nav_welcome_title")).classes("text-h5 text-blue-600")
            ui.markdown(t("nav_welcome_text"))


def run() -> None:
    ui.run(
        title="GKR Data Portal",
        reload=False,
        storage_secret=get_storage_secret(),
        host="0.0.0.0",
        port=8888,
    )
