"""NiceGUI data-entry page: Fragments (parity-first, with location inference)."""

from __future__ import annotations

from nicegui import ui
from sqlalchemy.orm import Session

from gkrp_data_portal.db.session import session_scope
from gkrp_data_portal.models.archaeology import Tblfragment
from gkrp_data_portal.ui.repository.archaeology_repo import (
    layer_choices,
    list_fragments,
    most_recent_layer_id,
)


def _row_to_dict(r: Tblfragment) -> dict:
    return {
        "fragmentid": r.fragmentid,
        "locationid": r.locationid,
        "piecetype": r.piecetype,
        "fragmenttype": r.fragmenttype,
        "technology": r.technology,
        "baking": r.baking,
        "primarycolor": r.primarycolor,
        "secondarycolor": r.secondarycolor,
        "count": r.count,
        "inventory": r.inventory,
        "image_url": r.image_url,
    }


def _save_fragment(db: Session, obj: Tblfragment, data: dict) -> Tblfragment:
    """Apply payload to object and persist.

    Commit/rollback is managed by session_scope().
    """
    for k, v in data.items():
        if hasattr(obj, k):
            setattr(obj, k, v)
    db.add(obj)
    db.flush()   # ensures PK assigned for new objects inside the transaction
    db.refresh(obj)
    return obj


