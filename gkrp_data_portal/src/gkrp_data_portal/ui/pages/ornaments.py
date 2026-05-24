"""NiceGUI data-entry page: Ornaments (parity-first, with fragment inference)."""

from __future__ import annotations

from nicegui import ui
from sqlalchemy.orm import Session

from gkrp_data_portal.db.session import session_scope
from gkrp_data_portal.models.archaeology import Tblornament
from gkrp_data_portal.ui.repository.archaeology_repo import (
    column_distinct,
    fragment_choices,
    list_ornaments,
    most_recent_fragment_id,
)
from gkrp_data_portal.ui.lang import t


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
    ui.label(t("title_ornaments")).classes("text-h5 text-blue-600")

    search = ui.input(t("search_ornaments")).props("clearable").classes("w-[500px]")

    filter_widgets: dict[str, ui.select] = {}
    filter_cols = ["location", "primary_", "secondary", "tertiary", "color1", "color2"]
    filter_labels = {
        "location": t("col_location"),
        "primary_": t("col_primary_"),
        "secondary": t("col_secondary"),
        "tertiary": t("col_tertiary"),
        "color1": t("col_color1"),
        "color2": t("col_color2"),
    }

    def refresh() -> None:
        q = (search.value or "").strip()
        filters = {col: sel.value for col, sel in filter_widgets.items() if sel.value}
        with session_scope() as db:
            res = list_ornaments(
                db,
                q=q if q else None,
                filters=filters or None,
            )
            table.rows = [_row_to_dict(x) for x in res.items]
        table.update()

    table_columns = [
        {
            "name": "ornamentid",
            "label": t("col_id"),
            "field": "ornamentid",
            "sortable": True,
        },
        {
            "name": "fragmentid",
            "label": t("col_fragment_id"),
            "field": "fragmentid",
            "sortable": True,
        },
        {"name": "location", "label": t("col_location"), "field": "location"},
        {"name": "primary_", "label": t("col_primary_"), "field": "primary_"},
        {"name": "secondary", "label": t("col_secondary"), "field": "secondary"},
        {"name": "tertiary", "label": t("col_tertiary"), "field": "tertiary"},
        {"name": "color1", "label": t("col_color1"), "field": "color1"},
        {"name": "color2", "label": t("col_color2"), "field": "color2"},
    ]

    ordered_filter_cols = sorted(
        filter_cols,
        key=lambda c: next(
            (i for i, col in enumerate(table_columns) if col["name"] == c), 99
        ),
    )

    with ui.column().classes("w-full"):
        with ui.row().classes("w-full items-center gap-2 flex-wrap"):
            ui.button(t("btn_refresh"), on_click=refresh)
            with session_scope() as db:
                for col in ordered_filter_cols:
                    opts = column_distinct(db, Tblornament, col)
                    sel = (
                        ui.select(
                            options=opts,
                            multiple=True,
                            label=filter_labels[col],
                        )
                        .props("clearable use-chips dense")
                        .classes("min-w-[130px] flex-1")
                    )
                    filter_widgets[col] = sel

        table = ui.table(
            columns=table_columns,
            rows=[],
            row_key="ornamentid",
            pagination=25,
        ).classes("w-full")

    def open_editor(ornamentid: int | None = None) -> None:
        with session_scope() as db:
            obj = db.get(Tblornament, ornamentid) if ornamentid else Tblornament()
            frag_opts = fragment_choices(db)
            inferred_fragment_id = most_recent_fragment_id(db)

        dialog = ui.dialog()
        with dialog, ui.card().classes("w-[1000px]"):
            ui.label(
                t("dialog_edit_ornament") if ornamentid else t("dialog_create_ornament")
            ).classes("text-h6 text-blue-600")

            ui.markdown(t("dialog_ornament_hint")).classes("text-sm")

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
                    label=t("label_fragment_optional"),
                ).props("clearable")

                inp_location = ui.input("location", value=obj.location or "")
                inp_relationship = ui.input(
                    "relationship",
                    value=getattr(obj, "relationship_type", None) or "",
                )
                inp_onornament = ui.number("onornament", value=obj.onornament or 0)

                inp_color1 = ui.input(
                    "color1", value=getattr(obj, "color1", None) or ""
                )
                inp_color2 = ui.input(
                    "color2", value=getattr(obj, "color2", None) or ""
                )
                inp_en1 = ui.input("encrustcolor1", value=obj.encrustcolor1 or "")
                inp_en2 = ui.input("encrustcolor2", value=obj.encrustcolor2 or "")

                inp_primary = ui.input("primary_", value=obj.primary_ or "")
                inp_secondary = ui.input("secondary", value=obj.secondary or "")
                inp_tertiary = ui.input("tertiary", value=obj.tertiary or "")
                inp_quarter = ui.number("quarternary", value=obj.quarternary or 0)

            with ui.row().classes("w-full justify-end"):
                ui.button(t("btn_cancel"), on_click=dialog.close)

                def do_save() -> None:
                    chosen_fragment_id = (
                        frag_map.get(sel_fragment.value) if sel_fragment.value else None
                    )
                    if chosen_fragment_id is None:
                        chosen_fragment_id = inferred_fragment_id  # parity inference

                    with session_scope() as db:
                        obj2 = (
                            db.get(Tblornament, ornamentid)
                            if ornamentid
                            else Tblornament()
                        )
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

                ui.button(t("btn_save"), on_click=do_save)

        dialog.open()

    with ui.row().classes("w-full justify-end"):
        ui.button(t("btn_new_ornament"), on_click=lambda: open_editor(None))

    def on_row_click(e) -> None:
        row = e.args.get("row") or {}
        open_editor(row.get("ornamentid"))

    table.on("rowClick", on_row_click)
    search.on("change", lambda: refresh())
    for sel in filter_widgets.values():
        sel.on("change", lambda: refresh())

    refresh()
