"""NiceGUI page: Analytics (TABLE only).

Layout:
- Left: query selector, filters
- Center: grid (scrollable, with per-column dropdown filters)
"""

from __future__ import annotations

import json
from typing import Any

from nicegui import app, ui

from gkrp_data_portal.db.session import session_scope
from gkrp_data_portal.ui.repository.analytics_repo import (
    get_layer_hierarchy,
)

from .analytics_common import (
    DEFAULT_LIMIT,
    LOCALE,
    QUERY_OPTIONS,
    TABLE_MAX_LIMIT,
    result_for,
    ui_columns,
)


def _select_to_list(widget: ui.select) -> list[str] | None:
    """Convert a NiceGUI select widget value to a filtered list of strings.

    Returns None when the widget has no selection.
    """
    vals = widget.value
    if isinstance(vals, list) and vals:
        return [str(v).strip() for v in vals if str(v).strip()]
    if isinstance(vals, str) and vals.strip():
        return [vals.strip()]
    return None


@ui.page("/analytics/table")
def page_analytics_table() -> None:
    """Render the Analytics Table page.

    This page provides:
    - a left panel for selecting a predefined query and applying filters,
    - a center panel with an interactive AG Grid table (filterable/sortable).

    Notes:
        - Date filters are intentionally removed (date_from/date_to are passed as None).
        - All columns are shown (no column toggles).
        - Layer filters follow a Site->Sector->Square->Layer hierarchy.
    """
    ui.label(LOCALE["title_analytics_table"]).classes("text-h5 text-blue-600")

    # Mutable state shared across callbacks (kept in-memory for this page instance).
    state: dict[str, Any] = {
        "query_id": "q2",
        "_refreshing": False,
        "last_items": [],
        "last_columns": [],
        "_hierarchy": {},
        "_all_sites": [],
        "_all_sectors": [],
        "_all_squares": [],
        "_all_layers": [],
    }

    with ui.row().classes("w-full gap-4 items-start flex-nowrap"):
        # Left panel
        with ui.column().classes("w-[340px] shrink-0"):
            ui.label(LOCALE["panel_query_filters"]).classes("text-subtitle1 font-medium text-blue-600")

            sel_query = ui.select(
                options=list(QUERY_OPTIONS.keys()),
                value=LOCALE["query_filter2"],
                label=LOCALE["label_predefined_query"],
            ).classes("w-full")

            with ui.row().classes("w-full gap-2 items-center"):
                btn_run = ui.button(LOCALE["btn_run_query"], icon="play_arrow").classes("flex-1")

            with ui.scroll_area().classes(
                "w-full h-[420px] border rounded p-2 bg-white"
            ):
                sel_site_t = (
                    ui.select(
                        options=[],
                        label=LOCALE["label_site"],
                        multiple=True,
                        clearable=True,
                        with_input=True,
                    )
                    .classes("w-full")
                    .props("dense")
                )

                sel_sector_t = (
                    ui.select(
                        options=[],
                        multiple=True,
                        clearable=True,
                        with_input=True,
                        label=LOCALE["label_sector"],
                    )
                    .classes("w-full")
                    .props("dense")
                )

                sel_square_t = (
                    ui.select(
                        options=[],
                        multiple=True,
                        clearable=True,
                        with_input=True,
                        label=LOCALE["label_square"],
                    )
                    .classes("w-full")
                    .props("dense")
                )

                sel_layer_t = (
                    ui.select(
                        options=[],
                        multiple=True,
                        clearable=True,
                        with_input=True,
                        label=LOCALE["label_layer"],
                    )
                    .classes("w-full")
                    .props("dense")
                )

            inp_limit = ui.number("limit", value=DEFAULT_LIMIT).classes("w-full")

        # Center panel (grid)
        with ui.column().classes("flex-1 min-w-0"):
            ui.label(LOCALE["panel_table"]).classes("text-subtitle1 font-medium text-blue-600")
            status = ui.label("").classes("text-sm text-gray-600")
            dbg = ui.label("").classes("text-xs text-gray-500")

            # AG Grid: horizontal scrollbar stays at the bottom of the grid viewport
            grid = (
                ui.aggrid(
                    {
                        "columnDefs": [],
                        "rowData": [],
                        "defaultColDef": {
                            "resizable": True,
                            "sortable": True,
                            "filter": True,
                            "floatingFilter": True,
                            "menuTabs": ["filterMenuTab"],
                        },
                        "animateRows": True,
                        "pagination": True,
                        "paginationPageSize": 25,
                        "alwaysShowHorizontalScroll": True,
                        "alwaysShowVerticalScroll": True,
                    }
                )
                .classes("w-full border rounded bg-white")
                .style("height: 740px;")
            )

            ui.label(LOCALE["tip_filter_header"]).classes("text-xs text-gray-500 mt-1")

    def _set_grid(items: list[dict[str, Any]], visible_cols: list[str]) -> None:
        """Populate AG Grid with the given rows and visible columns.

        Uses the AG Grid Set Filter for each column to provide value dropdowns.
        """
        col_defs = [
            {
                "headerName": c,
                "field": c,
                "width": 200,
                "minWidth": 150,
                "filter": "agSetColumnFilter",
                "filterParams": {"buttons": ["reset", "apply"], "closeOnApply": True},
            }
            for c in visible_cols
        ]

        row_data: list[dict[str, Any]] = []
        for i, r in enumerate(items):
            rr: dict[str, Any] = {"__rowid__": i}
            for c in visible_cols:
                rr[c] = r.get(c)
            row_data.append(rr)

        grid.options["columnDefs"] = col_defs
        grid.options["rowData"] = row_data
        grid.update()

    def _apply_view() -> None:
        """Apply all columns to the grid."""
        items: list[dict[str, Any]] = state.get("last_items", [])
        ui_cols: list[str] = state.get("last_columns", [])

        _set_grid(items, ui_cols)

        dbg.set_text(
            f"query={state.get('query_id')} table_rows={len(items)} cols={len(ui_cols)}"
        )

    def _fetch_layer_cache() -> None:
        """Fetch the layer hierarchy from the database and cache it in state."""
        with session_scope() as db:
            hierarchy_data = get_layer_hierarchy(db, query_id="q2")
        state["_hierarchy"] = hierarchy_data.get("hierarchy", {})
        state["_all_sites"] = hierarchy_data.get("all_sites", [])
        state["_all_sectors"] = hierarchy_data.get("all_sectors", [])
        state["_all_squares"] = hierarchy_data.get("all_squares", [])
        state["_all_layers"] = hierarchy_data.get("all_layers", [])

    def _populate_layer_options_hierarchical() -> None:
        """Populate layer dropdown options based on the cached hierarchy.

        Enforces the Site -> Sector -> Square -> Layer cascade:
        - Selecting a site filters sectors, squares, and layers to that site.
        - Selecting a sector filters squares and layers to that sector.
        - Selecting a square filters layers to that square.
        """
        hierarchy = state["_hierarchy"]

        sel_site_t.clear()
        sel_sector_t.clear()
        sel_square_t.clear()
        sel_layer_t.clear()

        all_sites = state["_all_sites"]

        sel_site_t.set_options(all_sites)
        sel_site_t.update()

        # Apply cascade based on current selections
        site_val = _select_to_list(sel_site_t)

        # Determine effective site(s) for filtering
        if site_val:
            sites_to_use = site_val
        else:
            sites_to_use = all_sites

        # Filter sectors based on selected sites
        if sites_to_use:
            filtered_sectors = set()
            for site in sites_to_use:
                site_hier = hierarchy.get(site, {})
                filtered_sectors.update(site_hier.keys())
            filtered_sectors = sorted(filtered_sectors)
            sel_sector_t.set_options(filtered_sectors)
            sel_sector_t.update()

            # If current sector selection is no longer valid, clear it
            current_sector = _select_to_list(sel_sector_t)
            if current_sector:
                valid_sectors = set(filtered_sectors)
                for s in current_sector:
                    if s not in valid_sectors:
                        sel_sector_t.set_value(None)
                        break
        else:
            sel_sector_t.set_value(None)

        # Determine effective sectors
        sector_sel = _select_to_list(sel_sector_t)
        if sector_sel:
            sectors_to_use = sector_sel
        else:
            sectors_to_use = (sel_sector_t.options or [])[:]

        # Filter squares based on selected sites and sectors
        if sites_to_use and sectors_to_use:
            filtered_squares = set()
            for site in sites_to_use:
                site_hier = hierarchy.get(site, {})
                for sector in sectors_to_use:
                    sector_hier = site_hier.get(sector, {})
                    filtered_squares.update(sector_hier.keys())
            filtered_squares = sorted(filtered_squares)
            sel_square_t.set_options(filtered_squares)
            sel_square_t.update()

            current_square = _select_to_list(sel_square_t)
            if current_square:
                valid_squares = set(filtered_squares)
                for sq in current_square:
                    if sq not in valid_squares:
                        sel_square_t.set_value(None)
                        break
        else:
            sel_square_t.set_value(None)

        # Determine effective squares
        square_sel = _select_to_list(sel_square_t)
        if square_sel:
            squares_to_use = square_sel
        else:
            squares_to_use = (sel_square_t.options or [])[:]

        # Filter layers based on selected sites, sectors, and squares
        if sites_to_use and sectors_to_use and squares_to_use:
            filtered_layers = set()
            for site in sites_to_use:
                site_hier = hierarchy.get(site, {})
                for sector in sectors_to_use:
                    sector_hier = site_hier.get(sector, {})
                    for square in squares_to_use:
                        square_layers = sector_hier.get(square, [])
                        filtered_layers.update(square_layers)
            filtered_layers = sorted(filtered_layers)
            sel_layer_t.set_options(filtered_layers)
            sel_layer_t.update()

            current_layer = _select_to_list(sel_layer_t)
            if current_layer:
                valid_layers = set(filtered_layers)
                for item in current_layer:
                    if item not in valid_layers:
                        sel_layer_t.set_value(None)
                        break
        else:
            sel_layer_t.set_value(None)

    def _read_filters() -> dict[str, Any]:
        """Read current filter widgets and normalize the filter payload."""
        query_id = QUERY_OPTIONS.get(sel_query.value, "q2")

        layer_filters_map: dict[str, list[str] | None] = {}
        layer_filters_map["Site"] = _select_to_list(sel_site_t)
        layer_filters_map["Sector"] = _select_to_list(sel_sector_t)
        layer_filters_map["Square"] = _select_to_list(sel_square_t)
        layer_filters_map["Layer"] = _select_to_list(sel_layer_t)

        limit = int(inp_limit.value or DEFAULT_LIMIT)
        limit = max(1, min(limit, TABLE_MAX_LIMIT))

        # Persist and expose selected query id.
        state["query_id"] = query_id
        app.storage.general["analytics_last_query_id"] = query_id
        ui.run_javascript(f"window.__gkrp_query_id = {json.dumps(query_id)};")

        return {
            "query_id": query_id,
            "layer_filters": layer_filters_map,
            "limit": limit,
            "offset": 0,
        }

    def refresh() -> None:
        """Run the backend query and refresh grid + status labels."""
        if state.get("_refreshing"):
            return
        state["_refreshing"] = True
        try:
            _fetch_layer_cache()
            _populate_layer_options_hierarchical()

            f = _read_filters()

            res = result_for(
                f["query_id"],
                layer_filters=f.get("layer_filters"),
                limit=f["limit"],
                offset=f["offset"],
            )

            total = int(res.total or 0)
            if total == 0:
                state["last_items"] = []
                state["last_columns"] = []
                _set_grid([], [])
                dbg.set_text(f"query={f['query_id']} rows=0 total=0")
                status.set_text(LOCALE["status_no_results"])
                return

            ui_cols = ui_columns(res.columns) or list(res.columns)

            state["last_items"] = res.items
            state["last_columns"] = ui_cols

            _apply_view()

            dbg.set_text(
                f"query={f['query_id']} table_rows={len(res.items)} total={res.total}"
            )
            status.set_text(LOCALE["status_returned"].format(count=len(res.items), total=res.total))

        finally:
            state["_refreshing"] = False

    btn_run.on("click", lambda e: refresh())

    sel_query.on("change", lambda e: refresh())

    def _on_site_change(e) -> None:
        _populate_layer_options_hierarchical()

    def _on_sector_change(e) -> None:
        _populate_layer_options_hierarchical()

    def _on_square_change(e) -> None:
        _populate_layer_options_hierarchical()

    def _on_layer_change(e) -> None:
        _populate_layer_options_hierarchical()

    sel_site_t.on("change", _on_site_change)
    sel_sector_t.on("change", _on_sector_change)
    sel_square_t.on("change", _on_square_change)
    sel_layer_t.on("change", _on_layer_change)

    inp_limit.on("change", lambda e: refresh())

    # Initial load
    refresh()
