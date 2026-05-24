"""NiceGUI page: Analytics Chart — Fragments.

Layout:
- Left: layer filters (Site, Sector, Square, Layer) + limit selector
- Center: chart (Plotly) with X-axis, series, chart type selectors
- Right: Fragments + Ornaments filter panels

This page is a dedicated view for the q2 query
(Layers + Fragments + Ornaments).
"""

from __future__ import annotations

import json
import pathlib
from typing import Any

import markdown
from nicegui import ui

from .analytics_common import (
    CHART_FRAGMENTS_ROUTE,
    DEFAULT_LIMIT,
    TABLE_MAX_LIMIT,
    build_histogram,
    build_histogram_series,
    plotly_bar,
    plotly_donut,
    plotly_grouped_bar,
    plotly_pie,
    _column_to_label,
)
from gkrp_data_portal.ui.lang import t
from gkrp_data_portal.db.session import session_scope
from gkrp_data_portal.ui.repository.analytics_repo import (
    build_chart_histogram,
    get_distinct_values,
    get_groupby_columns,
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


@ui.page(CHART_FRAGMENTS_ROUTE)
def page_analytics_chart_fragments() -> None:
    ui.label(t("title_analytics_chart_fragments")).classes("text-h5 text-blue-600")

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
        # Left panel — layer filters
        with ui.column().classes("w-[340px] shrink-0"):
            ui.label(t("panel_query_filters")).classes(
                "text-subtitle1 font-medium text-blue-600"
            )

            with ui.row().classes("w-full gap-2 items-center"):
                btn_run = ui.button(t("btn_run_query"), icon="play_arrow").classes(
                    "flex-1"
                )

            with ui.scroll_area().classes(
                "w-full h-[320px] border rounded p-2 bg-white"
            ):
                sel_site = (
                    ui.select(
                        options=[],
                        label=t("label_site"),
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
                        label=t("label_sector"),
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
                        label=t("label_square"),
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
                        label=t("label_layer"),
                    )
                    .classes("w-full")
                    .props("dense")
                )

            sel_limit = ui.select(
                options=[100, 200, 500, 1000, 2500, 5000, "max"],
                value=DEFAULT_LIMIT,
                label=t("label_limit"),
            ).classes("w-full")
            ui.label(t("limit_max_info")).classes("text-xs text-gray-400 mt-1")

        # Center panel — chart
        with ui.column().classes("flex-1 min-w-0"):
            with ui.row().classes("w-full items-center justify-between"):
                ui.label(t("panel_chart")).classes(
                    "text-subtitle1 font-medium text-blue-600"
                )
                with ui.column().classes("items-center gap-0"):
                    ui.label(t("chart_help_label")).classes(
                        "text-subtitle2 text-blue-600"
                    )
                    help_btn = (
                        ui.button(icon="help")
                        .classes("p-1")
                        .style("font-size: 1.2rem;")
                    )
                    help_btn.on("click", lambda: help_dialog.open())
            status = ui.label("").classes("text-sm text-gray-600")
            dbg = ui.label("").classes("text-xs text-gray-500")
            chart_type_debug = ui.label("").classes("text-xs text-blue-600")

            chart = (
                ui.plotly({"data": [], "layout": {"height": 800}})
                .classes("w-full border rounded bg-white")
                .style("height: 800px;")
            )
            chart_id = chart.id

            with ui.row().classes("w-full items-center justify-between gap-2"):
                with ui.column().classes("gap-0"):
                    sel_x = ui.select(
                        options=[], label=t("label_group_by")
                    ).classes("w-[300px]")
                    ui.label(
                        t("chart_help_groupby")
                    ).classes("text-xs text-gray-400")
                with ui.column().classes("gap-0"):
                    sel_series = ui.select(
                        options=[],
                        label=t("label_series"),
                        clearable=True,
                    ).classes("w-[200px]")
                    ui.label(
                        t("chart_help_series")
                    ).classes("text-xs text-gray-400")
                with ui.column().classes("gap-0"):
                    sel_chart_type = ui.select(
                        options=["Bar", "Pie", "Donut"],
                        value="Pie",
                        label=t("label_chart_type"),
                    ).classes("w-[160px]")
                    ui.label(
                        t("chart_help_chart_type")
                    ).classes("text-xs text-gray-400")

                with ui.row().classes("gap-2"):
                    ui.button(
                        t("btn_download_png"),
                        on_click=lambda: ui.run_javascript(
                            f"""
                            (function() {{
                              const el = document.getElementById('{chart_id}');
                              if (!el) return;
                              const gd = el.querySelector('.js-plotly-plot') || el;
                              if (window.Plotly && gd) {{
                                Plotly.downloadImage(gd, {{format:'png', filename:'analytics_chart_fragments', height:650, width:1100}});
                              }}
                            }})();
                            """
                        ),
                    )
                    ui.button(
                        t("btn_download_jpg"),
                        on_click=lambda: ui.run_javascript(
                            f"""
                            (function() {{
                              const el = document.getElementById('{chart_id}');
                              if (!el) return;
                              const gd = el.querySelector('.js-plotly-plot') || el;
                              if (window.Plotly && gd) {{
                                Plotly.downloadImage(gd, {{format:'jpeg', filename:'analytics_chart_fragments', height:650, width:1100}});
                              }}
                            }})();
                            """
                        ),
                    )
                    ui.button(
                        t("btn_print_pdf"),
                        on_click=lambda: ui.run_javascript(
                            "window.open('/api/analytics/chart.html?query_id=' + encodeURIComponent(window.__gkrp_query_id || 'q2'), '_blank');"
                        ),
                    )

            with ui.column().classes("w-full mt-2"):
                with ui.row().classes("items-center gap-2"):
                    ui.label(t("chart_fetch_info")).classes(
                        "text-sm text-gray-500"
                    )
                    use_all_rows = ui.toggle(
                        {True: t("toggle_on"), False: t("toggle_off")},
                        value=False,
                    ).classes("text-sm")
                    ui.label(t("enable_all_rows"))

        # Right panel — fragments filters
        with ui.column().classes("w-[320px] shrink-0"):
            ui.label(t("panel_fragments")).classes(
                "text-subtitle1 font-medium text-blue-600"
            )
            with ui.scroll_area().classes(
                "w-full h-[820px] border rounded p-2 bg-white"
            ):
                frag_filters: list[tuple[str, Any]] = [
                    (
                        "Piecetype",
                        ui.select(
                            options=[],
                            label="Piecetype",
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
                            label="Technology",
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
                            label="Baking",
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
                            label="Color / Primary color",
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
                            label="Covering",
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
                            label="Surface",
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
                            label="Wall thickness",
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
                            label="Handle type",
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
                            label="Handle size",
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
                            label="Bottom type",
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
                            label="Category",
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
                            label="Form",
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
                            label="Type",
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
                            label="Subtype",
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
                            label="Variant",
                        )
                        .classes("w-full")
                        .props("dense"),
                    ),
                ]

            # Ornaments section
            orn_section = ui.column().classes("w-full gap-1 mt-4")
            with orn_section:
                ui.label(t("panel_ornaments")).classes(
                    "text-subtitle1 font-medium text-blue-600"
                )
                orn_filters: list[tuple[str, Any]] = [
                    (
                        "Primary",
                        ui.select(
                            options=[],
                            label="Primary",
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
                            label="Secondary",
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
                            label="Tertiary",
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
                            label="Quarternary",
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
                            label="Color / color1",
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
                            label="Encrust color",
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

        state["query_id"] = "q2"
        ui.run_javascript(f"window.__gkrp_query_id = {json.dumps('q2')};")

        return {
            "query_id": "q2",
            "layer_filters": layer_filters_map,
            "limit": limit,
            "offset": 0,
            "frag_filters": frag_filters_map,
        }

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

    def refresh() -> None:
        _fetch_layer_cache()
        _populate_layer_options_hierarchical()

        if state.get("_refreshing"):
            return
        state["_refreshing"] = True
        try:
            f = _read_filters()

            # --- Build group-by column options from known definitions ---
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
            all_cols = get_groupby_columns("q2")
            groupby_cols = [c for c in all_cols if c.lower() not in _GROUPBY_EXCLUDE]
            sel_x.options = groupby_cols
            sel_x.update()
            sel_series.options = groupby_cols
            sel_series.update()

            # Default X if not set or invalid
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

            # --- Chart: SQL-side aggregation (no raw row fetch needed) ---
            x_key = sel_x.value or "l_site"
            series_key = sel_series.value

            with session_scope() as db:
                chart_agg = build_chart_histogram(
                    db,
                    query_id="q2",
                    x_key=x_key,
                    series_key=series_key,
                    layer_filters=f.get("layer_filters"),
                    frag_filters=f.get("frag_filters"),
                    top_n=30,
                )

            if not chart_agg:
                _set_chart(
                    _build_figure(
                        [], [], t("status_no_results_query").format(query_id="q2")
                    )
                )
                dbg.set_text("query=q2 rows=0 total=0")
                status.set_text(t("status_no_results"))
                return

            if series_key and series_key in (sel_x.options or []):
                series_label = _column_to_label(series_key)
                xs, series_data = build_histogram_series(
                    [], x_key, series_key, top_n=30,
                    pre_aggregated=chart_agg,
                )
                _set_chart(
                    _build_figure(
                        xs,
                        [],
                        f"Count by {x_key} grouped by {series_key} (q2)",
                        series_data=series_data,
                        series_label=series_label,
                    )
                )
            else:
                xs, ys = build_histogram(
                    [], x_key, top_n=30, pre_aggregated=chart_agg
                )
                _set_chart(_build_figure(xs, ys, f"Count by {x_key} (q2)"))

            dbg.set_text(
                f"query=q2 chart_buckets={len(xs)} "
                f"x={x_key} series={series_key or 'none'}"
            )

            # --- Filter dropdowns: still need distinct-value queries ---
            _populate_frag_filter_options_for_dropdowns()

        finally:
            state["_refreshing"] = False

    def _populate_frag_filter_options_for_dropdowns() -> None:
        """Populate filter dropdown options using SQL DISTINCT queries.

        Separate from chart rendering so dropdowns can refresh independently.
        """
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

    def _on_layer_change() -> None:
        _populate_layer_options_hierarchical()

    btn_run.on("click", lambda e: refresh())

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
    with ui.dialog() as help_dialog, ui.card().classes("w-[1200px] max-h-[80vh]"):
        ui.markdown(_load_chart_guide()).classes("max-w-full").style("max-width: none")
        ui.button(t("chart_help_close"), on_click=help_dialog.close).classes(
            "w-full mt-2"
        )
