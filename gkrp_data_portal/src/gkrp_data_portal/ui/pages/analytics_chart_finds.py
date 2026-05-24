"""NiceGUI page: Analytics Chart — Finds.

Layout:
- Left: Finds filters (Find Type, Material, Coin, etc.) + limit selector
- Center: chart (Plotly) with X-axis, series, chart type selectors

This page uses the finds_arch query (finds table + optional layer join).
Visualizations count table rows (not f_count), so each row = 1.
"""

from __future__ import annotations

import json
import pathlib
from typing import Any

import markdown
from nicegui import ui

from .analytics_common import (
    CHART_FINDS_ROUTE,
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
)

_PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[5]
_CHART_GUIDE_PATH = _PROJECT_ROOT / "CHART.md"


def _load_chart_guide() -> str:
    """Load and render CHART.md as HTML."""
    if _CHART_GUIDE_PATH.exists():
        md = _CHART_GUIDE_PATH.read_text(encoding="utf-8")
        return markdown.markdown(md, extensions=["tables", "fenced_code"])
    return "<p>Chart guide not found.</p>"


@ui.page(CHART_FINDS_ROUTE)
def page_analytics_chart_finds() -> None:
    ui.label(t("title_analytics_chart_finds")).classes("text-h5 text-blue-600")

    state: dict[str, Any] = {
        "query_id": "finds_arch",
        "_refreshing": False,
        "_suppress_x_change": False,
        "_hierarchy": {},
        "_all_sites": [],
        "_all_sectors": [],
        "_all_squares": [],
        "_all_layers": [],
    }

    with ui.row().classes("w-full gap-4 items-start flex-nowrap"):
        # Left panel — finds filters
        with ui.column().classes("w-[340px] shrink-0"):
            ui.label(t("panel_query_filters")).classes(
                "text-subtitle1 font-medium text-blue-600"
            )

            with ui.row().classes("w-full gap-2 items-center"):
                btn_run = ui.button(t("btn_run_query"), icon="play_arrow").classes(
                    "flex-1"
                )

            with ui.scroll_area().classes(
                "w-full h-[600px] border rounded p-2 bg-white"
            ):
                finds_filters: list[tuple[str, Any]] = [
                    (
                        "Find Type",
                        ui.select(
                            options=[],
                            label="Find Type",
                            multiple=True,
                            clearable=True,
                            with_input=True,
                        )
                        .classes("w-full")
                        .props("dense"),
                    ),
                    (
                        "Material",
                        ui.select(
                            options=[],
                            label="Material",
                            multiple=True,
                            clearable=True,
                            with_input=True,
                        )
                        .classes("w-full")
                        .props("dense"),
                    ),
                    (
                        "Coin",
                        ui.select(
                            options=[],
                            label="Coin",
                            multiple=True,
                            clearable=True,
                            with_input=True,
                        )
                        .classes("w-full")
                        .props("dense"),
                    ),
                    (
                        "Denomination",
                        ui.select(
                            options=[],
                            label="Denomination",
                            multiple=True,
                            clearable=True,
                            with_input=True,
                        )
                        .classes("w-full")
                        .props("dense"),
                    ),
                    (
                        "Mint",
                        ui.select(
                            options=[],
                            label="Mint",
                            multiple=True,
                            clearable=True,
                            with_input=True,
                        )
                        .classes("w-full")
                        .props("dense"),
                    ),
                    (
                        "Year",
                        ui.select(
                            options=[],
                            label="Year",
                            multiple=True,
                            clearable=True,
                            with_input=True,
                        )
                        .classes("w-full")
                        .props("dense"),
                    ),
                    (
                        "Depth",
                        ui.select(
                            options=[],
                            label="Depth",
                            multiple=True,
                            clearable=True,
                            with_input=True,
                        )
                        .classes("w-full")
                        .props("dense"),
                    ),
                    (
                        "Context",
                        ui.select(
                            options=[],
                            label="Context",
                            multiple=True,
                            clearable=True,
                            with_input=True,
                        )
                        .classes("w-full")
                        .props("dense"),
                    ),
                ]

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
                        t("chart_help_groupby_finds")
                    ).classes("text-xs text-gray-400")
                with ui.column().classes("gap-0"):
                    sel_series = ui.select(
                        options=[],
                        label=t("label_series"),
                        clearable=True,
                    ).classes("w-[200px]")
                    ui.label(
                        t("chart_help_series_finds")
                    ).classes("text-xs text-gray-400")
                with ui.column().classes("gap-0"):
                    sel_chart_type = ui.select(
                        options=["Bar", "Pie", "Donut"],
                        value="Pie",
                        label=t("label_chart_type"),
                    ).classes("w-[160px]")
                    ui.label(t("chart_help_chart_type_finds")).classes("text-xs text-gray-400")

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
                                Plotly.downloadImage(gd, {{format:'png', filename:'analytics_chart_finds', height:650, width:1100}});
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
                                Plotly.downloadImage(gd, {{format:'jpeg', filename:'analytics_chart_finds', height:650, width:1100}});
                              }}
                            }})();
                            """
                        ),
                    )
                    ui.button(
                        t("btn_print_pdf"),
                        on_click=lambda: ui.run_javascript(
                            "window.open('/api/analytics/chart.html?query_id=' + encodeURIComponent(window.__gkrp_query_id || 'finds_arch'), '_blank');"
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
        limit_raw = sel_limit.value
        if limit_raw == "max":
            limit = TABLE_MAX_LIMIT
        else:
            limit = int(limit_raw or DEFAULT_LIMIT)
            limit = max(1, min(limit, TABLE_MAX_LIMIT))

        frag_filters_map: dict[str, list[str] | None] = {}
        for label, widget in finds_filters:
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

        state["query_id"] = "finds_arch"
        ui.run_javascript(f"window.__gkrp_query_id = {json.dumps('finds_arch')};")

        return {
            "query_id": "finds_arch",
            "layer_filters": {
                "Site": None,
                "Sector": None,
                "Square": None,
                "Layer": None,
            },
            "limit": limit,
            "offset": 0,
            "frag_filters": frag_filters_map,
        }

    def _populate_frag_filter_options_for_dropdowns() -> None:
        needed: set[str] = set()
        for label, widget in finds_filters:
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

        for label, widget in finds_filters:
            if not isinstance(widget, ui.select):
                continue
            widget.options = distinct.get(label, [])
            widget.update()

    def refresh() -> None:
        if state.get("_refreshing"):
            return
        state["_refreshing"] = True
        try:
            f = _read_filters()

            # Determine group-by columns from available data
            # For finds_arch, use the column definitions to build the options
            groupby_cols = [
                "fi_find_type", "fi_material", "fi_coin", "fi_denomination",
                "fi_mint", "fi_year", "fi_depth_m", "fi_context",
                "l_site", "l_sector", "l_square", "l_layer",
            ]

            sel_x.options = groupby_cols
            sel_x.update()
            sel_series.options = groupby_cols
            sel_series.update()

            if not sel_x.value or sel_x.value not in groupby_cols:
                default_x = next((c for c in ["fi_find_type", "fi_material", "fi_coin", "fi_denomination", "fi_mint", "fi_year", "fi_depth_m", "fi_context", "l_site", "l_sector", "l_square", "l_layer"] if c in groupby_cols), None) or (groupby_cols[0] if groupby_cols else None)
                state["_suppress_x_change"] = True
                sel_x.set_value(default_x)
                state["_suppress_x_change"] = False

            x_key = sel_x.value
            series_key = sel_series.value

            # --- Chart: SQL-side aggregation ---
            with session_scope() as db:
                chart_agg = build_chart_histogram(
                    db,
                    query_id="finds_arch",
                    x_key=x_key,
                    series_key=series_key,
                    layer_filters=f.get("layer_filters"),
                    frag_filters=f.get("frag_filters"),
                    top_n=30,
                )

            if not chart_agg:
                _set_chart(
                    _build_figure(
                        [],
                        [],
                        t("status_no_results_query").format(query_id="finds_arch"),
                    )
                )
                dbg.set_text("query=finds_arch rows=0 total=0")
                status.set_text(t("status_no_results"))
                return

            if series_key and series_key in groupby_cols:
                series_label = _column_to_label(series_key)
                xs, series_data = build_histogram_series(
                    [], x_key, series_key, top_n=30,
                    pre_aggregated=chart_agg,
                )
                _set_chart(
                    _build_figure(
                        xs,
                        [],
                        f"Count by {x_key} grouped by {series_key} (finds_arch)",
                        series_data=series_data,
                        series_label=series_label,
                    )
                )
            else:
                xs, ys = build_histogram(
                    [], x_key, top_n=30, pre_aggregated=chart_agg
                )
                _set_chart(_build_figure(xs, ys, f"Count by {x_key} (finds_arch)"))

            dbg.set_text(
                f"query=finds_arch chart_buckets={len(xs)} "
                f"x={x_key} series={series_key or 'none'}"
            )

            # --- Filter dropdowns: SQL DISTINCT queries ---
            _populate_frag_filter_options_for_dropdowns()

        finally:
            state["_refreshing"] = False

    btn_run.on("click", lambda e: refresh())

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
