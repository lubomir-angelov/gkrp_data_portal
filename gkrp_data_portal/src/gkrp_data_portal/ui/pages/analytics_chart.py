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
from typing import Any

from loguru import logger
from nicegui import app, ui
from starlette.responses import HTMLResponse, PlainTextResponse, Response

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
from gkrp_data_portal.db.session import session_scope
from gkrp_data_portal.ui.repository.analytics_repo import get_distinct_values


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
        "_debounce_timer": None,
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
            inp_q = (
                ui.input("free text (inventory/note/piecetype or finds fields)")
                .props("clearable")
                .classes("w-full")
            )

            with ui.row().classes("w-full gap-2"):
                inp_date_from = (
                    ui.input("from").props("type=date clearable").classes("w-1/2")
                )
                inp_date_to = (
                    ui.input("to").props("type=date clearable").classes("w-1/2")
                )

            inp_limit = ui.number("limit", value=DEFAULT_LIMIT).classes("w-full")

        # Center panel (chart only)
        with ui.column().classes("flex-1 min-w-0"):
            ui.label("Chart").classes("text-subtitle1 font-medium")
            status = ui.label("").classes("text-sm text-gray-600")
            pending = ui.label("").classes("text-xs text-orange-700")
            dbg = ui.label("").classes("text-xs text-gray-500")

            chart = (
                ui.plotly({"data": [], "layout": {"height": 520}})
                .classes("w-full border rounded bg-white")
                .style("height: 520px;")
            )
            chart_id = chart.id

            with ui.row().classes("w-full items-center justify-between gap-2"):
                sel_x = ui.select(options=[], label="Group by (x-axis)").classes(
                    "w-[420px]"
                )

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

        # Right panel (fragments filters)
        with ui.column().classes("w-[320px] shrink-0"):
            ui.label("Fragments").classes("text-subtitle1 font-medium")
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
                    (
                        "Note",
                        ui.input(label="Note")
                        .props("clearable dense")
                        .classes("w-full"),
                    ),
                    (
                        "Inventory",
                        ui.input(label="Inventory")
                        .props("clearable dense")
                        .classes("w-full"),
                    ),
                ]

            # ---- Ornaments section (always visible) ----
            orn_section = ui.column().classes("w-full gap-1 mt-4")
            with orn_section:
                ui.label("Ornaments").classes("text-subtitle1 font-medium")
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
            "site": site,
            "sector": sector,
            "square": square,
            "date_from": date_from,
            "date_to": date_to,
            "q": q,
            "limit": limit,
            "offset": 0,
            "frag_filters": frag_filters_map,
        }

    def _get_type_columns(cols: list[str]) -> list[str]:
        # case-insensitive match; keeps original order
        return [c for c in cols if "type" in c.lower()]

    def _populate_frag_filter_options(items: list[dict[str, Any]]) -> None:
        # Determine which columns are needed by looking at active widgets
        needed: set[str] = set()
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
                site=f["site"],
                sector=f["sector"],
                square=f["square"],
                date_from=f["date_from"],
                date_to=f["date_to"],
                q=f["q"],
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
        if state.get("_refreshing"):
            return
        state["_refreshing"] = True
        try:
            f = _read_filters()
            notes: list[str] = []

            chart_fetch = min(max(f["limit"], 0), CHART_MAX_FETCH)

            res = result_for(
                f["query_id"],
                site=f["site"],
                sector=f["sector"],
                square=f["square"],
                date_from=f["date_from"],
                date_to=f["date_to"],
                q=f["q"],
                limit=chart_fetch,
                offset=f["offset"],
                frag_filters=f.get("frag_filters"),
            )

            total = int(res.total or 0)
            if total == 0:
                _set_chart(plotly_bar([], [], title=f"No results ({f['query_id']})"))
                dbg.set_text(f"query={f['query_id']} rows=0 total=0")
                status.set_text("No results for current filters.")
                return

            if not res.items:
                _set_chart(plotly_bar([], [], title=f"No results ({f['query_id']})"))
                dbg.set_text(f"query={f['query_id']} rows=0 total={res.total}")
                status.set_text("No results for current filters.")
                return

            ui_cols = ui_columns(res.columns) or list(res.columns)

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
                default_x = next((c for c in preferred if c in ui_cols), None) or (
                    ui_cols[0] if ui_cols else None
                )
                state["_suppress_x_change"] = True
                sel_x.set_value(default_x)
                state["_suppress_x_change"] = False
                if default_x:
                    notes.append(f"group-by defaulted to {default_x}")

            x_key = sel_x.value
            xs, ys = build_histogram(res.items, x_key, top_n=30)
            _set_chart(plotly_bar(xs, ys, title=f"Count by {x_key} ({f['query_id']})"))

            _populate_frag_filter_options(res.items)

            dbg.set_text(
                f"query={f['query_id']} rows={len(res.items)} total={res.total} "
                f"x={x_key} buckets={len(xs)}"
            )

            base = f"Chart built from {len(res.items)} rows (total {res.total})."
            if notes:
                base += "  " + " \u2022 ".join(notes)
            status.set_text(base)

        finally:
            state["_refreshing"] = False

    def _trigger_refresh() -> None:
        """Execute the actual refresh (called after debounce)."""
        if sw_autorun.value:
            pending.set_text("")
            refresh()
        else:
            pending.set_text("Filters changed \u2014 click \u201cRun query\u201d")

    def request_refresh() -> None:
        """Schedule a debounced refresh (300 ms)."""
        if state.get("_debounce_timer"):
            state["_debounce_timer"].cancel()
        state["_debounce_timer"] = ui.timer(0.3, once=True, callback=_trigger_refresh)

    btn_run.on("click", lambda e: (pending.set_text(""), refresh()))

    def _on_query_change(e) -> None:
        request_refresh()

    sel_query.on("change", _on_query_change)
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
