"""NiceGUI page: Analytics (CHART only)."""

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
        ui.button("Chart view", on_click=lambda: ui.navigate.to("/analytics/chart"), icon="bar_chart")
        ui.button("Table view", on_click=lambda: ui.navigate.to("/analytics/table"), icon="table_chart")

@ui.page("/analytics/chart")
def page_analytics_chart() -> None:
    ui.label("Analytics — Chart").classes("text-h5")

    state: dict[str, Any] = {"_refreshing": False}

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

            # Йерархични падащи менюта (Вероника)
            sel_site = ui.select(options=["All"], value="All", label="site").classes("w-full")
            sel_sector = ui.select(options=["All"], value="All", label="sector").classes("w-full")
            sel_square = ui.select(options=["All"], value="All", label="square").classes("w-full")
            sel_layer = ui.select(options=["All"], value="All", label="layer").classes("w-full")


            # Полета за дата
            with ui.row().classes("w-full gap-2"):
                inp_date_from = ui.input("from").props("type=date clearable").classes("w-1/2")
                inp_date_to = ui.input("to").props("type=date clearable").classes("w-1/2")

            inp_limit = ui.number("limit", value=DEFAULT_LIMIT).classes("w-full")

        # ЦЕНТРАЛЕН ПАНЕЛ (Графика)
        with ui.column().classes("flex-1 min-w-0"):
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

    def _read_filters() -> dict[str, Any]:
        return {
            "query_id": QUERY_OPTIONS.get(sel_query.value, "q1"),
            "site": sel_site.value if sel_site.value != "All" else None,
            "sector": sel_sector.value if sel_sector.value != "All" else None,
            "square": sel_square.value if sel_square.value != "All" else None,
            "layer": sel_layer.value if sel_layer.value != "All" else None,
            "q": None, # Текстовото поле е премахнато
            "date_from": parse_date(inp_date_from.value),
            "date_to": parse_date(inp_date_to.value),
            "limit": int(inp_limit.value or DEFAULT_LIMIT),
            "offset": 0,
        }

    def _set_images(urls: list[str]) -> None:
        images_box.clear()
        with images_box:
            for url in urls[:50]:
                ui.image(url).classes("w-full").props("fit=contain")

    def refresh() -> None:
        if state.get("_refreshing"): return
        state["_refreshing"] = True
        try:
            f = _read_filters()
            # Извикваме базата с филтрите
            res = result_for(f["query_id"], **{k: v for k, v in f.items() if k != "query_id"})
            total = int(res.total or 0)

            if total == 0:
                chart.figure = plotly_bar([], [], title="No results"); chart.update()
                _set_images([]); status.set_text("⚠️ No results."); return

            # Подготовка на чистите имена за Х-оста
            all_cols = ui_columns(res.columns)
            excluded = {"l_layername", "l_site", "l_square", "l_layer", "f_note", "f_inventory", "f_image_url"}
            x_cols = [c for c in all_cols if c not in excluded]
            clean_names = {c: c[2:].replace("_", " ") if c.startswith(("f_", "l_", "o_")) else c for c in x_cols}
            
            sel_x.options = clean_names
            if not sel_x.value or sel_x.value not in x_cols:
                sel_x.value = x_cols[0] if x_cols else None

            xs, ys = build_histogram(res.items, sel_x.value)
            chart.figure = plotly_bar(xs, ys, title=f"Count by {clean_names.get(sel_x.value, sel_x.value)}")
            chart.update()
            
            _set_images(extract_image_urls(res.items))
            status.set_text(f"✅ Loaded {len(res.items)} rows (Total matches: {total}).")
        except Exception:
            logger.exception("Refresh failed")
            status.set_text("❌ Error loading data.")
        finally:
            state["_refreshing"] = False

    def update_dropdowns(e: Any) -> None:
        from .analytics_common import get_filter_options
        
        # Вземаме текущите стойности от менютата
        s_val = sel_site.value if sel_site.value != "All" else None
        sec_val = sel_sector.value if sel_sector.value != "All" else None
        sq_val = sel_square.value if sel_square.value != "All" else None

        # Кое меню е променил потребителят?
        if e.sender == sel_site:
            # Сменен обект -> Търсим неговите сектори
            opts = get_filter_options("sector", site=s_val)
            sel_sector.options = ["All"] + opts
            sel_sector.value = "All"
            # Ресет на долните
            sel_square.options = ["All"]; sel_square.value = "All"
            sel_layer.options = ["All"]; sel_layer.value = "All"
        
        elif e.sender == sel_sector:
            # Сменен сектор -> Търсим неговите квадрати
            opts = get_filter_options("square", site=s_val, sector=sec_val)
            sel_square.options = ["All"] + opts
            sel_square.value = "All"
            # Ресет на пластовете
            sel_layer.options = ["All"]; sel_layer.value = "All"

        elif e.sender == sel_square:
            # Сменен квадрат -> Търсим пластовете
            opts = get_filter_options("layer", site=s_val, sector=sec_val, square=sq_val)
            sel_layer.options = ["All"] + opts
            sel_layer.value = "All"

        # Пускаме графиката
        if sw_autorun.value:
            refresh()

    # Свързване на събития
    sel_site.on("change", update_dropdowns)
    sel_sector.on("change", update_dropdowns)
    sel_square.on("change", update_dropdowns)
    sel_layer.on("change", lambda: refresh() if sw_autorun.value else None)
    sel_x.on("change", refresh)
    btn_run.on("click", refresh)
    

    for w in (inp_limit, inp_date_from, inp_date_to):
        w.on("change", lambda: refresh() if sw_autorun.value else None)

    # --- ПЪРВОНАЧАЛНО ПЪЛНЕНЕ НА SITE ---
    def load_initial_data():
        try:
            from .analytics_common import get_filter_options
            sites = get_filter_options("site")
            if sites:
                sel_site.options = ["All"] + sites
                sel_site.update() # Важно за NiceGUI
        except Exception:
            logger.exception("Initial site load failed")

    load_initial_data()
    refresh()

# --- Ендпойнтите за експорт (CSV, JSON, HTML) трябва да са под този ред ---