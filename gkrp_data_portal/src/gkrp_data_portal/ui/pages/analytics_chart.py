"""NiceGUI page: Analytics (CHART only).

Layout:
- Left: query selector and filters
- Center: chart
- Right: images (from fragment/find image_url)
"""

from __future__ import annotations

import csv
import io
import json
from typing import Any

from loguru import logger
from nicegui import app, ui
from starlette.responses import HTMLResponse, PlainTextResponse, Response

from gkrp_data_portal.ui.repository.analytics_repo import extract_image_urls

from .analytics_common import (
    CHART_MAX_FETCH,
    DEFAULT_LIMIT,
    QUERY_OPTIONS,
    TABLE_MAX_LIMIT,
    build_histogram,
    parse_date,
    plotly_bar,
    result_for,
    ui_columns,
)


@ui.page("/analytics")
def page_analytics_index() -> None:
    """Render the analytics landing page."""
    ui.label("Analytics").classes("text-h5")
    with ui.row().classes("gap-2"):
        ui.button(
            "Chart view",
            on_click=lambda: ui.navigate.to("/analytics/chart"),
            icon="bar_chart",
        )
        ui.button(
            "Table view",
            on_click=lambda: ui.navigate.to("/analytics/table"),
            icon="table_chart",
        )


@ui.page("/analytics/chart")
def page_analytics_chart() -> None:
    """Render the chart-only analytics page."""
    ui.label("Analytics — Chart").classes("text-h5")

    state: dict[str, Any] = {
        "_refreshing": False,
    }

    with ui.row().classes("w-full gap-4 items-start flex-nowrap"):
        with ui.column().classes("w-[340px] shrink-0"):
            ui.label("Query + Filters").classes("text-subtitle1 font-medium")

            sel_query = ui.select(
                options=list(QUERY_OPTIONS.keys()),
                value="Filter #1 (Layers + Fragments)",
                label="Predefined query",
            ).classes("w-full")

            with ui.row().classes("w-full gap-2 items-center"):
                btn_run = ui.button("Run query", icon="play_arrow").classes("flex-1")
                sw_autorun = ui.switch("Auto-run", value=True).props("dense")

            sel_site = ui.select(
                options=["All"],
                value="All",
                label="site",
            ).classes("w-full")
            sel_sector = ui.select(
                options=["All"],
                value="All",
                label="sector",
            ).classes("w-full")
            sel_square = ui.select(
                options=["All"],
                value="All",
                label="square",
            ).classes("w-full")
            sel_layer = ui.select(
                options=["All"],
                value="All",
                label="layer",
            ).classes("w-full")
            sel_layer.set_visibility(False)

            inp_q = ui.input("free text (inventory/note/piecetype...)").props(
                "clearable"
            ).classes("w-full")

            with ui.row().classes("w-full gap-2"):
                inp_date_from = ui.input("from").props("type=date clearable").classes(
                    "w-1/2"
                )
                inp_date_to = ui.input("to").props("type=date clearable").classes(
                    "w-1/2"
                )

            # Kept for consistency with the other analytics page and CSV export.
            # The chart itself does not use this limit; it fetches up to CHART_MAX_FETCH.
            inp_limit = ui.number("limit", value=DEFAULT_LIMIT).classes("w-full")

        with ui.column().classes("flex-1 min-w-0"):
            ui.label("Chart").classes("text-subtitle1 font-medium")
            status = ui.label("").classes("text-sm text-gray-600")
            pending = ui.label("").classes("text-xs text-orange-700")
            dbg = ui.label("").classes("text-xs text-gray-500")

            chart = ui.plotly({"data": [], "layout": {"height": 520}}).classes(
                "w-full border rounded bg-white"
            )
            chart_id = chart.id

            with ui.row().classes("w-full items-center justify-between gap-2"):
                sel_x = ui.select(
                    options=[],
                    label="Group by (x-axis)",
                ).classes("w-[420px]")

                ui.button(
                    "Download PNG",
                    on_click=lambda: ui.run_javascript(
                        f"""
                        Plotly.downloadImage(
                            document.getElementById('{chart_id}')
                                .querySelector('.js-plotly-plot'),
                            {{format: 'png', filename: 'chart'}}
                        );
                        """
                    ),
                )

        with ui.column().classes("w-[320px] shrink-0"):
            ui.label("Images").classes("text-subtitle1 font-medium")
            images_box = ui.scroll_area().classes(
                "w-full h-[820px] border rounded p-2 bg-white"
            )

    def _read_filters() -> dict[str, Any]:
        """Read the current UI filter values."""
        return {
            "query_id": QUERY_OPTIONS.get(sel_query.value, "q1"),
            "site": sel_site.value if sel_site.value != "All" else None,
            "sector": sel_sector.value if sel_sector.value != "All" else None,
            "square": sel_square.value if sel_square.value != "All" else None,
            "layer": sel_layer.value if sel_layer.value != "All" else None,
            "q": (inp_q.value or "").strip() or None,
            "date_from": parse_date(inp_date_from.value),
            "date_to": parse_date(inp_date_to.value),
            "limit": int(inp_limit.value or DEFAULT_LIMIT),
            "offset": 0,
        }

    def _set_images(urls: list[str]) -> None:
        """Render the image strip."""
        images_box.clear()
        with images_box:
            for url in urls[:50]:
                ui.image(url).classes("w-full").props("fit=contain")

    def refresh() -> None:
        """Refresh the chart and image results."""
        if state.get("_refreshing"):
            return

        state["_refreshing"] = True

        try:
            filters = _read_filters()
            query_id = filters["query_id"]

            meta_filters = dict(filters)
            meta_filters["limit"] = 1
            meta_filters["offset"] = 0

            meta = result_for(query_id, **{k: v for k, v in meta_filters.items() if k != "query_id"})
            total = int(meta.total or 0)

            if total == 0:
                chart.figure = plotly_bar([], [], title="No results")
                chart.update()
                _set_images([])
                status.set_text("⚠️ No results.")
                pending.set_text("")
                dbg.set_text("")
                return

            chart_fetch = min(total, CHART_MAX_FETCH)

            data_filters = dict(filters)
            data_filters["limit"] = chart_fetch
            data_filters["offset"] = 0

            res = result_for(query_id, **{k: v for k, v in data_filters.items() if k != "query_id"})

            all_cols = ui_columns(res.columns)
            excluded = {
                "l_layername",
                "l_site",
                "l_square",
                "l_layer",
                "f_note",
                "f_inventory",
                "f_image_url",
            }
            x_axis_cols = [col for col in all_cols if col not in excluded]

            clean_names = {
                col: col[2:].replace("_", " ") if col.startswith(("f_", "l_", "o_")) else col
                for col in x_axis_cols
            }

            sel_x.options = clean_names
            if not x_axis_cols:
                chart.figure = plotly_bar([], [], title="No plottable columns")
                chart.update()
                _set_images(extract_image_urls(res.items))
                status.set_text(f"⚠️ Loaded {len(res.items)} rows, but no chartable columns were found.")
                pending.set_text("")
                dbg.set_text("")
                return

            if not sel_x.value or sel_x.value not in x_axis_cols:
                sel_x.value = x_axis_cols[0]

            xs, ys = build_histogram(res.items, sel_x.value)
            chart.figure = plotly_bar(
                xs,
                ys,
                title=f"Count by {clean_names.get(sel_x.value, sel_x.value)}",
            )
            chart.update()

            _set_images(extract_image_urls(res.items))

            status.set_text(
                f"✅ Chart built from {len(res.items)} rows (Total matches: {total})."
            )
            pending.set_text(
                f"Showing first {chart_fetch} rows for charting."
                if total > CHART_MAX_FETCH
                else ""
            )
            dbg.set_text(f"x-axis: {sel_x.value}")

        except Exception:
            logger.exception("Failed to refresh analytics chart page")
            status.set_text("❌ Failed to build chart.")
            pending.set_text("")
            dbg.set_text("See server logs for details.")
        finally:
            state["_refreshing"] = False

    def update_dropdowns(e: Any) -> None:
        """Update dependent dropdowns after a filter selection changes."""
        from .analytics_common import get_filter_options

        trigger = e.sender.label

        site = sel_site.value if sel_site.value != "All" else None
        sector = sel_sector.value if sel_sector.value != "All" else None
        square = sel_square.value if sel_square.value != "All" else None

        if trigger == "site":
            sel_sector.options = ["All"] + get_filter_options("sector", site=site)
            sel_sector.value = "All"
            sel_square.options = ["All"]
            sel_square.value = "All"
            sel_layer.options = ["All"]
            sel_layer.value = "All"

        elif trigger == "sector":
            sel_square.options = ["All"] + get_filter_options(
                "square",
                site=site,
                sector=sector,
            )
            sel_square.value = "All"
            sel_layer.options = ["All"]
            sel_layer.value = "All"

        elif trigger == "square":
            sel_layer.options = ["All"]
            sel_layer.value = "All"

        if site and sector:
            layers = get_filter_options(
                "layer",
                site=site,
                sector=sector,
                square=square,
            )
            if 0 < len(layers) < 100:
                sel_layer.options = ["All"] + layers
                sel_layer.set_visibility(True)
            else:
                sel_layer.set_visibility(False)
                sel_layer.options = ["All"]
                sel_layer.value = "All"
        else:
            sel_layer.set_visibility(False)
            sel_layer.options = ["All"]
            sel_layer.value = "All"

        if sw_autorun.value:
            refresh()

    def _trigger_refresh(_: Any | None = None) -> None:
        """Refresh only when auto-run is enabled."""
        if sw_autorun.value:
            refresh()

    def _populate_site_options() -> None:
        """Load initial site filter options."""
        try:
            from .analytics_common import get_filter_options

            sel_site.options = ["All"] + get_filter_options("site")
        except Exception:
            logger.exception("Failed to load initial analytics site options")

    sel_query.on("change", _trigger_refresh)
    sel_site.on("change", update_dropdowns)
    sel_sector.on("change", update_dropdowns)
    sel_square.on("change", update_dropdowns)
    sel_layer.on("change", _trigger_refresh)
    sel_x.on("change", lambda _: refresh())
    btn_run.on("click", lambda _: refresh())

    for widget in (inp_q, inp_limit, inp_date_from, inp_date_to):
        widget.on("change", _trigger_refresh)

    _populate_site_options()
    refresh()


