"""NiceGUI page: Analytics (CHART only).

Layout:
- Left: query selector, filters
- Center: chart
- Right: Fragments filter panel (multi-select dropdowns)
"""

from __future__ import annotations

import csv
import io
import json
import pathlib
from typing import Any

import markdown
from loguru import logger
from nicegui import app, ui
from starlette.responses import HTMLResponse, PlainTextResponse, Response

from .analytics_common import (
    CHART_MAX_FETCH,
    DEFAULT_LIMIT,
    LOCALE,
    QUERY_OPTIONS,
    TABLE_MAX_LIMIT,
    build_histogram,
    build_histogram_series,
    parse_date,
    plotly_bar,
    plotly_donut,
    plotly_grouped_bar,
    plotly_pie,
    result_for,
    ui_columns,
    _column_to_label,
)
from gkrp_data_portal.db.session import session_scope
from gkrp_data_portal.ui.repository.analytics_repo import (
    get_distinct_values,
    get_layer_hierarchy,
)

_PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[5]
_CHART_GUIDE_PATH = _PROJECT_ROOT / "CHART.md"


def _load_chart_guide() -> str:
    """Load and render CHART.md as HTML."""
    if _CHART_GUIDE_PATH.exists():
        md = _CHART_GUIDE_PATH.read_text(encoding="utf-8")
        return markdown.markdown(md, extensions=["tables", "fenced_code"])
    return "<p>Chart guide not found.</p>"


@ui.page("/analytics")
def page_analytics_index() -> None:
    ui.label(LOCALE["title_analytics"]).classes("text-h5 text-blue-600")
    with ui.row().classes("gap-2"):
        ui.button(
            LOCALE["btn_chart_view"],
            on_click=lambda: ui.navigate.to("/analytics/chart"),
            icon="bar_chart",
        )
        ui.button(
            LOCALE["btn_table_view"],
            on_click=lambda: ui.navigate.to("/analytics/table"),
            icon="table_chart",
        )


