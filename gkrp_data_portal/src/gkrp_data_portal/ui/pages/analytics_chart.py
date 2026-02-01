"""NiceGUI page: Analytics (CHART only).

Layout:
- Left: query selector, filters, column toggles
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
    ui.label("Analytics — Chart").classes("text-h5")

    state: dict[str, Any] = {
        "query_id": "q1",
        "_refreshing": False,
        "_suppress_x_change": False,
    }

    with ui.row().classes("w-full gap-4 items-start flex-nowrap"):
        # Left panel
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

            inp_site = ui.input("site").props("clearable").classes("w-full")
            inp_sector = ui.input("sector").props("clearable").classes("w-full")
            inp_square = ui.input("square").props("clearable").classes("w-full")
            inp_q = ui.input("free text (inventory/note/piecetype or finds fields)").props("clearable").classes("w-full")

            with ui.row().classes("w-full gap-2"):
                inp_date_from = ui.input("from").props("type=date clearable").classes("w-1/2")
                inp_date_to = ui.input("to").props("type=date clearable").classes("w-1/2")

            inp_limit = ui.number("limit", value=DEFAULT_LIMIT).classes("w-full")

            ui.separator()
            ui.label("Columns").classes("text-subtitle1 font-medium")

            with ui.row().classes("w-full justify-between"):
                btn_select_all = ui.button("Select all")
                btn_clear_all = ui.button("Deselect all")

            columns_container = ui.scroll_area().classes("w-full h-[420px] border rounded p-2 bg-white")

        # Center panel (chart only)
        with ui.column().classes("flex-1 min-w-0"):
            ui.label("Chart").classes("text-subtitle1 font-medium")
            status = ui.label("").classes("text-sm text-gray-600")
            pending = ui.label("").classes("text-xs text-orange-700")
            dbg = ui.label("").classes("text-xs text-gray-500")

            chart = ui.plotly({"data": [], "layout": {"height": 520}}).classes("w-full border rounded bg-white").style(
                "height: 520px;"
            )
            chart_id = chart.id

            with ui.row().classes("w-full items-center justify-between gap-2"):
                sel_x = ui.select(options=[], label="Group by (x-axis)").classes("w-[420px]")

                with ui.row().classes("gap-2"):
                    ui.button(
                        "Download PNG",
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
                        "Download JPG",
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
                        "Print / Save as PDF",
                        on_click=lambda: ui.run_javascript(
                            "window.open('/api/analytics/chart.html?query_id=' + encodeURIComponent(window.__gkrp_query_id || 'q1'), '_blank');"
                        ),
                    )

        # Right panel (images)
        with ui.column().classes("w-[320px] shrink-0"):
            ui.label("Images").classes("text-subtitle1 font-medium")
            images_box = ui.scroll_area().classes("w-full h-[820px] border rounded p-2 bg-white")

    # --- local state ---
    checkboxes: dict[str, Any] = {}

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
                    raise RuntimeError("Cannot update Plotly chart on this NiceGUI version.")

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

    def _set_images(urls: list[str]) -> None:
        images_box.clear()
        with images_box:
            if not urls:
                ui.label("No image URLs in current result.")
                return
            for u in urls[:50]:
                ui.image(u).classes("w-full").props("fit=contain")

    def _rebuild_column_checkboxes(all_columns: list[str]) -> None:
        current = set(all_columns) if not state.get("selected_columns") else (set(state["selected_columns"]) & set(all_columns))
        columns_container.clear()
        checkboxes.clear()
        with columns_container:
            for c in all_columns:
                cb = ui.checkbox(c, value=(c in current)).classes("text-sm")
                checkboxes[c] = cb
        state["selected_columns"] = current

    def _read_filters() -> dict[str, Any]:
        query_id = QUERY_OPTIONS.get(sel_query.value, "q1")

        site = (inp_site.value or "").strip() or None
        sector = (inp_sector.value or "").strip() or None
        square = (inp_square.value or "").strip() or None
        q = (inp_q.value or "").strip() or None
        date_from = parse_date(inp_date_from.value)
        date_to = parse_date(inp_date_to.value)

        limit = int(inp_limit.value or DEFAULT_LIMIT)
        limit = max(1, min(limit, TABLE_MAX_LIMIT))

        state["query_id"] = query_id
        app.storage.general["analytics_last_query_id"] = query_id
        ui.run_javascript(f"window.__gkrp_query_id = {json.dumps(query_id)};")

        return {
            "query_id": query_id,
            "site": site,
            "sector": sector,
            "square": square,
            "date_from": date_from,
            "date_to": date_to,
            "q": q,
            "limit": limit,  # used for “table-like” fetch (images + small sample)
            "offset": 0,
        }

    def refresh() -> None:
        if state.get("_refreshing"):
            return
        state["_refreshing"] = True
        try:
            f = _read_filters()
            notes: list[str] = []

            # (A) limited fetch: used for images (and cheap metadata like total)
            res_limited = result_for(
                f["query_id"],
                site=f["site"],
                sector=f["sector"],
                square=f["square"],
                date_from=f["date_from"],
                date_to=f["date_to"],
                q=f["q"],
                limit=f["limit"],
                offset=f["offset"],
            )

            total = int(res_limited.total or 0)
            if total == 0:
                _set_chart(plotly_bar([], [], title=f"No results ({f['query_id']})"))
                _set_images([])
                dbg.set_text(f"query={f['query_id']} rows=0 total=0")
                status.set_text("⚠️ No results for current filters.")
                return

            # (B) chart fetch (full, capped)
            chart_fetch = min(max(total, 0), CHART_MAX_FETCH)
            res_chart = (
                res_limited
                if chart_fetch <= len(res_limited.items)
                else result_for(
                    f["query_id"],
                    site=f["site"],
                    sector=f["sector"],
                    square=f["square"],
                    date_from=f["date_from"],
                    date_to=f["date_to"],
                    q=f["q"],
                    limit=chart_fetch,
                    offset=0,
                )
            )

            if not res_chart.items:
                _set_chart(plotly_bar([], [], title=f"No results ({f['query_id']})"))
                _set_images([])
                dbg.set_text(f"query={f['query_id']} rows=0 total={res_chart.total}")
                status.set_text("⚠️ No results for current filters.")
                return

            ui_cols = ui_columns(res_chart.columns) or list(res_chart.columns)
            if not checkboxes or list(checkboxes.keys()) != ui_cols:
                _rebuild_column_checkboxes(ui_cols)

            sel_x.options = list(ui_cols)

            preferred = [
                "l_site",
                "l_sector",
                "l_square",
                "l_context",
                "l_layername",
                "f_piecetype",
                "f_category",
                "f_form",
                "f_fragmenttype",
                "f_technology",
            ]

            if not sel_x.value or sel_x.value not in ui_cols:
                default_x = next((c for c in preferred if c in ui_cols), None) or (ui_cols[0] if ui_cols else None)
                state["_suppress_x_change"] = True
                sel_x.set_value(default_x)
                state["_suppress_x_change"] = False
                if default_x:
                    notes.append(f"group-by defaulted to {default_x}")

            x_key = sel_x.value
            xs, ys = build_histogram(res_chart.items, x_key, top_n=30)
            _set_chart(plotly_bar(xs, ys, title=f"Count by {x_key} ({f['query_id']})"))

            urls = extract_image_urls(res_limited.items)
            _set_images(urls)

            dbg.set_text(
                f"query={f['query_id']} limited_rows={len(res_limited.items)} total={res_limited.total} "
                f"chart_rows={len(res_chart.items)} x={x_key} buckets={len(xs)}"
            )

            base = f"✅ Chart built from {len(res_chart.items)} rows (total {res_chart.total})."
            if notes:
                base += "  " + " • ".join(notes)
            status.set_text(base)

        finally:
            state["_refreshing"] = False

    def _select_all() -> None:
        for cb in checkboxes.values():
            cb.set_value(True)
        refresh()

    def _deselect_all() -> None:
        for cb in checkboxes.values():
            cb.set_value(False)
        refresh()

    btn_select_all.on("click", lambda e: _select_all())
    btn_clear_all.on("click", lambda e: _deselect_all())

    def request_refresh() -> None:
        if sw_autorun.value:
            pending.set_text("")
            refresh()
        else:
            pending.set_text("Filters changed — click “Run query”")

    btn_run.on("click", lambda e: (pending.set_text(""), refresh()))

    sel_query.on("change", lambda e: request_refresh())
    for w in (inp_site, inp_sector, inp_square, inp_q, inp_limit):
        w.on("change", lambda e: request_refresh())
    inp_date_from.on("change", lambda e: request_refresh())
    inp_date_to.on("change", lambda e: request_refresh())

    def _on_x_change(e) -> None:
        if state.get("_suppress_x_change"):
            return
        request_refresh()

    sel_x.on("change", _on_x_change)

    refresh()


# -------------------------
# Export endpoints (kept here so they register once)
# -------------------------

@app.get("/api/analytics/data.csv")
def analytics_data_csv(
    query_id: str = "q1",
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

    logger.info("DEBUG first_row_keys: {}", sorted(res.items[0].keys()) if res.items else "NO_ROWS")
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
        headers={"Content-Disposition": f'attachment; filename="analytics_{query_id}.csv"'},
    )


@app.get("/api/analytics/chart.json")
def analytics_chart_json(
    query_id: str = "q1",
    x: str | None = None,
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

    xs, ys = build_histogram(res.items, x)
    fig = plotly_bar(xs, ys, title=f"Count by {x} ({query_id})")
    return Response(content=json.dumps(fig), media_type="application/json")


@app.get("/api/analytics/chart.html")
def analytics_chart_html(query_id: str = "q1") -> Response:
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
    return PlainTextResponse("ok")
