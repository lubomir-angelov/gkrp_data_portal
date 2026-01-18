"""NiceGUI page: Analytics (layout + predefined queries + exports).

Layout:
- Left: query selector, filters, column toggles
- Center: chart
- Bottom: wide table (scrollable)
- Right: images (from fragment/find image_url)
"""

from __future__ import annotations

import csv
import io
import json
from datetime import date
from typing import Any, Optional

from nicegui import app, ui
from starlette.responses import HTMLResponse, PlainTextResponse, Response

from gkrp_data_portal.db.session import session_scope
from gkrp_data_portal.ui.repository.analytics_repo import (
    AnalyticsResult,
    extract_image_urls,
    query_finds,
    query_q1_layers_fragments,
    query_q2_layers_fragments_ornaments,
)

QUERY_OPTIONS = {
    "Filter #1 (Layers + Fragments)": "q1",
    "Filter #2 (Layers + Fragments + Ornaments)": "q2",
    "Finds (tblfinds)": "finds",
}

DEFAULT_LIMIT = 500


def _parse_date(s: Optional[str]) -> Optional[date]:
    if not s:
        return None
    try:
        return date.fromisoformat(s)
    except ValueError:
        return None


def _result_for(query_id: str, **kwargs) -> AnalyticsResult:
    with session_scope() as db:
        if query_id == "q1":
            return query_q1_layers_fragments(db, **kwargs)
        if query_id == "q2":
            return query_q2_layers_fragments_ornaments(db, **kwargs)
        return query_finds(db, **kwargs)


def _build_histogram(items: list[dict[str, Any]], x_key: str) -> tuple[list[str], list[int]]:
    counts: dict[str, int] = {}
    for r in items:
        v = r.get(x_key)
        label = str(v) if v is not None and str(v).strip() else "(empty)"
        counts[label] = counts.get(label, 0) + 1
    # stable ordering by count desc
    pairs = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    xs = [p[0] for p in pairs][:50]  # cap to keep chart readable
    ys = [p[1] for p in pairs][:50]
    return xs, ys


def _plotly_bar(xs: list[str], ys: list[int], *, title: str) -> dict[str, Any]:
    return {
        "data": [{"type": "bar", "x": xs, "y": ys}],
        "layout": {
            "title": {"text": title},
            "margin": {"l": 50, "r": 20, "t": 50, "b": 140},
            "xaxis": {"automargin": True, "tickangle": -30},
            "yaxis": {"title": {"text": "Count"}},
        },
        "config": {
            "displaylogo": False,
            "responsive": True,
            "toImageButtonOptions": {"format": "png", "filename": "analytics_chart"},
        },
    }


