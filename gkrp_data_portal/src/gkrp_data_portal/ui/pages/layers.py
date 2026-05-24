"""NiceGUI data-entry page: Layers (parity-first)."""

from __future__ import annotations

from nicegui import ui
from sqlalchemy.orm import Session

from gkrp_data_portal.db.session import session_scope
from gkrp_data_portal.models.archaeology import Tbllayer
from gkrp_data_portal.ui.repository.archaeology_repo import (
    column_distinct,
    layer_choices,
    list_layers,
    most_recent_layer_id,
)
from gkrp_data_portal.ui.lang import t


def _row_to_dict(r: Tbllayer) -> dict:
    return {
        "layerid": r.layerid,
        "site": r.site,
        "sector": r.sector,
        "square": r.square,
        "layer": r.layer,
        "layertype": r.layertype,
        "layername": r.layername,
        "context": r.context,
        "stratum": r.stratum,
        "level": r.level,
        "structure": r.structure,
        "color1": r.color1,
        "color2": r.color2,
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
    ui.label(t("title_layers")).classes("text-h5 text-blue-600")

    search = ui.input(t("search_layers")).props("clearable").classes("w-[500px]")

    filter_widgets: dict[str, ui.select] = {}
    filter_cols = [
        "site",
        "sector",
        "square",
        "layer",
        "layertype",
        "layername",
        "context",
        "stratum",
        "level",
        "structure",
        "color1",
        "color2",
    ]
    filter_labels = {
        "site": t("label_site"),
        "sector": t("label_sector"),
        "square": t("label_square"),
        "layer": t("label_layer"),
        "layertype": t("label_layertype"),
        "layername": t("label_layername"),
        "context": t("label_context"),
        "stratum": t("label_stratum"),
        "level": t("label_level"),
        "structure": t("label_structure"),
        "color1": t("label_color1"),
        "color2": t("label_color2"),
    }

    def refresh() -> None:
        q = (search.value or "").strip()
        filters = {col: sel.value for col, sel in filter_widgets.items() if sel.value}
        with session_scope() as db:
            res = list_layers(
                db,
                q=q if q else None,
                filters=filters or None,
            )
            table.rows = [_row_to_dict(x) for x in res.items]
        table.update()

    table_columns = [
        {
            "name": "layerid",
            "label": t("col_id"),
            "field": "layerid",
            "sortable": True,
        },
        {"name": "site", "label": t("label_site"), "field": "site"},
        {"name": "sector", "label": t("label_sector"), "field": "sector"},
        {"name": "square", "label": t("label_square"), "field": "square"},
        {"name": "layer", "label": t("label_layer"), "field": "layer"},
        {"name": "layertype", "label": t("label_layertype"), "field": "layertype"},
        {"name": "layername", "label": t("label_layername"), "field": "layername"},
        {"name": "context", "label": t("label_context"), "field": "context"},
        {"name": "stratum", "label": t("label_stratum"), "field": "stratum"},
        {"name": "level", "label": t("label_level"), "field": "level"},
        {"name": "structure", "label": t("label_structure"), "field": "structure"},
        {"name": "color1", "label": t("label_color1"), "field": "color1"},
        {"name": "color2", "label": t("label_color2"), "field": "color2"},
    ]

    # Order filter columns to match their position in table_columns
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
                    opts = column_distinct(db, Tbllayer, col)
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
            row_key="layerid",
            pagination=25,
        ).classes("w-full")

    def open_editor(layerid: int | None = None) -> None:
        with session_scope() as db:
            obj = db.get(Tbllayer, layerid) if layerid else Tbllayer()
            layer_opts = layer_choices(db)
            inferred_layer_id = most_recent_layer_id(db)

        dialog = ui.dialog()
        with dialog, ui.card().classes("w-[800px]"):
            ui.label(
                t("dialog_edit_layer") if layerid else t("dialog_create_layer")
            ).classes("text-h6 text-blue-600")

            ui.markdown(t("dialog_layer_hint")).classes("text-sm")

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
                    label=t("label_layer_optional"),
                ).props("clearable")

                inp_site = ui.input("site", value=obj.site or "")
                inp_sector = ui.input("sector", value=obj.sector or "")
                inp_square = ui.input("square", value=obj.square or "")
                inp_layer = ui.input("layer", value=obj.layer or "")

            with ui.row().classes("w-full justify-end"):
                ui.button(t("btn_cancel"), on_click=dialog.close)

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

                ui.button(t("btn_save"), on_click=do_save)

        dialog.open()

    with ui.row().classes("w-full justify-end"):
        ui.button(t("btn_new_layer"), on_click=lambda: open_editor(None))

    def on_row_click(e) -> None:
        row = e.args.get("row") or {}
        open_editor(row.get("layerid"))

    table.on("rowClick", on_row_click)
    search.on("change", lambda: refresh())
    for sel in filter_widgets.values():
        sel.on("change", lambda: refresh())

    refresh()
