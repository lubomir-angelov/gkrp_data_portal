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
from collections import Counter
from datetime import date
from typing import Any, Optional
from loguru import logger

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

TABLE_MAX_LIMIT = 50000      # increase/remove the 5000 cap for the TABLE
CHART_MAX_FETCH = 250000     # safety cap to avoid pulling millions of rows


# Columns you never want to show in UI (table + chart + selectors).
_UI_HIDDEN_COLUMNS = frozenset(
    {
        "l_recordenteredon",
        "l_recordenteredby",
        "l_recordcreatedby",
        "l_level",
        "l_structure",
        "l_includes",
        "l_color1",
        "l_color2",
        "l_description",
        "l_akb_num",
        "f_fragmentid",
        "f_locationid",
        "f_outline",
        "f_speed",
        "f_recrodenteredby",
        "f_recrodenteredon",
        "f_topsize",
        "f_necksize",
        "f_bodysize",
        "f_bottomsize",
        "f_dishheight",
    }
)


def _is_ui_hidden_column(name: str) -> bool:
    return (name or "").strip().lower() in _UI_HIDDEN_COLUMNS


def _ui_columns(columns: list[str]) -> list[str]:
    """Return columns allowed to appear in UI (preserves original casing)."""
    return [c for c in columns if not _is_ui_hidden_column(c)]


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


def _norm_bucket(v: Any) -> str:
    """Normalize values into a histogram bucket label (never empty)."""
    if v is None:
        return "(null)"
    if isinstance(v, str):
        s = v.strip()
        return s if s else "(null)"
    return str(v)


def _build_histogram(rows: list[dict], x_key: str, top_n: int = 30) -> tuple[list[str], list[int]]:
    """Build a top-N histogram for a column from dict rows."""
    if not rows or not x_key:
        return [], []

    c = Counter(_norm_bucket(r.get(x_key)) for r in rows)

    # If everything is "(null)", keep it but you'll see a single bar.
    items = c.most_common(top_n)
    xs = [k for k, _ in items]
    ys = [v for _, v in items]
    return xs, ys

def _build_histogram_from_table_rows(
    table_rows: list[dict[str, Any]],
    x_key: str,
    top_n: int = 30,
) -> tuple[list[str], list[int]]:
    """Build histogram from what is actually rendered in the UI table."""
    if not table_rows or not x_key:
        return [], []

    # table rows include __rowid__; ignore it and count x_key
    c = Counter(_norm_bucket(r.get(x_key)) for r in table_rows)
    items = c.most_common(top_n)
    xs = [k for k, _ in items]
    ys = [v for _, v in items]
    return xs, ys