@app.get("/api/analytics/data.csv")
def analytics_data_csv(
    query_id: str = "q1",
    site: str | None = None,
    sector: str | None = None,
    square: str | None = None,
    layer: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    q: str | None = None,
    limit: int = DEFAULT_LIMIT,
) -> Response:
    """Export analytics data as CSV."""
    df = parse_date(date_from)
    dt = parse_date(date_to)

    res = result_for(
        query_id,
        site=site or None,
        sector=sector or None,
        square=square or None,
        layer=layer or None,
        date_from=df,
        date_to=dt,
        q=q or None,
        limit=min(max(int(limit), 1), TABLE_MAX_LIMIT),
        offset=0,
    )

    logger.info(
        "analytics_data_csv first_row_keys={}",
        sorted(res.items[0].keys()) if res.items else "NO_ROWS",
    )
    logger.info(
        "analytics_data_csv first_row_sample={}",
        res.items[0] if res.items else "NO_ROWS",
    )

    buf = io.StringIO()
    cols = ui_columns(res.columns)
    writer = csv.DictWriter(buf, fieldnames=cols)
    writer.writeheader()
    for row in res.items:
        writer.writerow({key: row.get(key) for key in cols})

    return Response(
        content=buf.getvalue(),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="analytics_{query_id}.csv"'
        },
    )