@ui.page("/fragments")
def page_fragments() -> None:
    ui.label("Fragments (tblfragments)").classes("text-h5")

    search = ui.input("Search (inventory/note/piecetype/fragmenttype/technology)").props("clearable")

    table = ui.table(
        columns=[
            {"name": "fragmentid", "label": "ID", "field": "fragmentid", "sortable": True},
            {"name": "locationid", "label": "Layer ID", "field": "locationid", "sortable": True},
            {"name": "piecetype", "label": "Piece Type", "field": "piecetype"},
            {"name": "fragmenttype", "label": "Fragment Type", "field": "fragmenttype"},
            {"name": "technology", "label": "Technology", "field": "technology"},
            {"name": "baking", "label": "Baking", "field": "baking"},
            {"name": "primarycolor", "label": "Primary", "field": "primarycolor"},
            {"name": "secondarycolor", "label": "Secondary", "field": "secondarycolor"},
            {"name": "count", "label": "Count", "field": "count"},
            {"name": "inventory", "label": "Inventory", "field": "inventory"},
            {"name": "image_url", "label": "Image URL", "field": "image_url"},
        ],
        rows=[],
        row_key="fragmentid",
        pagination=25,
    ).classes("w-full")

    def refresh() -> None:
        q = (search.value or "").strip()
        with session_scope() as db:
            res = list_fragments(db, q=q if q else None)
            table.rows = [_row_to_dict(x) for x in res.items]
        table.update()

    def open_editor(fragmentid: int | None = None) -> None:
        with session_scope() as db:
            obj = db.get(Tblfragment, fragmentid) if fragmentid else Tblfragment()
            layer_opts = layer_choices(db)
            inferred_layer_id = most_recent_layer_id(db)

        dialog = ui.dialog()
        with dialog, ui.card().classes("w-[1100px]"):
            ui.label("Edit Fragment" if fragmentid else "Create Fragment").classes("text-h6")

            # Parity-first workflow: infer locationid if not provided.
            ui.markdown(
                "If **Layer ID** is empty, it will be inferred as the **most recent layer** (parity with ceramics workflow)."
            ).classes("text-sm")

            with ui.grid(columns=4).classes("w-full gap-4"):
                # location selection
                layer_map = {label: lid for (lid, label) in layer_opts}
                layer_label_default = None
                if obj.locationid:
                    for lid, label in layer_opts:
                        if lid == obj.locationid:
                            layer_label_default = label
                            break

                sel_layer = ui.select(
                    options=list(layer_map.keys()),
                    value=layer_label_default,
                    label="Layer (optional)",
                ).props("clearable")

                inp_piecetype = ui.input("piecetype (required)", value=obj.piecetype or "")
                inp_fragmenttype = ui.input("fragmenttype", value=obj.fragmenttype or "")
                inp_technology = ui.input("technology", value=obj.technology or "")

                inp_baking = ui.input("baking", value=obj.baking or "")
                inp_fract = ui.input("fract", value=obj.fract or "")
                inp_primary = ui.input("primarycolor", value=obj.primarycolor or "")
                inp_secondary = ui.input("secondarycolor", value=obj.secondarycolor or "")

                inp_covering = ui.input("covering", value=obj.covering or "")
                inp_includesconc = ui.input("includesconc", value=obj.includesconc or "")
                inp_includessize = ui.input("includessize", value=obj.includessize or "")
                inp_surface = ui.input("surface", value=obj.surface or "")

                inp_wall = ui.input("wallthickness", value=obj.wallthickness or "")
                inp_handle_size = ui.input("handlesize", value=obj.handlesize or "")
                inp_handle_type = ui.input("handletype", value=obj.handletype or "")
                inp_dishsize = ui.input("dishsize", value=obj.dishsize or "")

                inp_bottomtype = ui.input("bottomtype", value=obj.bottomtype or "")
                inp_outline = ui.input("outline", value=obj.outline or "")
                inp_category = ui.input("category", value=obj.category or "")
                inp_form = ui.input("form", value=obj.form or "")

                inp_type = ui.number("type", value=obj.type or 0)
                inp_subtype = ui.input("subtype", value=obj.subtype or "")
                inp_variant = ui.number("variant", value=obj.variant or 0)
                inp_onepot = ui.input("onepot", value=obj.onepot or "")

                inp_count = ui.number("count (required)", value=obj.count or 1)
                inp_inventory = ui.input("inventory", value=obj.inventory or "")
                inp_entered_by = ui.input("recordenteredby", value=obj.recordenteredby or "")
                inp_recordenteredon = ui.input("recordenteredon (legacy str)", value=obj.recordenteredon or "")

                inp_note = ui.textarea("note", value=obj.note or "").classes("col-span-4")
                inp_image_url = ui.input("image_url", value=obj.image_url or "").classes("col-span-4")

            with ui.row().classes("w-full justify-end"):
                ui.button("Cancel", on_click=dialog.close)

                def do_save() -> None:
                    chosen_layer_id = layer_map.get(sel_layer.value) if sel_layer.value else None
                    if chosen_layer_id is None:
                        chosen_layer_id = inferred_layer_id  # parity inference

                    if not inp_piecetype.value:
                        ui.notify("piecetype is required", type="negative")
                        return
                    if not inp_count.value:
                        ui.notify("count is required", type="negative")
                        return

                    with session_scope() as db:
                        obj2 = db.get(Tblfragment, fragmentid) if fragmentid else Tblfragment()
                        payload = {
                            "locationid": chosen_layer_id,
                            "piecetype": inp_piecetype.value,
                            "fragmenttype": inp_fragmenttype.value or None,
                            "technology": inp_technology.value or None,
                            "baking": inp_baking.value or None,
                            "fract": inp_fract.value or None,
                            "primarycolor": inp_primary.value or None,
                            "secondarycolor": inp_secondary.value or None,
                            "covering": inp_covering.value or None,
                            "includesconc": inp_includesconc.value or None,
                            "includessize": inp_includessize.value or None,
                            "surface": inp_surface.value or None,
                            "wallthickness": inp_wall.value or None,
                            "handlesize": inp_handle_size.value or None,
                            "handletype": inp_handle_type.value or None,
                            "dishsize": inp_dishsize.value or None,
                            "bottomtype": inp_bottomtype.value or None,
                            "outline": inp_outline.value or None,
                            "category": inp_category.value or None,
                            "form": inp_form.value or None,
                            "type": int(inp_type.value) if inp_type.value is not None else None,
                            "subtype": inp_subtype.value or None,
                            "variant": int(inp_variant.value) if inp_variant.value is not None else None,
                            "onepot": inp_onepot.value or None,
                            "count": int(inp_count.value),
                            "inventory": inp_inventory.value or None,
                            "recordenteredby": inp_entered_by.value or None,
                            "recordenteredon": inp_recordenteredon.value or None,
                            "note": inp_note.value or None,
                            "image_url": inp_image_url.value or None,
                        }
                        _save_fragment(db, obj2, payload)

                    dialog.close()
                    refresh()

                ui.button("Save", on_click=do_save)

        dialog.open()

    with ui.row().classes("w-full justify-between"):
        ui.button("Refresh", on_click=refresh)
        ui.button("New Fragment", on_click=lambda: open_editor(None))

    def on_row_click(e) -> None:
        row = e.args.get("row") or {}
        open_editor(row.get("fragmentid"))

    table.on("rowClick", on_row_click)
    search.on("change", lambda: refresh())

    refresh()
