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

    # --- UI LAYOUT START ---
    with ui.row().classes("w-full gap-4 items-start flex-nowrap"):
        
        # ЛЯВ ПАНЕЛ (Филтри)
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

            # 1. ДЕФИНИРАНЕ НА ПАДАЩИТЕ МЕНЮТА (Вероника)
            sel_site = ui.select(options=['All'], value='All', label="site").classes("w-full")
            sel_sector = ui.select(options=['All'], value='All', label="sector").classes("w-full")
            sel_square = ui.select(options=['All'], value='All', label="square").classes("w-full")
            sel_layer = ui.select(options=['All'], value='All', label="layer").classes("w-full")
            sel_layer.set_visibility(False) 

            inp_q = ui.input("free text (inventory/note/piecetype...)").props("clearable").classes("w-full")

            with ui.row().classes("w-full gap-2"):
                inp_date_from = ui.input("from").props("type=date clearable").classes("w-1/2")
                inp_date_to = ui.input("to").props("type=date clearable").classes("w-1/2")

            inp_limit = ui.number("limit", value=DEFAULT_LIMIT).classes("w-full")

            ui.separator()
            columns_container = ui.scroll_area().classes("w-full h-[320px] border rounded p-2 bg-white")

        # ЦЕНТРАЛЕН ПАНЕЛ (Графика)
        with ui.column().classes("flex-1 min-w-0"):
            ui.label("Chart").classes("text-subtitle1 font-medium")
            status = ui.label("").classes("text-sm text-gray-600")
            pending = ui.label("").classes("text-xs text-orange-700")
            dbg = ui.label("").classes("text-xs text-gray-500")

            chart = ui.plotly({"data": [], "layout": {"height": 520}}).classes("w-full border rounded bg-white")
            chart_id = chart.id

            with ui.row().classes("w-full items-center justify-between gap-2"):
                sel_x = ui.select(options=[], label="Group by (x-axis)").classes("w-[420px]")
                ui.button("Download PNG", on_click=lambda: ui.run_javascript(f"Plotly.downloadImage(document.getElementById('{chart_id}').querySelector('.js-plotly-plot'), {{format:'png', filename:'chart'}});"))

        # ДЕСЕН ПАНЕЛ (Снимки)
        with ui.column().classes("w-[320px] shrink-0"):
            ui.label("Images").classes("text-subtitle1 font-medium")
            images_box = ui.scroll_area().classes("w-full h-[820px] border rounded p-2 bg-white")

    # --- ЛОГИКА ---
    checkboxes: dict[str, Any] = {}
        def _read_filters() -> dict[str, Any]:
        query_id = QUERY_OPTIONS.get(sel_query.value, "q1")
        # Четем от новите менюта
        s_val = sel_site.value
        sec_val = sel_sector.value
        sq_val = sel_square.value
        lay_val = sel_layer.value

        return {
            "query_id": query_id,
            "site": s_val if s_val != 'All' else None,
            "sector": sec_val if sec_val != 'All' else None,
            "square": sq_val if sq_val != 'All' else None,
            "layer": lay_val if lay_val != 'All' else None,
            "q": (inp_q.value or "").strip() or None,
            "date_from": parse_date(inp_date_from.value),
            "date_to": parse_date(inp_date_to.value),
            "limit": int(inp_limit.value or DEFAULT_LIMIT),
            "offset": 0,
            }

    def refresh() -> None:
        if state.get("_refreshing"): return
        state["_refreshing"] = True
        try:
            f = _read_filters()
            res = result_for(f["query_id"], **f)
            total = int(res.total or 0)
            
            if total == 0:
                status.set_text("⚠️ No results.")
                return

            # Чистене на имената (Вероника)
            all_cols = ui_columns(res.columns)
            excluded = ['l_layername', 'l_site', 'l_square', 'l_layer', 'f_note', 'f_inventory', 'f_image_url']
            ui_cols = [c for c in all_cols if c not in excluded]
            clean_names = {c: c[2:].replace('_', ' ') if c.startswith(('f_','l_','o_')) else c for c in ui_cols}
            
            sel_x.options = clean_names
                if not sel_x.value or sel_x.value not in ui_cols:
                sel_x.value = ui_cols[0] if ui_cols else None

            xs, ys = build_histogram(res.items, sel_x.value)
            chart.figure = plotly_bar(xs, ys, title=f"Count by {clean_names.get(sel_x.value)}")
            chart.update()
            
            _set_images(extract_image_urls(res.items))
            status.set_text(f"✅ Chart built from {len(res.items)} rows (Total {total}).")
        finally:
            state["_refreshing"] = False

    def _set_images(urls: list[str]) -> None:
        images_box.clear()
        with images_box:
            for u in urls[:50]: ui.image(u).classes("w-full").props("fit=contain")

    # 2. ВЕРИЖНА РЕАКЦИЯ (Вероника)
    def update_dropdowns(e):
        from .analytics_common import get_filter_options
        trigger = e.sender.label
        
        s = sel_site.value if sel_site.value != 'All' else None
        sec = sel_sector.value if sel_sector.value != 'All' else None
        sq = sel_square.value if sel_square.value != 'All' else None

        if trigger == 'site':
            sel_sector.options = ['All'] + get_filter_options('sector', site=s)
            sel_sector.value = 'All'
            sel_square.options = ['All']
            sel_square.value = 'All'
        elif trigger == 'sector':
            sel_square.options = ['All'] + get_filter_options('square', site=s, sector=sec)
            sel_square.value = 'All'

        # Логика за Layer
        if s and sec:
            layers = get_filter_options('layer', site=s, sector=sec, square=sq)
            if 0 < len(layers) < 100:
                sel_layer.options = ['All'] + layers
                sel_layer.set_visibility(True)
            else: sel_layer.set_visibility(False)
        else: sel_layer.set_visibility(False)
        
        if sw_autorun.value: refresh()

    # 3. ВРЪЗВАНЕ НА СЪБИТИЯ
    sel_site.on('change', update_dropdowns)
    sel_sector.on('change', update_dropdowns)
    sel_square.on('change', update_dropdowns)
    sel_layer.on('change', lambda: refresh() if sw_autorun.value else None)
    sel_x.on('change', refresh)
    btn_run.on('click', refresh)
    
    for w in (inp_q, inp_limit, inp_date_from, inp_date_to):
        w.on("change", lambda: refresh() if sw_autorun.value else None)

    # 4. СТАРТ: Първоначално пълнене на Site
    try:
        from .analytics_common import get_filter_options
        sel_site.options = ['All'] + get_filter_options('site')
    except: pass
    
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