@app.get("/api/analytics/chart.json")
def analytics_chart_json(
    query_id: str = "q1",
    x: str | None = None,
    site: str | None = None,
    sector: str | None = None,
    square: str | None = None,
    layer: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    q: str | None = None,
) -> Response:
    """Return chart JSON for the selected analytics query."""
    df = parse_date(date_from)
    dt = parse_date(date_to)

    meta = result_for(
        query_id,
        site=site or None,
        sector=sector or None,
        square=square or None,
        layer=layer or None,
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
        layer=layer or None,
        date_from=df,
        date_to=dt,
        q=q or None,
        limit=chart_fetch,
        offset=0,
    )

    cols = ui_columns(res.columns) or list(res.columns)
    if x and x not in cols:
        x = None
    if not x:
        x = "f_piecetype" if "f_piecetype" in cols else (cols[0] if cols else "")

    xs, ys = build_histogram(res.items, x)
    fig = plotly_bar(xs, ys, title=f"Count by {x} ({query_id})")
    return Response(content=json.dumps(fig), media_type="application/json")


@app.get("/api/analytics/chart.html")
def analytics_chart_html(query_id: str = "q1") -> Response:
    """Return a simple printable HTML wrapper for the analytics chart."""
    qid = query_id or (app.storage.general.get("analytics_last_query_id") or "q1")
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
  <div class="hint">Use browser Print → Save as PDF.</div>
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
    """Return a basic health response."""
    return PlainTextResponse("ok")