@ui.page("/analytics/chart")
def page_analytics_chart() -> None:
    ui.label(LOCALE["title_analytics_chart"]).classes("text-h5 text-blue-600")

    state: dict[str, Any] = {
        "query_id": "q2",
        "_refreshing": False,
        "_suppress_x_change": False,
        "_hierarchy": {},
        "_all_sites": [],
        "_all_sectors": [],
        "_all_squares": [],
        "_all_layers": [],
    }

    with ui.row().classes("w-full gap-4 items-start flex-nowrap"):
        # Left panel
        with ui.column().classes("w-[340px] shrink-0"):
            ui.label(LOCALE["panel_query_filters"]).classes("text-subtitle1 font-medium text-blue-600")

            sel_query = ui.select(
                options=list(QUERY_OPTIONS.keys()),
                value=LOCALE["query_filter2"],
                label=LOCALE["label_predefined_query"],
            ).classes("w-full")

            with ui.row().classes("w-full gap-2 items-center"):
                btn_run = ui.button(LOCALE["btn_run_query"], icon="play_arrow").classes("flex-1")

            with ui.scroll_area().classes(
                "w-full h-[320px] border rounded p-2 bg-white"
            ):
                sel_site = (
                    ui.select(
                        options=[],
                        label=LOCALE["label_site"],
                        multiple=True,
                        clearable=True,
                        with_input=True,
                    )
                    .classes("w-full")
                    .props("dense")
                )
                sel_sector = (
                    ui.select(
                        options=[],
                        multiple=True,
                        clearable=True,
                        with_input=True,
                        label=LOCALE["label_sector"],
                    )
                    .classes("w-full")
                    .props("dense")
                )
                sel_square = (
                    ui.select(
                        options=[],
                        multiple=True,
                        clearable=True,
                        with_input=True,
                        label=LOCALE["label_square"],
                    )
                    .classes("w-full")
                    .props("dense")
                )
                sel_layer = (
                    ui.select(
                        options=[],
                        multiple=True,
                        clearable=True,
                        with_input=True,
                        label=LOCALE["label_layer"],
                    )
                    .classes("w-full")
                    .props("dense")
                )

            sel_limit = ui.select(
                options=[100, 200, 500, 1000, 2500, 5000, "max"],
                value=DEFAULT_LIMIT,
                label=LOCALE["label_limit"],
            ).classes("w-full")
            ui.label(LOCALE["limit_max_info"]).classes("text-xs text-gray-400 mt-1")

        # Center panel (chart only)
        with ui.column().classes("flex-1 min-w-0"):
            with ui.row().classes("w-full items-center justify-between"):
                ui.label(LOCALE["panel_chart"]).classes("text-subtitle1 font-medium text-blue-600")
                with ui.column().classes("items-center gap-0"):
                    ui.label(LOCALE["chart_help_label"]).classes("text-subtitle2 text-blue-600")
                    help_btn = ui.button(
                        icon="help",
                    ).classes("p-1").style("font-size: 1.2rem;")
                    help_btn.on("click", lambda: help_dialog.open())
            status = ui.label("").classes("text-sm text-gray-600")
            dbg = ui.label("").classes("text-xs text-gray-500")
            chart_type_debug = ui.label("").classes("text-xs text-blue-600")

            chart = (
                ui.plotly({"data": [], "layout": {"height": 520}})
                .classes("w-full border rounded bg-white")
                .style("height: 520px;")
            )
            chart_id = chart.id

            with ui.row().classes("w-full items-center justify-between gap-2"):
                with ui.column().classes("gap-0"):
                    sel_x = ui.select(options=[], label=LOCALE["label_group_by"]).classes(
                        "w-[300px]"
                    )
                    ui.label(
                        "Основната размерност, по която графиката е групирана (напр. Обект, Сектор, Квадрат)."
                    ).classes("text-xs text-gray-400")
                with ui.column().classes("gap-0"):
                    sel_series = ui.select(
                        options=[],
                        label=LOCALE["label_series"],
                        clearable=True,
                    ).classes("w-[200px]")
                    ui.label(
                        "По избор: разделя стълбовете на групирани следи по втора размерност (напр. Тип Отломък, Технология, Повърхност)."
                    ).classes("text-xs text-gray-400")
                with ui.column().classes("gap-0"):
                    sel_chart_type = ui.select(
                        options=["Bar", "Pie", "Donut"],
                        value="Pie",
                        label=LOCALE["label_chart_type"],
                    ).classes("w-[160px]")
                    ui.label(
                        "Стълб показва групирани стълбове, Кръг/Поничка показват пропорции."
                    ).classes("text-xs text-gray-400")

                with ui.row().classes("gap-2"):
                    ui.button(
                        LOCALE["btn_download_png"],
                        on_click=lambda: ui.run_javascript(
                            f"""
                            (function() {{
                              const el = document.getElementById('{chart_id}');
                              if (!el) return;
                              const gd = el.querySelector('.js-plotly-plot') || el;
                              if (window.Plotly && gd) {{
                                Plotly.downloadImage(gd, {{format:'png', filename:'analytics_chart', height:650, width:1100}});
                              }}
                            }})();
                            """
                        ),
                    )
                    ui.button(
                        LOCALE["btn_download_jpg"],
                        on_click=lambda: ui.run_javascript(
                            f"""
                            (function() {{
                              const el = document.getElementById('{chart_id}');
                              if (!el) return;
                              const gd = el.querySelector('.js-plotly-plot') || el;
                              if (window.Plotly && gd) {{
                                Plotly.downloadImage(gd, {{format:'jpeg', filename:'analytics_chart', height:650, width:1100}});
                              }}
                            }})();
                            """
                        ),
                    )
                    ui.button(
                        LOCALE["btn_print_pdf"],
                        on_click=lambda: ui.run_javascript(
                            "window.open('/api/analytics/chart.html?query_id=' + encodeURIComponent(window.__gkrp_query_id || 'q2'), '_blank');"
                        ),
                    )

            with ui.column().classes("w-full mt-2"):
                with ui.row().classes("items-center gap-2"):
                    ui.label(LOCALE["chart_fetch_info"]).classes("text-sm text-gray-500")
                    use_all_rows = ui.toggle(
                        {True: LOCALE["toggle_on"], False: LOCALE["toggle_off"]},
                        value=False,
                    ).classes("text-sm")
                    ui.label(LOCALE["enable_all_rows"])

        # Right panel (fragments filters)
        with ui.column().classes("w-[320px] shrink-0"):
            ui.label(LOCALE["panel_fragments"]).classes("text-subtitle1 font-medium text-blue-600")
            with ui.scroll_area().classes(
                "w-full h-[820px] border rounded p-2 bg-white"
            ):
                frag_filters: list[tuple[str, Any]] = [
                    (
                        "Piecetype",
                        ui.select(
                            options=[],
                            label=LOCALE["frag_piecetype"],
                            value=[],
                            multiple=True,
                            clearable=True,
                            with_input=True,
                        )
                        .classes("w-full")
                        .props("dense"),
                    ),
                    (
                        "Technology",
                        ui.select(
                            options=[],
                            multiple=True,
                            clearable=True,
                            with_input=True,
                            label=LOCALE["frag_technology"],
                        )
                        .classes("w-full")
                        .props("dense"),
                    ),
                    (
                        "Baking",
                        ui.select(
                            options=[],
                            multiple=True,
                            clearable=True,
                            with_input=True,
                            label=LOCALE["frag_baking"],
                        )
                        .classes("w-full")
                        .props("dense"),
                    ),
                    (
                        "Color / Primary color",
                        ui.select(
                            options=[],
                            multiple=True,
                            clearable=True,
                            with_input=True,
                            label=LOCALE["frag_color_primary"],
                        )
                        .classes("w-full")
                        .props("dense"),
                    ),
                    (
                        "Covering",
                        ui.select(
                            options=[],
                            multiple=True,
                            clearable=True,
                            with_input=True,
                            label=LOCALE["frag_covering"],
                        )
                        .classes("w-full")
                        .props("dense"),
                    ),
                    (
                        "Surface",
                        ui.select(
                            options=[],
                            multiple=True,
                            clearable=True,
                            with_input=True,
                            label=LOCALE["frag_surface"],
                        )
                        .classes("w-full")
                        .props("dense"),
                    ),
                    (
                        "Wall thickness",
                        ui.select(
                            options=[],
                            multiple=True,
                            clearable=True,
                            with_input=True,
                            label=LOCALE["frag_wall_thickness"],
                        )
                        .classes("w-full")
                        .props("dense"),
                    ),
                    (
                        "Handle type",
                        ui.select(
                            options=[],
                            multiple=True,
                            clearable=True,
                            with_input=True,
                            label=LOCALE["frag_handle_type"],
                        )
                        .classes("w-full")
                        .props("dense"),
                    ),
                    (
                        "Handle size",
                        ui.select(
                            options=[],
                            multiple=True,
                            clearable=True,
                            with_input=True,
                            label=LOCALE["frag_handle_size"],
                        )
                        .classes("w-full")
                        .props("dense"),
                    ),
                    (
                        "Bottom type",
                        ui.select(
                            options=[],
                            multiple=True,
                            clearable=True,
                            with_input=True,
                            label=LOCALE["frag_bottom_type"],
                        )
                        .classes("w-full")
                        .props("dense"),
                    ),
                    (
                        "Category",
                        ui.select(
                            options=[],
                            multiple=True,
                            clearable=True,
                            with_input=True,
                            label=LOCALE["frag_category"],
                        )
                        .classes("w-full")
                        .props("dense"),
                    ),
                    (
                        "Form",
                        ui.select(
                            options=[],
                            multiple=True,
                            clearable=True,
                            with_input=True,
                            label=LOCALE["frag_form"],
                        )
                        .classes("w-full")
                        .props("dense"),
                    ),
                    (
                        "Type",
                        ui.select(
                            options=[],
                            multiple=True,
                            clearable=True,
                            with_input=True,
                            label=LOCALE["frag_type"],
                        )
                        .classes("w-full")
                        .props("dense"),
                    ),
                    (
                        "Subtype",
                        ui.select(
                            options=[],
                            multiple=True,
                            clearable=True,
                            with_input=True,
                            label=LOCALE["frag_subtype"],
                        )
                        .classes("w-full")
                        .props("dense"),
                    ),
                    (
                        "Variant",
                        ui.select(
                            options=[],
                            multiple=True,
                            clearable=True,
                            with_input=True,
                            label=LOCALE["frag_variant"],
                        )
                        .classes("w-full")
                        .props("dense"),
                    ),
                ]

            # ---- Ornaments section (always visible) ----
            orn_section = ui.column().classes("w-full gap-1 mt-4")
            with orn_section:
                ui.label(LOCALE["panel_ornaments"]).classes("text-subtitle1 font-medium text-blue-600")
                orn_filters: list[tuple[str, Any]] = [
                    (
                        "Primary",
                        ui.select(
                            options=[],
                            label=LOCALE["frag_primary"],
                            multiple=True,
                            clearable=True,
                            with_input=True,
                        )
                        .classes("w-full")
                        .props("dense"),
                    ),
                    (
                        "Secondary",
                        ui.select(
                            options=[],
                            label=LOCALE["frag_secondary"],
                            multiple=True,
                            clearable=True,
                            with_input=True,
                        )
                        .classes("w-full")
                        .props("dense"),
                    ),
                    (
                        "Tertiary",
                        ui.select(
                            options=[],
                            label=LOCALE["frag_tertiary"],
                            multiple=True,
                            clearable=True,
                            with_input=True,
                        )
                        .classes("w-full")
                        .props("dense"),
                    ),
                    (
                        "Quarternary",
                        ui.select(
                            options=[],
                            label=LOCALE["frag_quarternary"],
                            multiple=True,
                            clearable=True,
                            with_input=True,
                        )
                        .classes("w-full")
                        .props("dense"),
                    ),
                    (
                        "Color / color1",
                        ui.select(
                            options=[],
                            label=LOCALE["frag_color_color1"],
                            multiple=True,
                            clearable=True,
                            with_input=True,
                        )
                        .classes("w-full")
                        .props("dense"),
                    ),
                    (
                        "Encrust color",
                        ui.select(
                            options=[],
                            label=LOCALE["frag_encrust_color"],
                            multiple=True,
                            clearable=True,
                            with_input=True,
                        )
                        .classes("w-full")
                        .props("dense"),
                    ),
                ]

    # --- local state ---

    def _set_chart(figure: dict[str, Any]) -> None:
        if hasattr(chart, "figure"):
            setattr(chart, "figure", figure)
            try:
                chart.update()
            except TypeError:
                chart.update()
        else:
            try:
                chart.update(figure)  # type: ignore[arg-type]
            except TypeError:
                if hasattr(chart, "props"):
                    chart.props(f":figure='{json.dumps(figure)}'")  # type: ignore[attr-defined]
                    chart.update()
                else:
                    raise RuntimeError(
                        "Cannot update Plotly chart on this NiceGUI version."
                    )

        ui.run_javascript(
            f"""
            setTimeout(() => {{
              const el = document.getElementById({json.dumps(chart_id)});
              if (!el) return;
              const gd = el.querySelector('.js-plotly-plot') || el;
              if (window.Plotly && gd) {{
                Plotly.Plots.resize(gd);
                Plotly.redraw(gd);
              }}
            }}, 50);
            """
        )

    def _build_figure(
        xs: list[str],
        ys: list[int],
        title: str,
        series_data: dict[str, list[int]] | None = None,
        series_label: str = "Series",
    ) -> dict[str, Any]:
        chart_type = (sel_chart_type.value or "Bar").lower()
        chart_type_debug.set_text(f"chart_type={chart_type} series={bool(series_data)}")
        if series_data:
            return plotly_grouped_bar(xs, series_data, title, series_label=series_label)
        if chart_type == "pie":
            return plotly_pie(xs, ys, title)
        if chart_type == "donut":
            return plotly_donut(xs, ys, title)
        return plotly_bar(xs, ys, title)

    def _select_to_list(widget: Any) -> list[str] | None:
        vals = widget.value
        if isinstance(vals, list) and vals:
            return [str(v).strip() for v in vals if str(v).strip()]
        elif isinstance(vals, str) and vals.strip():
            return [vals.strip()]
        return None

    def _read_filters() -> dict[str, Any]:
        query_id = QUERY_OPTIONS.get(sel_query.value, "q2")

        layer_filters_map: dict[str, list[str] | None] = {
            "Site": _select_to_list(sel_site),
            "Sector": _select_to_list(sel_sector),
            "Square": _select_to_list(sel_square),
            "Layer": _select_to_list(sel_layer),
        }

        limit_raw = sel_limit.value
        if limit_raw == "max":
            limit = TABLE_MAX_LIMIT
        else:
            limit = int(limit_raw or DEFAULT_LIMIT)
            limit = max(1, min(limit, TABLE_MAX_LIMIT))

        frag_filters_map: dict[str, list[str] | None] = {}
        for label, widget in frag_filters:
            if isinstance(widget, ui.select):
                vals = widget.value
                if isinstance(vals, list) and vals:
                    frag_filters_map[label] = [
                        str(v).strip() for v in vals if str(v).strip()
                    ]
                elif isinstance(vals, str) and vals.strip():
                    frag_filters_map[label] = [vals.strip()]
                else:
                    frag_filters_map[label] = None
            elif isinstance(widget, ui.input):
                val = (widget.value or "").strip() or None
                frag_filters_map[label] = val

        for label, widget in orn_filters:
            if isinstance(widget, ui.select):
                vals = widget.value
                if isinstance(vals, list) and vals:
                    frag_filters_map[label] = [
                        str(v).strip() for v in vals if str(v).strip()
                    ]
                elif isinstance(vals, str) and vals.strip():
                    frag_filters_map[label] = [vals.strip()]
                else:
                    frag_filters_map[label] = None

        state["query_id"] = query_id
        app.storage.general["analytics_last_query_id"] = query_id
        ui.run_javascript(f"window.__gkrp_query_id = {json.dumps(query_id)};")

        return {
            "query_id": query_id,
            "layer_filters": layer_filters_map,
            "limit": limit,
            "offset": 0,
            "frag_filters": frag_filters_map,
        }

    def _get_type_columns(cols: list[str]) -> list[str]:
        # case-insensitive match; keeps original order
        return [c for c in cols if "type" in c.lower()]

    def _fetch_layer_cache() -> None:
        with session_scope() as db:
            data = get_layer_hierarchy(db, query_id="q2")
            state["_hierarchy"] = data.get("hierarchy", {})
            state["_all_sites"] = data.get("all_sites", [])
            state["_all_sectors"] = data.get("all_sectors", [])
            state["_all_squares"] = data.get("all_squares", [])
            state["_all_layers"] = data.get("all_layers", [])

    def _populate_layer_options_hierarchical() -> None:
        """Populate dropdowns using the cached hierarchy dict."""
        hierarchy = state.get("_hierarchy", {})
        all_sites = state.get("_all_sites", [])
        all_sectors = state.get("_all_sectors", [])
        all_squares = state.get("_all_squares", [])
        all_layers = state.get("_all_layers", [])

        sel_site.options = all_sites
        sel_site.update()

        # Sector: only those under selected sites
        selected_sites = sel_site.value
        if isinstance(selected_sites, list):
            selected_sites = [s for s in selected_sites if s]
        elif selected_sites:
            selected_sites = [selected_sites]
        else:
            selected_sites = []

        if len(selected_sites) == 1:
            site_h = hierarchy.get(selected_sites[0], {})
            sector_vals = sorted(site_h.keys())
        else:
            sector_vals = all_sectors
        sel_sector.options = sector_vals
        sel_sector.update()

        # Square: only those under selected site+sector
        selected_sectors = sel_sector.value
        if isinstance(selected_sectors, list):
            selected_sectors = [s for s in selected_sectors if s]
        elif selected_sectors:
            selected_sectors = [selected_sectors]
        else:
            selected_sectors = []

        if len(selected_sites) == 1 and len(selected_sectors) == 1:
            sq_h = hierarchy.get(selected_sites[0], {}).get(selected_sectors[0], {})
            square_vals = sorted(sq_h.keys())
        elif len(selected_sites) == 1:
            square_vals = []
            for sector in all_sectors:
                sq_h = hierarchy.get(selected_sites[0], {}).get(sector, {})
                square_vals.extend(sq_h.keys())
            square_vals = sorted(set(square_vals))
        else:
            square_vals = all_squares
        sel_square.options = square_vals
        sel_square.update()

        # Layer: only those under selected site+sector+square
        selected_squares = sel_square.value
        if isinstance(selected_squares, list):
            selected_squares = [s for s in selected_squares if s]
        elif selected_squares:
            selected_squares = [selected_squares]
        else:
            selected_squares = []

        if (
            len(selected_sites) == 1
            and len(selected_sectors) == 1
            and len(selected_squares) == 1
        ):
            sq_h = hierarchy.get(selected_sites[0], {}).get(selected_sectors[0], {})
            layer_vals = sorted(sq_h.get(selected_squares[0], []))
        elif len(selected_sites) == 1 and len(selected_sectors) == 1:
            layer_vals = set()
            for sq in all_squares:
                sq_h = hierarchy.get(selected_sites[0], {}).get(selected_sectors[0], {})
                layer_vals.update(sq_h.get(sq, []))
            layer_vals = sorted(layer_vals)
        elif len(selected_sites) == 1:
            layer_vals = set()
            for sector in all_sectors:
                sq_h = hierarchy.get(selected_sites[0], {}).get(sector, {})
                for sq in all_squares:
                    layer_vals.update(sq_h.get(sq, []))
            layer_vals = sorted(layer_vals)
        else:
            layer_vals = all_layers
        sel_layer.options = layer_vals
        sel_layer.update()

    def _populate_frag_filter_options(items: list[dict[str, Any]]) -> None:
        # Determine which columns are needed by looking at active widgets
        needed: set[str] = set()
        for label in ["Site", "Sector", "Square", "Layer"]:
            needed.add(label)
        for label, widget in frag_filters:
            if isinstance(widget, ui.select):
                needed.add(label)
        for label, widget in orn_filters:
            if isinstance(widget, ui.select):
                needed.add(label)

        if not needed:
            return

        f = _read_filters()
        with session_scope() as db:
            distinct = get_distinct_values(
                db,
                query_id=f["query_id"],
                layer_filters=f.get("layer_filters"),
                frag_filters=f.get("frag_filters"),
                columns=needed,
            )

        for label, widget in frag_filters:
            if not isinstance(widget, ui.select):
                continue
            widget.options = distinct.get(label, [])
            widget.update()

        for label, widget in orn_filters:
            if not isinstance(widget, ui.select):
                continue
            widget.options = distinct.get(label, [])
            widget.update()

    def refresh() -> None:
        _fetch_layer_cache()
        _populate_layer_options_hierarchical()

        if state.get("_refreshing"):
            return
        state["_refreshing"] = True
        try:
            f = _read_filters()
            notes: list[str] = []

            if f["limit"] >= TABLE_MAX_LIMIT:
                chart_fetch = f["limit"]
            elif use_all_rows.value:
                chart_fetch = TABLE_MAX_LIMIT
            else:
                chart_fetch = min(max(f["limit"], 0), CHART_MAX_FETCH)

            res = result_for(
                f["query_id"],
                layer_filters=f.get("layer_filters"),
                limit=chart_fetch,
                offset=f["offset"],
                frag_filters=f.get("frag_filters"),
            )

            total = int(res.total or 0)
            if total == 0:
                _set_chart(_build_figure([], [], LOCALE["status_no_results_query"].format(query_id=f['query_id'])))
                dbg.set_text(f"query={f['query_id']} rows=0 total=0")
                status.set_text(LOCALE["status_no_results"])
                return

            if not res.items:
                _set_chart(_build_figure([], [], LOCALE["status_no_results_query"].format(query_id=f['query_id'])))
                dbg.set_text(f"query={f['query_id']} rows=0 total={res.total}")
                status.set_text(LOCALE["status_no_results"])
                return

            ui_cols = ui_columns(res.columns) or list(res.columns)

            _GROUPBY_EXCLUDE = frozenset(
                {
                    "l_layername",
                    "l_context",
                    "f_fragmenttype",
                    "f_fract",
                    "f_secondarycolor",
                    "f_includesconc",
                    "f_includessize",
                    "f_onepot",
                    "f_includestype",
                    "f_han",
                    "f_note",
                    "f_inventory",
                    "f_imageurl",
                    "p_ornamentid",
                    "o_fragmentid",
                    "o_relationship",
                    "o_ornament",
                    "o_color1",
                    "o_color2",
                    "encrustcolor",
                    "o_encrustcolor1",
                    "o_encrustcolor2",
                    "o_recordenteredon",
                }
            )
            groupby_cols = [c for c in ui_cols if c.lower() not in _GROUPBY_EXCLUDE]
            sel_x.options = groupby_cols
            sel_x.update()
            sel_series.options = groupby_cols
            sel_series.update()

            preferred = [
                "l_site",
                "l_sector",
                "l_square",
                "f_piecetype",
                "f_category",
                "f_form",
                "f_technology",
            ]

            if not sel_x.value or sel_x.value not in groupby_cols:
                default_x = next((c for c in preferred if c in groupby_cols), None) or (
                    groupby_cols[0] if groupby_cols else None
                )
                state["_suppress_x_change"] = True
                sel_x.set_value(default_x)
                state["_suppress_x_change"] = False
                if default_x:
                    notes.append(f"group-by defaulted to {default_x}")

            x_key = sel_x.value
            series_key = sel_series.value
            if series_key and series_key in groupby_cols:
                series_label = _column_to_label(series_key)
                xs, series_data = build_histogram_series(
                    res.items, x_key, series_key, top_n=30
                )
                _set_chart(
                    _build_figure(
                        xs,
                        [],
                        f"Count by {x_key} grouped by {series_key} ({f['query_id']})",
                        series_data=series_data,
                        series_label=series_label,
                    )
                )
            else:
                xs, ys = build_histogram(res.items, x_key, top_n=30)
                _set_chart(_build_figure(xs, ys, f"Count by {x_key} ({f['query_id']})"))

            _populate_frag_filter_options(res.items)

            dbg.set_text(
                f"query={f['query_id']} rows={len(res.items)} total={res.total} "
                f"x={x_key} series={series_key or 'none'} buckets={len(xs)}"
            )

            base = LOCALE["status_returned"].format(count=len(res.items), total=res.total)
            if notes:
                base += "  " + " \u2022 ".join(notes)
            status.set_text(base)

        finally:
            state["_refreshing"] = False

    def _on_layer_change() -> None:
        _populate_layer_options_hierarchical()

    btn_run.on("click", lambda e: refresh())

    def _on_query_change(e) -> None:
        refresh()

    sel_query.on("change", _on_query_change)
    sel_site.on("change", lambda e: _on_layer_change())
    sel_sector.on("change", lambda e: _on_layer_change())
    sel_square.on("change", lambda e: _on_layer_change())
    sel_layer.on("change", lambda e: _on_layer_change())
    sel_limit.on("change", lambda e: refresh())

    def _on_x_change(e) -> None:
        if state.get("_suppress_x_change"):
            return
        refresh()

    sel_x.on("change", _on_x_change)
    sel_chart_type.on("change", lambda e: refresh())
    use_all_rows.on("change", lambda e: refresh())

    refresh()

    # --- Help dialog (outside the 3-column row) ---
    with ui.dialog() as help_dialog, ui.card().classes("w-[750px] max-h-[80vh]"):
        ui.markdown(_load_chart_guide())
        ui.button(LOCALE["chart_help_close"], on_click=help_dialog.close).classes("w-full mt-2")