@ui.page("/analytics")
def page_analytics() -> None:
    ui.label("Analytics").classes("text-h5")

    # ---- State ----
    state: dict[str, Any] = {
        "query_id": "q1",
        "site": "",
        "sector": "",
        "square": "",
        "date_from": "",
        "date_to": "",
        "q": "",
        "limit": DEFAULT_LIMIT,
        "selected_columns": set(),  # filled after first load
        "x_axis": None,
    }

    # ---- Layout ----
    with ui.row().classes("w-full gap-3"):
        # Left panel
        with ui.column().classes("w-[320px]"):
            ui.label("Query + Filters").classes("text-subtitle1")

            sel_query = ui.select(
                options=list(QUERY_OPTIONS.keys()),
                value="Filter #1 (Layers + Fragments)",
                label="Predefined query",
            ).classes("w-full")

            inp_site = ui.input("site").props("clearable").classes("w-full")
            inp_sector = ui.input("sector").props("clearable").classes("w-full")
            inp_square = ui.input("square").props("clearable").classes("w-full")
            inp_q = ui.input("free text (inventory/note/piecetype or finds fields)").props("clearable").classes("w-full")

            with ui.row().classes("w-full"):
                inp_date_from = ui.date("from").classes("w-full")
                inp_date_to = ui.date("to").classes("w-full")

            inp_limit = ui.number("limit", value=DEFAULT_LIMIT).classes("w-full")

            ui.separator()
            ui.label("Columns").classes("text-subtitle1")

            btn_row = ui.row().classes("w-full justify-between")
            with btn_row:
                btn_select_all = ui.button("Select all")
                btn_clear_all = ui.button("Deselect all")

            columns_container = ui.scroll_area().classes("w-full h-[420px] border rounded p-2")

        # Center panel
        with ui.column().classes("flex-1"):
            ui.label("Chart").classes("text-subtitle1")

            chart = ui.plotly({}).classes("w-full border rounded")
            # chart.id is used by client-side export
            chart_id = chart.id

            with ui.row().classes("w-full justify-between"):
                sel_x = ui.select(options=[], label="Group by (x-axis)").classes("w-[420px]")
                ui.button(
                    "Download PNG",
                    on_click=lambda: ui.run_javascript(
                        f"""
                        (function() {{
                          const el = document.getElementById('{chart_id}');
                          if (!el) return;
                          const gd = el.querySelector('.js-plotly-plot') || el;
                          if (window.Plotly && gd) {{
                            Plotly.downloadImage(gd, {{format:'png', filename:'analytics_chart', height:600, width:1000}});
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
                            Plotly.downloadImage(gd, {{format:'jpeg', filename:'analytics_chart', height:600, width:1000}});
                          }}
                        }})();
                        """
                    ),
                )
                ui.button(
                    "Print / Save as PDF",
                    on_click=lambda: ui.run_javascript(
                        f"window.open('/api/analytics/chart.html?query_id=' + encodeURIComponent(window.__gkrp_query_id || 'q1'), '_blank');"
                    ),
                )

            ui.separator()
            ui.label("Table (scrollable)").classes("text-subtitle1")

            # Bottom table container (horizontal + vertical scrolling)
            table_wrap = ui.element("div").classes("w-full border rounded").style(
                "height: 340px; overflow: auto;"
            )
            with table_wrap:
                table = ui.table(columns=[], rows=[], row_key="__rowid__", pagination=25).classes("w-full")

        # Right panel
        with ui.column().classes("w-[320px]"):
            ui.label("Images").classes("text-subtitle1")
            images_box = ui.scroll_area().classes("w-full h-[820px] border rounded p-2")

    # ---- Helpers to build UI ----
    checkboxes: dict[str, Any] = {}  # col_name -> checkbox

    def _set_chart(figure: dict[str, Any]) -> None:
        chart.options = figure
        chart.update()

    def _set_table(items: list[dict[str, Any]], visible_cols: list[str]) -> None:
        cols = [{"name": c, "label": c, "field": c} for c in visible_cols]
        rows = []
        for i, r in enumerate(items):
            rr = {"__rowid__": i}
            for c in visible_cols:
                rr[c] = r.get(c)
            rows.append(rr)

        table.columns = cols
        table.rows = rows
        table.update()

    def _set_images(urls: list[str]) -> None:
        images_box.clear()
        with images_box:
            if not urls:
                ui.label("No image URLs in current result.")
                return
            for u in urls[:50]:
                ui.image(u).classes("w-full").props("fit=contain")

    def _rebuild_column_checkboxes(all_columns: list[str]) -> None:
        # preserve selections if possible
        current = set(state["selected_columns"]) if state["selected_columns"] else set(all_columns)

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
        date_from = _parse_date(inp_date_from.value)
        date_to = _parse_date(inp_date_to.value)

        limit = int(inp_limit.value or DEFAULT_LIMIT)
        limit = max(1, min(limit, 5000))

        # store for export endpoint
        state["query_id"] = query_id
        app.storage.general["analytics_last_query_id"] = query_id  # global fallback
        # Also expose for JS open('/api/analytics/chart.html?...')
        ui.run_javascript(f"window.__gkrp_query_id = {json.dumps(query_id)};")

        return {
            "query_id": query_id,
            "site": site,
            "sector": sector,
            "square": square,
            "date_from": date_from,
            "date_to": date_to,
            "q": q,
            "limit": limit,
            "offset": 0,
        }

    def refresh() -> None:
        f = _read_filters()
        res = _result_for(
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

        # (1) columns panel
        if not checkboxes:
            _rebuild_column_checkboxes(res.columns)
        else:
            # if schema changes per query switch, rebuild
            if set(res.columns) != set(checkboxes.keys()):
                _rebuild_column_checkboxes(res.columns)

        visible_cols = [c for c, cb in checkboxes.items() if cb.value]
        if not visible_cols:
            visible_cols = res.columns[:25]  # fallback

        # (2) table
        _set_table(res.items, visible_cols)

        # (3) chart
        # pick x-axis: prefer user selection; else default to a common field
        sel_x.options = res.columns
        if not sel_x.value:
            default_x = "f_piecetype" if "f_piecetype" in res.columns else (res.columns[0] if res.columns else None)
            sel_x.set_value(default_x)

        x_key = sel_x.value
        if x_key:
            xs, ys = _build_histogram(res.items, x_key)
            fig = _plotly_bar(xs, ys, title=f"Count by {x_key} ({f['query_id']})")
            _set_chart(fig)

        # (4) images
        urls = extract_image_urls(res.items)
        _set_images(urls)

    # ---- Column toggle buttons ----
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

    # ---- Wiring events ----
    sel_query.on("change", lambda e: refresh())
    for w in (inp_site, inp_sector, inp_square, inp_q, inp_limit):
        w.on("change", lambda e: refresh())
    inp_date_from.on("change", lambda e: refresh())
    inp_date_to.on("change", lambda e: refresh())
    sel_x.on("change", lambda e: refresh())

    # first load
    refresh()


# -------------------------
# Export endpoints
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
    df = _parse_date(date_from)
    dt = _parse_date(date_to)

    res = _result_for(
        query_id,
        site=site or None,
        sector=sector or None,
        square=square or None,
        date_from=df,
        date_to=dt,
        q=q or None,
        limit=min(max(int(limit), 1), 5000),
        offset=0,
    )

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=res.columns)
    writer.writeheader()
    for row in res.items:
        writer.writerow({k: row.get(k) for k in res.columns})

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
    limit: int = DEFAULT_LIMIT,
) -> Response:
    df = _parse_date(date_from)
    dt = _parse_date(date_to)

    res = _result_for(
        query_id,
        site=site or None,
        sector=sector or None,
        square=square or None,
        date_from=df,
        date_to=dt,
        q=q or None,
        limit=min(max(int(limit), 1), 5000),
        offset=0,
    )

    if not x:
        x = "f_piecetype" if "f_piecetype" in res.columns else (res.columns[0] if res.columns else "")

    xs, ys = _build_histogram(res.items, x)
    fig = _plotly_bar(xs, ys, title=f"Count by {x} ({query_id})")

    return Response(content=json.dumps(fig), media_type="application/json")


@app.get("/api/analytics/chart.html")
def analytics_chart_html(query_id: str = "q1") -> Response:
    """Printable chart view. Users can Print -> Save as PDF."""
    # Minimal: render a default chart (client can also call chart.json directly).
    # Use last query stored by UI as a fallback.
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
    #chart {{ width: 100vw; height: 95vh; }}
    .hint {{ padding: 10px; }}
  </style>
</head>
<body>
  <div class="hint">Use browser Print → Save as PDF.</div>
  <div id="chart"></div>
  <script>
    const fig = {fig_json};
    Plotly.newPlot('chart', fig.data, fig.layout, fig.config);
  </script>
</body>
</html>
"""
    return HTMLResponse(html)


@app.get("/api/analytics/health")
def analytics_health() -> Response:
    return PlainTextResponse("ok")