def _plotly_bar(xs: list[str], ys: list[int], title: str) -> dict:
    return {
        "data": [
            {
                "type": "bar",
                "x": xs,
                "y": ys,
            }
        ],
        "layout": {
            "title": {"text": title},
            "margin": {"l": 50, "r": 20, "t": 50, "b": 90},
            "xaxis": {"automargin": True, "tickangle": -30},
            "yaxis": {"automargin": True},
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
    with ui.row().classes("w-full gap-4 items-start flex-nowrap"):  # <-- IMPORTANT: flex-nowrap
        # Left panel
        with ui.column().classes("w-[340px] shrink-0"):  # <-- shrink-0 keeps it from collapsing
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

            # ✅ compact date inputs (instead of huge calendars)
            with ui.row().classes("w-full gap-2"):
                inp_date_from = ui.input("from").props("type=date clearable").classes("w-1/2")
                inp_date_to = ui.input("to").props("type=date clearable").classes("w-1/2")

            inp_limit = ui.number("limit", value=DEFAULT_LIMIT).classes("w-full")

            ui.separator()
            ui.label("Columns").classes("text-subtitle1 font-medium")

            with ui.row().classes("w-full justify-between"):
                btn_select_all = ui.button("Select all")
                btn_clear_all = ui.button("Deselect all")

            columns_container = ui.scroll_area().classes(
                "w-full h-[420px] border rounded p-2 bg-white"
            )

        # Center panel  ✅ min-w-0 prevents Plotly/table from forcing wrapping
        with ui.column().classes("flex-1 min-w-0"):
            ui.label("Chart").classes("text-subtitle1 font-medium")
            status = ui.label("").classes("text-sm text-gray-600")
            pending = ui.label("").classes("text-xs text-orange-700")
            dbg = ui.label("").classes("text-xs text-gray-500")

            chart = ui.plotly({"data": [], "layout": {"height": 420}}).classes(
                "w-full border rounded bg-white"
            ).style("height: 420px;")

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
                            "window.open('/api/analytics/chart.html?query_id=' + encodeURIComponent(window.__gkrp_query_id || 'q1'), '_blank');"
                        ),
                    )

            ui.separator()
            ui.label("Table (scrollable)").classes("text-subtitle1 font-medium")

            table_wrap = ui.element("div").classes("w-full border rounded bg-white").style(
                "height: 340px; overflow: auto;"
            )
            with table_wrap:
                table = ui.table(columns=[], rows=[], row_key="__rowid__", pagination=25).classes("w-full")

        # Right panel
        with ui.column().classes("w-[320px] shrink-0"):
            ui.label("Images").classes("text-subtitle1 font-medium")
            images_box = ui.scroll_area().classes("w-full h-[820px] border rounded p-2 bg-white")


    # ---- Helpers to build UI ----
    checkboxes: dict[str, Any] = {}  # col_name -> checkbox

    def _set_chart(figure: dict[str, Any]) -> None:
        """Update the Plotly widget in a NiceGUI-version-tolerant way."""
        # NiceGUI Plotly APIs vary by version:
        # - some expose `.figure`
        # - some accept `.update(figure)`
        # - some expose `.props(...)`
        # We try in a safe order.

        # 1) Preferred: figure attribute exists
        if hasattr(chart, "figure"):
            setattr(chart, "figure", figure)
            try:
                chart.update()
            except TypeError:
                # some versions don't need args
                chart.update()
        else:
            # 2) update() may accept the figure directly
            try:
                chart.update(figure)  # type: ignore[arg-type]
            except TypeError:
                # 3) props() may exist
                if hasattr(chart, "props"):
                    # Plotly element is typically driven by a `figure` prop in some builds
                    chart.props(f":figure='{json.dumps(figure)}'")  # type: ignore[attr-defined]
                    chart.update()
                else:
                    # 4) last resort: recreate by replacing content (rarely needed)
                    raise RuntimeError(
                        "Cannot update Plotly chart: this NiceGUI Plotly element exposes neither "
                        "'.figure' nor '.update(figure)' nor '.props'."
                    )

        # Force Plotly resize/redraw after DOM/layout settles (prevents "axes only").
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




    def _set_table(items: list[dict[str, Any]], visible_cols: list[str]) -> None:
        """Render the bottom table; this becomes the canonical dataset for charting."""
        cols = [{"name": c, "label": c, "field": c} for c in visible_cols]
        rows: list[dict[str, Any]] = []

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
        # preserve selections if possible, but only among available columns
        if state["selected_columns"]:
            current = set(state["selected_columns"]) & set(all_columns)
        else:
            current = set(all_columns)
    
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
        limit = max(1, min(limit, TABLE_MAX_LIMIT))

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
        # Prevent re-entrant refresh storms (sel_x.set_value triggers change events).
        if state.get("_refreshing"):
            return
        state["_refreshing"] = True
        try:
            f = _read_filters()
            notes: list[str] = []

            # (A) TABLE result (limited)
            res_table = _result_for(
                f["query_id"],
                site=f["site"],
                sector=f["sector"],
                square=f["square"],
                date_from=f["date_from"],
                date_to=f["date_to"],
                q=f["q"],
                limit=f["limit"],     # <-- user limit applies ONLY here
                offset=f["offset"],
            )

            # (B) CHART result (full, or capped)
            total = int(res_table.total or 0)
            chart_fetch = min(max(total, 0), CHART_MAX_FETCH)

            # If total is 0, we can bail early with empty visuals
            if total == 0:
                # filter on cols which should be visible
                ui_cols0 = _ui_columns(res_table.columns)

                # render te table, chart and images sections
                _set_table([], ui_cols0[:25] if ui_cols0 else [])
                _set_chart(_plotly_bar([], [], title=f"No results ({f['query_id']})"))
                _set_images([])

                # show results message for chart plot
                dbg.set_text(f"query={f['query_id']} rows=0 total=0")
                
                return

            # If chart needs more than the table limit, fetch more rows for chart aggregation
            if chart_fetch <= len(res_table.items):
                res_chart = res_table
            else:
                res_chart = _result_for(
                    f["query_id"],
                    site=f["site"],
                    sector=f["sector"],
                    square=f["square"],
                    date_from=f["date_from"],
                    date_to=f["date_to"],
                    q=f["q"],
                    limit=chart_fetch,   # <-- full dataset (or capped)
                    offset=0,
                )

            if not res_chart.items:
                # Empty result: keep columns, but show empty visuals
                _set_table([], [c for c, cb in checkboxes.items() if cb.value] or (res_chart.columns[:25] if res_chart.columns else []))
                _set_chart(_plotly_bar([], [], title=f"No results ({f['query_id']})"))
                _set_images([])

                dbg.set_text(f"query={f['query_id']} rows=0 total={res_chart.total} x={sel_x.value}")
                status.set_text("⚠️ No results for current filters.")

                return
            
            ui_cols = _ui_columns(res_chart.columns)
            if not ui_cols:
                ui_cols = list(res_chart.columns)  # safety fallback

            # (1) columns panel (checkboxes)
            if not checkboxes or list(checkboxes.keys()) != ui_cols:
                _rebuild_column_checkboxes(ui_cols)

            visible_cols = [c for c, cb in checkboxes.items() if cb.value]
            if not visible_cols:
                visible_cols = ui_cols[:25] if ui_cols else []
                notes.append("no columns selected → defaulted to first 25")

            if not [c for c, cb in checkboxes.items() if cb.value]:
                notes.append("no columns selected → defaulted to first 25")

            # (2) table
            _set_table(res_table.items, visible_cols)

            # (3) chart - ensure x-axis options and a stable default without re-triggering refresh
            sel_x.options = list(ui_cols)

            preferred = [
                "l_site",
                "l_sector",
                "l_square",
                "l_context",
                "l_layername",
                "l_level",
                "f_piecetype",
                "f_category",
                "f_form",
                "f_fragmenttype",
                "f_technology",
                "o_primary_",
                "o_secondary",
                "o_tertiary",
            ]

            if not sel_x.value or sel_x.value not in ui_cols:
                default_x = (
                    next((c for c in preferred if c in ui_cols), None)
                    or (ui_cols[0] if ui_cols else None)
                )
                state["_suppress_x_change"] = True
                sel_x.set_value(default_x)
                state["_suppress_x_change"] = False
                if default_x:
                    notes.append(f"group-by defaulted to {default_x}")


            x_key = sel_x.value

            xs, ys = _build_histogram(res_chart.items, x_key, top_n=30)

            # Extra debug (matches what you reported)
            sample_x = _norm_bucket(res_chart.items[0].get(x_key)) if (res_chart.items and x_key) else None
            top_bucket = xs[0] if xs else None

            fig = _plotly_bar(xs, ys, title=f"Count by {x_key} ({f['query_id']})")
            _set_chart(fig)

            dbg.set_text(
                f"query={f['query_id']} "
                f"table_rows={len(res_table.items)} total={res_table.total} "
                f"chart_rows={len(res_chart.items)} "
                f"x={x_key} buckets={len(xs)} sample_x={sample_x!r} top_bucket={top_bucket!r}"
            )
            
            # (4) images
            urls = extract_image_urls(res_table.items)
            _set_images(urls)

            base = f"✅ Returned {len(res_chart.items)} rows (total {res_chart.total})."
            if notes:
                base += "  " + " • ".join(notes)
            status.set_text(base)

        finally:
            state["_refreshing"] = False
    

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


    def request_refresh() -> None:
        """Refresh immediately if Auto-run is enabled, otherwise mark pending changes."""
        if sw_autorun.value:
            pending.set_text("")
            refresh()
        else:
            pending.set_text("Filters changed — click “Run query”")

    btn_run.on("click", lambda e: (pending.set_text(""), refresh()))

    # ---- Wiring events ----
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

    logger.info("DEBUG first_row_keys:", sorted(res.items[0].keys()) if res.items else "NO_ROWS")
    logger.info("DEBUG first_row_sample:", res.items[0] if res.items else "NO_ROWS")

    buf = io.StringIO()
    cols = _ui_columns(res.columns)
    writer = csv.DictWriter(buf, fieldnames=cols)
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

    # Get total cheaply with a tiny query
    meta = _result_for(
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
    
    res = _result_for(
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

    ui_cols = _ui_columns(res.columns)
    if not ui_cols:
        ui_cols = list(res.columns)  # safety fallback

    if x and (x not in ui_cols):
        x = None

    if not x:
        x = "f_piecetype" if "f_piecetype" in ui_cols else (ui_cols[0] if ui_cols else "")

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
