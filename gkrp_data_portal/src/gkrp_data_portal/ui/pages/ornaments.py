"""NiceGUI data-entry page: Ornaments (parity-first, with fragment inference)."""

from __future__ import annotations

from nicegui import ui
from sqlalchemy.orm import Session

from gkrp_data_portal.db.session import session_scope
from gkrp_data_portal.models.archaeology import Tblornament
from gkrp_data_portal.ui.repository.archaeology_repo import (
    fragment_choices,
    list_ornaments,
    most_recent_fragment_id,
)


def _row_to_dict(r: Tblornament) -> dict:
    return {
        "ornamentid": r.ornamentid,
        "fragmentid": r.fragmentid,
        "location": r.location,
        "primary_": r.primary_,
        "secondary": r.secondary,
        "tertiary": r.tertiary,
        "color1": r.color1,
        "color2": r.color2,
    }


def _save_ornament(db: Session, obj: Tblornament, data: dict) -> Tblornament:
    """Persist ornament changes.

    Commit/rollback is managed by session_scope().
    """
    for k, v in data.items():
        if hasattr(obj, k):
            setattr(obj, k, v)
    db.add(obj)
    db.flush()
    db.refresh(obj)
    return obj


@ui.page("/ornaments")
def page_ornaments() -> None:
    ui.label("Ornaments (tblornaments)").classes("text-h5")

    search = ui.input("Search (location/primary/secondary/tertiary)").props("clearable")

    table = ui.table(
        columns=[
            {"name": "ornamentid", "label": "ID", "field": "ornamentid", "sortable": True},
            {"name": "fragmentid", "label": "Fragment ID", "field": "fragmentid", "sortable": True},
            {"name": "location", "label": "Location", "field": "location"},
            {"name": "primary_", "label": "Primary", "field": "primary_"},
            {"name": "secondary", "label": "Secondary", "field": "secondary"},
            {"name": "tertiary", "label": "Tertiary", "field": "tertiary"},
            {"name": "color1", "label": "Color1", "field": "color1"},
            {"name": "color2", "label": "Color2", "field": "color2"},
        ],
        rows=[],
        row_key="ornamentid",
        pagination=25,
    ).classes("w-full")

    def refresh() -> None:
        q = (search.value or "").strip()
        with session_scope() as db:
            res = list_ornaments(db, q=q if q else None)
            table.rows = [_row_to_dict(x) for x in res.items]
        table.update()

    def open_editor(ornamentid: int | None = None) -> None:
        with session_scope() as db:
            obj = db.get(Tblornament, ornamentid) if ornamentid else Tblornament()
            frag_opts = fragment_choices(db)
            inferred_fragment_id = most_recent_fragment_id(db)

        dialog = ui.dialog()
        with dialog, ui.card().classes("w-[1000px]"):
            ui.label("Edit Ornament" if ornamentid else "Create Ornament").classes("text-h6")

            ui.markdown(
                "If **Fragment ID** is empty, it will be inferred as the **most recent fragment** (parity with ceramics workflow)."
            ).classes("text-sm")

            with ui.grid(columns=4).classes("w-full gap-4"):
                frag_map = {label: fid for (fid, label) in frag_opts}
                frag_label_default = None
                if obj.fragmentid:
                    for fid, label in frag_opts:
                        if fid == obj.fragmentid:
                            frag_label_default = label
                            break

                sel_fragment = ui.select(
                    options=list(frag_map.keys()),
                    value=frag_label_default,
                    label="Fragment (optional)",
                ).props("clearable")

                inp_location = ui.input("location", value=obj.location or "")
                inp_relationship = ui.input(
                    "relationship",
                    value=getattr(obj, "relationship_type", None) or "",
                )
                inp_onornament = ui.number("onornament", value=obj.onornament or 0)

                inp_color1 = ui.input("color1", value=getattr(obj, "color1", None) or "")
                inp_color2 = ui.input("color2", value=getattr(obj, "color2", None) or "")
                inp_en1 = ui.input("encrustcolor1", value=obj.encrustcolor1 or "")
                inp_en2 = ui.input("encrustcolor2", value=obj.encrustcolor2 or "")

                inp_primary = ui.input("primary_", value=obj.primary_ or "")
                inp_secondary = ui.input("secondary", value=obj.secondary or "")
                inp_tertiary = ui.input("tertiary", value=obj.tertiary or "")
                inp_quarter = ui.number("quarternary", value=obj.quarternary or 0)

            with ui.row().classes("w-full justify-end"):
                ui.button("Cancel", on_click=dialog.close)

                def do_save() -> None:
                    chosen_fragment_id = frag_map.get(sel_fragment.value) if sel_fragment.value else None
                    if chosen_fragment_id is None:
                        chosen_fragment_id = inferred_fragment_id  # parity inference

                    with session_scope() as db:
                        obj2 = db.get(Tblornament, ornamentid) if ornamentid else Tblornament()
                        payload = {
                            "fragmentid": chosen_fragment_id,
                            "location": inp_location.value or None,
                            # DB column is "relationship", model attribute may be relationship_type
                            "relationship_type": inp_relationship.value or None,
                            "onornament": int(inp_onornament.value)
                            if inp_onornament.value is not None
                            else None,
                            "color1": inp_color1.value or None,
                            "color2": inp_color2.value or None,
                            "encrustcolor1": inp_en1.value or None,
                            "encrustcolor2": inp_en2.value or None,
                            "primary_": inp_primary.value or None,
                            "secondary": inp_secondary.value or None,
                            "tertiary": inp_tertiary.value or None,
                            "quarternary": int(inp_quarter.value)
                            if inp_quarter.value is not None
                            else None,
                        }
                        _save_ornament(db, obj2, payload)

                    dialog.close()
                    refresh()

                ui.button("Save", on_click=do_save)

        dialog.open()

    with ui.row().classes("w-full justify-between"):
        ui.button("Refresh", on_click=refresh)
        ui.button("New Ornament", on_click=lambda: open_editor(None))

    def on_row_click(e) -> None:
        row = e.args.get("row") or {}
        open_editor(row.get("ornamentid"))

    table.on("rowClick", on_row_click)
    search.on("change", lambda: refresh())

    refresh()
