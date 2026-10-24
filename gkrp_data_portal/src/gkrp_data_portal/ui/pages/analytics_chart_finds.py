"""NiceGUI page: Analytics Chart — Finds.

Layout:
- Left: Finds filters (Find Type, Material, Coin, etc.)
- Center: chart (Plotly) with X-axis, series, chart type selectors

This page uses the finds_arch query (finds table + optional layer join).
Visualizations count table rows (not f_count), so each row = 1.
"""

from __future__ import annotations

import json
from typing import Any

from nicegui import ui

from .analytics_common import (
    CHART_GUIDE_PATH,
    CHART_FINDS_ROUTE,
    build_histogram,
    build_histogram_series,
    plotly_bar,
    plotly_donut,
    plotly_grouped_bar,
    plotly_pie,
    _column_to_label,
    register_plotly_export_js,
)
from gkrp_data_portal.ui.lang import t
from gkrp_data_portal.db.session import session_scope
from gkrp_data_portal.ui.repository.analytics_repo import (
    ARCH_FILTER_COLS,
    build_chart_histogram,
    get_distinct_values,
    get_groupby_columns,
)

# Archaeology filter labels deliberately not offered as widgets on this page.
ARCH_LABELS_NOT_SHOWN: frozenset[str] = frozenset({"Inv No"})

# Group-by options hidden from the dropdowns (members of get_groupby_columns("finds_arch")).
_GROUPBY_EXCLUDE = frozenset({"fi_inv_no"})
GROUPBY_OPTIONS: list[str] = [
    c for c in get_groupby_columns("finds_arch") if c not in _GROUPBY_EXCLUDE
]
DEFAULT_X = "fi_find_type"


@ui.page(CHART_FINDS_ROUTE)
def page_analytics_chart_finds() -> None:
    ui.label(t("title_analytics_chart_finds")).classes("text-h5 text-blue-600")

    state: dict[str, Any] = {
        "_refreshing": False,
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
                        label,
                        ui.select(
                            options=[],
                            label=label,
                            multiple=True,
                            clearable=True,
                            with_input=True,
                        )
                        .classes("w-full")
                        .props("dense"),
                    )
                    for label in ARCH_FILTER_COLS
                    if label not in ARCH_LABELS_NOT_SHOWN
                ]

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
            register_plotly_export_js()

            with ui.row().classes("w-full items-center justify-between gap-2"):
                with ui.column().classes("gap-0"):
                    sel_x = ui.select(
                        options=GROUPBY_OPTIONS,
                        value=DEFAULT_X,
                        label=t("label_group_by"),
                    ).classes("w-[300px]")
                    ui.label(t("chart_help_groupby_finds")).classes(
                        "text-xs text-gray-400"
                    )
                with ui.column().classes("gap-0"):
                    sel_series = ui.select(
                        options=GROUPBY_OPTIONS,
                        label=t("label_series"),
                        clearable=True,
                    ).classes("w-[200px]")
                    ui.label(t("chart_help_series_finds")).classes(
                        "text-xs text-gray-400"
                    )
                with ui.column().classes("gap-0"):
                    sel_chart_type = ui.select(
                        options=["Bar", "Pie", "Donut"],
                        value="Pie",
                        label=t("label_chart_type"),
                    ).classes("w-[160px]")
                    ui.label(t("chart_help_chart_type_finds")).classes(
                        "text-xs text-gray-400"
                    )

                with ui.row().classes("gap-2"):
                    ui.button(
                        t("btn_download_png"),
                        on_click=lambda: ui.run_javascript(
                            f"window.__gkrpPlotlyDownload && window.__gkrpPlotlyDownload({chart_id}, 'png', 'analytics_chart_finds');"
                        ),
                    )
                    ui.button(
                        t("btn_download_jpg"),
                        on_click=lambda: ui.run_javascript(
                            f"window.__gkrpPlotlyDownload && window.__gkrpPlotlyDownload({chart_id}, 'jpeg', 'analytics_chart_finds');"
                        ),
                    )
                    ui.button(
                        t("btn_print_pdf"),
                        on_click=lambda: ui.run_javascript(
                            f"window.__gkrpPlotlyPrint({chart_id});"
                        ),
                    )

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
            f"setTimeout(() => window.__gkrpPlotlyResize({chart_id}), 50);"
        )

    def _build_figure(
        xs: list[str],
        ys: list[int],
        title: str,
        series: tuple[dict[str, list[int]], str] | None = None,
    ) -> dict[str, Any]:
        chart_type = (sel_chart_type.value or "Bar").lower()
        chart_type_debug.set_text(
            f"chart_type={chart_type} series={series is not None}"
        )
        if series is not None:
            return plotly_grouped_bar(xs, series[0], title, series_label=series[1])
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
        frag_filters_map: dict[str, list[str] | None] = {
            label: _select_to_list(widget) for label, widget in finds_filters
        }

        return {
            "query_id": "finds_arch",
            # location comes from finds columns (fi_sector/fi_square/fi_layer_mechanical),
            # no layers-table filters on this page
            "layer_filters": None,
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

            x_key: str = sel_x.value
            series_key: str | None = sel_series.value

            # --- Chart: SQL-side aggregation ---
            with session_scope() as db:
                chart_agg = build_chart_histogram(
                    db,
                    query_id="finds_arch",
                    x_key=x_key,
                    series_key=series_key,
                    layer_filters=f.get("layer_filters"),
                    frag_filters=f.get("frag_filters"),
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

            if series_key is not None:
                xs, series_data = build_histogram_series(chart_agg)
                _set_chart(
                    _build_figure(
                        xs,
                        [],
                        f"Count by {x_key} grouped by {series_key} (finds_arch)",
                        series=(series_data, _column_to_label(series_key)),
                    )
                )
            else:
                xs, ys = build_histogram(chart_agg)
                _set_chart(_build_figure(xs, ys, f"Count by {x_key} (finds_arch)"))

            dbg.set_text(
                f"query=finds_arch chart_buckets={len(xs)} x={x_key}"
                + ("" if series_key is None else f" series={series_key}")
            )

            # --- Filter dropdowns: SQL DISTINCT queries ---
            _populate_frag_filter_options_for_dropdowns()

        finally:
            state["_refreshing"] = False

    btn_run.on("click", lambda e: refresh())

    sel_x.on("change", lambda e: refresh())
    sel_chart_type.on("change", lambda e: refresh())

    refresh()

    # --- Help dialog (outside the 3-column row) ---
    with ui.dialog() as help_dialog, ui.card().classes("w-[1200px] max-h-[80vh]"):
        ui.markdown(CHART_GUIDE_PATH.read_text(encoding="utf-8")).classes(
            "max-w-full"
        ).style("max-width: none")
        ui.button(t("chart_help_close"), on_click=help_dialog.close).classes(
            "w-full mt-2"
        )
