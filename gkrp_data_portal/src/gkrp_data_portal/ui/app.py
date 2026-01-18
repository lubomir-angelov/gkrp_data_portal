"""NiceGUI application entrypoint (parity-first)."""

from __future__ import annotations

from nicegui import ui

# Import pages to register routes
from gkrp_data_portal.ui.pages.layers import page_layers  # noqa: F401
from gkrp_data_portal.ui.pages.fragments import page_fragments  # noqa: F401
from gkrp_data_portal.ui.pages.ornaments import page_ornaments  # noqa: F401


@ui.page("/")
def index() -> None:
    with ui.row().classes("w-full"):
        with ui.column().classes("w-64"):
            ui.label("Navigation").classes("text-h6")
            ui.link("Layers", "/layers")
            ui.link("Fragments", "/fragments")
            ui.link("Ornaments", "/ornaments")

        with ui.column().classes("grow"):
            ui.label("GKR Portal — Data Entry").classes("text-h5")
            ui.markdown(
                "Use the navigation links on the left. This phase implements parity-first CRUD pages."
            )


def run() -> None:
    ui.run(title="GKR Data Portal", reload=False)
