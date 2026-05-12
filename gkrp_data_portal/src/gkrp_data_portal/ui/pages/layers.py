"""NiceGUI data-entry page: Layers (parity-first)."""

from __future__ import annotations

from nicegui import ui
from sqlalchemy.orm import Session

from gkrp_data_portal.db.session import session_scope
from gkrp_data_portal.models.archaeology import Tbllayer
from gkrp_data_portal.ui.repository.archaeology_repo import (
    layer_choices,
    list_layers,
    most_recent_layer_id,
)


def _row_to_dict(r: Tbllayer) -> dict:
    return {
        "layerid": r.layerid,
        "site": r.site,
        "sector": r.sector,
        "square": r.square,
        "layer": r.layer,
    }


def _save_layer(db: Session, obj: Tbllayer, data: dict) -> Tbllayer:
    """Persist layer changes.

    Commit/rollback is managed by session_scope().
    """
    for k, v in data.items():
        if hasattr(obj, k):
            setattr(obj, k, v)
    db.add(obj)
    db.flush()
    db.refresh(obj)
    return obj


@ui.page("/layers")
def page_layers() -> None:
    ui.label("Layers (tbllayers)").classes("text-h5")

    search = ui.input("Search (site/sector/square/layer)").props("clearable")

    table = ui.table(
        columns=[
            {"name": "layerid", "label": "ID", "field": "layerid", "sortable": True},
            {"name": "site", "label": "Site", "field": "site"},
            {"name": "sector", "label": "Sector", "field": "sector"},
            {"name": "square", "label": "Square", "field": "square"},
            {"name": "layer", "label": "Layer", "field": "layer"},
        ],
        rows=[],
        row_key="layerid",
        pagination=25,
    ).classes("w-full")

    def refresh() -> None:
        q = (search.value or "").strip()
        with session_scope() as db:
            res = list_layers(db, q=q if q else None)
            table.rows = [_row_to_dict(x) for x in res.items]
        table.update()

    def open_editor(layerid: int | None = None) -> None:
        with session_scope() as db:
            obj = db.get(Tbllayer, layerid) if layerid else Tbllayer()
            layer_opts = layer_choices(db)
            inferred_layer_id = most_recent_layer_id(db)

        dialog = ui.dialog()
        with dialog, ui.card().classes("w-[800px]"):
            ui.label("Edit Layer" if layerid else "Create Layer").classes("text-h6")

            ui.markdown(
                "If **Layer ID** is empty, it will be inferred as the **most recent layer** (parity with ceramics workflow)."
            ).classes("text-sm")

            with ui.grid(columns=2).classes("w-full gap-4"):
                # location selection
                layer_map = {label: lid for (lid, label) in layer_opts}
                layer_label_default = None
                if obj.layerid:
                    for lid, label in layer_opts:
                        if lid == obj.layerid:
                            layer_label_default = label
                            break

                sel_layer = ui.select(
                    options=list(layer_map.keys()),
                    value=layer_label_default,
                    label="Layer (optional)",
                ).props("clearable")

                inp_site = ui.input("site", value=obj.site or "")
                inp_sector = ui.input("sector", value=obj.sector or "")
                inp_square = ui.input("square", value=obj.square or "")
                inp_layer = ui.input("layer", value=obj.layer or "")

            with ui.row().classes("w-full justify-end"):
                ui.button("Cancel", on_click=dialog.close)

                def do_save() -> None:
                    chosen_layer_id = (
                        layer_map.get(sel_layer.value) if sel_layer.value else None
                    )
                    if chosen_layer_id is None:
                        chosen_layer_id = inferred_layer_id  # parity inference

                    with session_scope() as db:
                        obj2 = db.get(Tbllayer, layerid) if layerid else Tbllayer()
                        payload = {
                            "site": inp_site.value or None,
                            "sector": inp_sector.value or None,
                            "square": inp_square.value or None,
                            "layer": inp_layer.value or None,
                        }
                        _save_layer(db, obj2, payload)

                    dialog.close()
                    refresh()

                ui.button("Save", on_click=do_save)

        dialog.open()

    with ui.row().classes("w-full justify-between"):
        ui.button("Refresh", on_click=refresh)
        ui.button("New Layer", on_click=lambda: open_editor(None))

    def on_row_click(e) -> None:
        row = e.args.get("row") or {}
        open_editor(row.get("layerid"))

    table.on("rowClick", on_row_click)
    search.on("change", lambda: refresh())

    refresh()
