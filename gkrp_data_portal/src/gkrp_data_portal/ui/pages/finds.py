"""NiceGUI data-entry page: Finds (archaeological finds)."""

from __future__ import annotations

from nicegui import ui
from sqlalchemy.orm import Session

from gkrp_data_portal.db.session import session_scope
from gkrp_data_portal.models.archaeology import Find
from gkrp_data_portal.ui.repository.archaeology_repo import (
    layer_choices,
    list_finds,
    most_recent_layer_id,
)
from gkrp_data_portal.ui.lang import t


def _row_to_dict(r: Find) -> dict:
    return {
        "findid": r.findid,
        "layerid": r.layerid,
        "year": r.year,
        "inv_no": r.inv_no,
        "find_type": r.find_type,
        "material": r.material,
        "description": r.description,
        "coin": r.coin,
        "denomination": r.denomination,
        "mint": r.mint,
        "dimensions_cm": r.dimensions_cm,
        "weight_g": r.weight_g,
        "depth_m": r.depth_m,
        "context": r.context,
        "coord_north_m": r.coord_north_m,
        "coord_east_m": r.coord_east_m,
        "photo": r.photo,
        "drw_link": r.drw_link,
        "inventory": r.inventory if hasattr(r, "inventory") else None,
    }


def _save_find(db: Session, obj: Find, data: dict) -> Find:
    """Apply payload to object and persist."""
    for k, v in data.items():
        if hasattr(obj, k):
            setattr(obj, k, v)
    db.add(obj)
    db.flush()
    db.refresh(obj)
    return obj


@ui.page("/finds")
def page_finds() -> None:
    ui.label(t("title_finds")).classes("text-h5 text-blue-600")

    search = ui.input(t("search_finds")).props("clearable")

    table = ui.table(
        columns=[
            {"name": "findid", "label": t("col_id"), "field": "findid", "sortable": True},
            {"name": "year", "label": t("col_year"), "field": "year"},
            {"name": "inv_no", "label": t("col_inventory"), "field": "inv_no"},
            {"name": "find_type", "label": t("col_find_type"), "field": "find_type"},
            {"name": "material", "label": t("col_material"), "field": "material"},
            {"name": "description", "label": t("col_description"), "field": "description"},
            {"name": "coin", "label": t("col_coin"), "field": "coin"},
            {"name": "mint", "label": t("col_mint"), "field": "mint"},
            {"name": "depth_m", "label": t("col_depth_m"), "field": "depth_m"},
            {"name": "context", "label": t("col_context"), "field": "context"},
            {"name": "coord_north_m", "label": t("col_coord_north_m"), "field": "coord_north_m"},
            {"name": "coord_east_m", "label": t("col_coord_east_m"), "field": "coord_east_m"},
            {"name": "photo", "label": t("col_photo"), "field": "photo"},
        ],
        rows=[],
        row_key="findid",
        pagination=25,
    ).classes("w-full")

    def refresh() -> None:
        q = (search.value or "").strip()
        with session_scope() as db:
            res = list_finds(db, q=q if q else None)
            table.rows = [_row_to_dict(x) for x in res.items]
        table.update()

    def open_editor(findid: int | None = None) -> None:
        with session_scope() as db:
            obj = db.get(Find, findid) if findid else Find()
            layer_opts = layer_choices(db)
            inferred_layer_id = most_recent_layer_id(db)

        dialog = ui.dialog()
        with dialog, ui.card().classes("w-[1100px]"):
            ui.label(t("dialog_edit_find") if findid else t("dialog_create_find")).classes("text-h6 text-blue-600")

            with ui.grid(columns=4).classes("w-full gap-4"):
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
                    label=t("label_layer_optional"),
                ).props("clearable")

                inp_year = ui.number(t("label_year"), value=obj.year or None)
                inp_inv_no = ui.number(t("label_inv_no"), value=obj.inv_no or None)
                inp_find_type = ui.input(t("label_find_type"), value=obj.find_type or "")
                inp_material = ui.input(t("label_material"), value=obj.material or "")
                inp_description = ui.textarea(t("label_description"), value=obj.description or "").classes("col-span-2")
                inp_coin = ui.input(t("label_coin"), value=obj.coin or "")
                inp_denomination = ui.input(t("label_denomination"), value=obj.denomination or "")
                inp_mint = ui.input(t("label_mint"), value=obj.mint or "")
                inp_dimensions_cm = ui.input(t("label_dimensions_cm"), value=obj.dimensions_cm or "")
                inp_weight_g = ui.number(t("label_weight_g"), value=obj.weight_g or None)
                inp_depth_m = ui.input(t("label_depth_m"), value=obj.depth_m or "")
                inp_context = ui.input(t("label_context"), value=obj.context or "")
                inp_coord_north = ui.input(t("label_coord_north_m"), value=obj.coord_north_m or "")
                inp_coord_east = ui.input(t("label_coord_east_m"), value=obj.coord_east_m or "")
                inp_photo = ui.input(t("label_photo"), value=obj.photo or "")
                inp_drw_link = ui.input(t("label_drw_link"), value=obj.drw_link or "")
                inp_entered_by = ui.input(t("label_entered_by"), value=obj.recordenteredby or "")

            with ui.row().classes("w-full justify-end"):
                ui.button(t("btn_cancel"), on_click=dialog.close)

                def do_save() -> None:
                    chosen_layer_id = layer_map.get(sel_layer.value) if sel_layer.value else None
                    if chosen_layer_id is None:
                        chosen_layer_id = inferred_layer_id

                    with session_scope() as db:
                        obj2 = db.get(Find, findid) if findid else Find()
                        payload = {
                            "layerid": chosen_layer_id,
                            "year": int(inp_year.value) if inp_year.value is not None else None,
                            "inv_no": int(inp_inv_no.value) if inp_inv_no.value is not None else None,
                            "find_type": inp_find_type.value or None,
                            "material": inp_material.value or None,
                            "description": inp_description.value or None,
                            "coin": inp_coin.value or None,
                            "denomination": inp_denomination.value or None,
                            "mint": inp_mint.value or None,
                            "dimensions_cm": inp_dimensions_cm.value or None,
                            "weight_g": float(inp_weight_g.value) if inp_weight_g.value is not None else None,
                            "depth_m": inp_depth_m.value or None,
                            "context": inp_context.value or None,
                            "coord_north_m": inp_coord_north.value or None,
                            "coord_east_m": inp_coord_east.value or None,
                            "photo": inp_photo.value or None,
                            "drw_link": inp_drw_link.value or None,
                            "recordenteredby": inp_entered_by.value or None,
                        }
                        _save_find(db, obj2, payload)

                    dialog.close()
                    refresh()

                ui.button(t("btn_save"), on_click=do_save)

        dialog.open()

    with ui.row().classes("w-full justify-between"):
        ui.button(t("btn_refresh"), on_click=refresh)
        ui.button(t("btn_new_find"), on_click=lambda: open_editor(None))

    def on_row_click(e) -> None:
        row = e.args.get("row") or {}
        open_editor(row.get("findid"))

    table.on("rowClick", on_row_click)
    search.on("change", lambda: refresh())

    refresh()
