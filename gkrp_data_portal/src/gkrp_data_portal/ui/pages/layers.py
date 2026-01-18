"""NiceGUI data-entry page: Layers."""

from __future__ import annotations

from datetime import date
from typing import Optional

from nicegui import ui
from sqlalchemy.orm import Session

from gkrp_data_portal.db.session import session_scope
from gkrp_data_portal.models.archaeology import Tbllayer
from gkrp_data_portal.ui.repository.archaeology_repo import list_layers


def _row_to_dict(r: Tbllayer) -> dict:
    return {
        "layerid": r.layerid,
        "site": r.site,
        "sector": r.sector,
        "square": r.square,
        "context": r.context,
        "layername": r.layername,
        "layer": r.layer,
        "layertype": r.layertype,
        "recordenteredby": r.recordenteredby,
        "recordenteredon": str(r.recordenteredon) if r.recordenteredon else "",
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

    search = ui.input("Search (site/sector/square/layername/context)").props("clearable")

    table = ui.table(
        columns=[
            {"name": "layerid", "label": "ID", "field": "layerid", "sortable": True},
            {"name": "site", "label": "Site", "field": "site"},
            {"name": "sector", "label": "Sector", "field": "sector"},
            {"name": "square", "label": "Square", "field": "square"},
            {"name": "context", "label": "Context", "field": "context"},
            {"name": "layername", "label": "Layer Name", "field": "layername"},
            {"name": "layer", "label": "Layer", "field": "layer"},
            {"name": "layertype", "label": "Type", "field": "layertype"},
            {"name": "recordenteredby", "label": "Entered By", "field": "recordenteredby"},
            {"name": "recordenteredon", "label": "Entered On", "field": "recordenteredon"},
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

    def open_editor(layerid: Optional[int] = None) -> None:
        with session_scope() as db:
            obj = db.get(Tbllayer, layerid) if layerid else Tbllayer()

            data = {
                "layertype": obj.layertype,
                "layername": obj.layername,
                "site": obj.site,
                "sector": obj.sector,
                "square": obj.square,
                "context": obj.context,
                "layer": obj.layer,
                "stratum": obj.stratum,
                "level": obj.level,
                "structure": obj.structure,
                "includes": obj.includes,
                "color1": obj.color1,
                "color2": obj.color2,
                "handfragments": obj.handfragments,
                "wheelfragment": obj.wheelfragment,
                "recordenteredby": obj.recordenteredby,
                # recordenteredon is server default; keep as-is
                "recordcreatedby": obj.recordcreatedby,
                "recordcreatedon": obj.recordcreatedon or date.today(),
                "description": obj.description,
                "akb_num": obj.akb_num,
            }

        dialog = ui.dialog()
        with dialog, ui.card().classes("w-[900px]"):
            ui.label("Edit Layer" if layerid else "Create Layer").classes("text-h6")
            with ui.grid(columns=3).classes("w-full gap-4"):
                inp_site = ui.input("site", value=data["site"])
                inp_sector = ui.input("sector", value=data["sector"])
                inp_square = ui.input("square", value=data["square"])
                inp_context = ui.input("context", value=data["context"])
                inp_layername = ui.input("layername", value=data["layername"])
                inp_layer = ui.input("layer", value=data["layer"])
                inp_layertype = ui.input("layertype", value=data["layertype"])
                inp_stratum = ui.input("stratum", value=data.get("stratum"))
                inp_level = ui.input("level", value=data.get("level"))
                inp_structure = ui.input("structure", value=data.get("structure"))
                inp_includes = ui.input("includes", value=data.get("includes"))
                inp_color1 = ui.input("color1", value=data.get("color1"))
                inp_color2 = ui.input("color2", value=data.get("color2"))
                inp_hand = ui.number("handfragments", value=data.get("handfragments") or 0)
                inp_wheel = ui.number("wheelfragment", value=data.get("wheelfragment") or 0)
                inp_entered_by = ui.input("recordenteredby", value=data.get("recordenteredby"))
                inp_created_by = ui.input("recordcreatedby", value=data.get("recordcreatedby"))
                inp_created_on = ui.date("recordcreatedon", value=str(data["recordcreatedon"]))

                inp_desc = ui.textarea("description", value=data.get("description")).classes("col-span-3")
                inp_akb = ui.number("akb_num", value=data.get("akb_num") or 0)

            with ui.row().classes("w-full justify-end"):
                ui.button("Cancel", on_click=dialog.close)

                def do_save() -> None:
                    with session_scope() as db:
                        obj2 = db.get(Tbllayer, layerid) if layerid else Tbllayer()
                        payload = {
                            "site": inp_site.value,
                            "sector": inp_sector.value,
                            "square": inp_square.value,
                            "context": inp_context.value,
                            "layername": inp_layername.value,
                            "layer": inp_layer.value,
                            "layertype": inp_layertype.value,
                            "stratum": inp_stratum.value,
                            "level": inp_level.value,
                            "structure": inp_structure.value,
                            "includes": inp_includes.value,
                            "color1": inp_color1.value,
                            "color2": inp_color2.value,
                            "handfragments": int(inp_hand.value or 0),
                            "wheelfragment": int(inp_wheel.value or 0),
                            "recordenteredby": inp_entered_by.value,
                            "recordcreatedby": inp_created_by.value,
                            "recordcreatedon": date.fromisoformat(inp_created_on.value)
                            if inp_created_on.value
                            else date.today(),
                            "description": inp_desc.value,
                            "akb_num": int(inp_akb.value or 0),
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