# -------------------------
# Export endpoints (kept here so they register once)
# -------------------------


@app.get("/api/analytics/data.csv")
def analytics_data_csv(
    query_id: str = "q2",
    site: str | None = None,
    sector: str | None = None,
    square: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    q: str | None = None,
    limit: int = DEFAULT_LIMIT,
) -> Response:
    df = parse_date(date_from)
    dt = parse_date(date_to)

    res = result_for(
        query_id,
        site=site or None,
        sector=sector or None,
        square=square or None,
        date_from=df,
        date_to=dt,
        q=q or None,
        limit=min(max(int(limit), 1), TABLE_MAX_LIMIT),
        offset=0,
    )

    logger.info(
        "DEBUG first_row_keys: {}",
        sorted(res.items[0].keys()) if res.items else "NO_ROWS",
    )
    logger.info("DEBUG first_row_sample: {}", res.items[0] if res.items else "NO_ROWS")

    buf = io.StringIO()
    cols = ui_columns(res.columns)
    writer = csv.DictWriter(buf, fieldnames=cols)
    writer.writeheader()
    for row in res.items:
        writer.writerow({k: row.get(k) for k in cols})

    return Response(
        content=buf.getvalue(),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="analytics_{query_id}.csv"'
        },
    )


@app.get("/api/analytics/chart.json")
def analytics_chart_json(
    query_id: str = "q2",
    x: str | None = None,
    chart_type: str = "bar",
    series: str | None = None,
    site: str | None = None,
    sector: str | None = None,
    square: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    q: str | None = None,
) -> Response:
    df = parse_date(date_from)
    dt = parse_date(date_to)

    meta = result_for(
        query_id,
        site=site or None,
        sector=sector or None,
        square=square or None,
        date_from=df,
        date_to=dt,
        q=q or None,
        limit=1,
        offset=0,
    )

    total = int(meta.total or 0)
    chart_fetch = min(max(total, 0), CHART_MAX_FETCH)

    res = result_for(
        query_id,
        site=site or None,
        sector=sector or None,
        square=square or None,
        date_from=df,
        date_to=dt,
        q=q or None,
        limit=chart_fetch,
        offset=0,
    )

    cols = ui_columns(res.columns) or list(res.columns)
    if x and (x not in cols):
        x = None
    if not x:
        x = "f_piecetype" if "f_piecetype" in cols else (cols[0] if cols else "")

    if series and series in cols:
        series_label = _column_to_label(series)
        xs, series_data = build_histogram_series(res.items, x, series)
        fig = plotly_grouped_bar(
            xs,
            series_data,
            title=f"Count by {x} grouped by {series} ({query_id})",
            series_label=series_label,
        )
    else:
        xs, ys = build_histogram(res.items, x)
        if chart_type == "pie":
            fig = plotly_pie(xs, ys, title=f"Count by {x} ({query_id})")
        elif chart_type == "donut":
            fig = plotly_donut(xs, ys, title=f"Count by {x} ({query_id})")
        else:
            fig = plotly_bar(xs, ys, title=f"Count by {x} ({query_id})")
    return Response(content=json.dumps(fig), media_type="application/json")


@app.get("/api/analytics/chart.html")
def analytics_chart_html(query_id: str = "q2") -> Response:
    qid = query_id or (app.storage.general.get("analytics_last_query_id") or "q2")
    fig_json = analytics_chart_json(query_id=qid).body.decode("utf-8")

    html = f"""
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>Analytics Chart</title>
  <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
  <style>
    body {{ margin: 0; font-family: sans-serif; }}
    #chart {{ width: 100vw; height: 92vh; }}
    .hint {{ padding: 10px; }}
  </style>
</head>
<body>
  <div class="hint">Use browser Print \u2192 Save as PDF.</div>
  <div id="chart"></div>
  <script>
    const fig = {fig_json};
    const cfg = fig.config || {{responsive: true, displaylogo: false}};
    Plotly.newPlot('chart', fig.data || [], fig.layout || {{}}, cfg);
  </script>
</body>
</html>
"""
    return HTMLResponse(html)


@app.get("/api/analytics/health")
def analytics_health() -> Response:
    return PlainTextResponse("ok")
