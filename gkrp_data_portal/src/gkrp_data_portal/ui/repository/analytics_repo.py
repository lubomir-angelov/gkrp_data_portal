"""Analytics repository: predefined queries + safe filtering.

Implements the two predefined queries (layers+fragments; layers+fragments+ornaments)
and a third selector for finds (tblfinds).

All result columns are prefixed to avoid collisions:
- l_<col> for tbllayers
- f_<col> for tblfragments
- o_<col> for tblornaments
- fi_<col> for tblfinds
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Optional

from sqlalchemy import text
from sqlalchemy.engine import RowMapping
from sqlalchemy.orm import Session

from gkrp_data_portal.models.archaeology import (
    Find,
    Tbllayer,
    Tblfragment,
    Tblornament,
    Tblfind,
)


@dataclass(frozen=True)
class AnalyticsResult:
    items: list[dict[str, Any]]
    total: int
    columns: list[str]


def _model_select_list(prefix: str, alias: str, model) -> list[str]:
    cols = []
    for col in model.__table__.columns:
        cols.append(f"{alias}.{col.name} AS {prefix}{col.name}")
    return cols


def _apply_frag_filters(
    clauses: list[str],
    params: dict[str, Any],
    frag_filters: dict[str, Any],
    frag_alias: str = "f",
    orn_alias: str = "o",
) -> None:
    """Apply fragment field filters from the UI dropdowns.

    Maps UI labels to SQL column references using the given aliases.
    Multi-select uses ANY/ILIKE; single text inputs use ILIKE.
    """
    label_to_col: dict[str, str] = {
        "Piecetype": f"{frag_alias}.piecetype",
        "Technology": f"{frag_alias}.technology",
        "Baking": f"{frag_alias}.baking",
        "Color / Primary color": f"{frag_alias}.primarycolor",
        "Covering": f"{frag_alias}.covering",
        "Surface": f"{frag_alias}.surface",
        "Wall thickness": f"{frag_alias}.wallthickness",
        "Handle type": f"{frag_alias}.handletype",
        "Handle size": f"{frag_alias}.handlesize",
        "Bottom type": f"{frag_alias}.bottomtype",
        "Category": f"{frag_alias}.category",
        "Form": f"{frag_alias}.form",
        "Type": f"{frag_alias}.type",
        "Subtype": f"{frag_alias}.subtype",
        "Variant": f"{frag_alias}.variant",
        "Primary": f"{orn_alias}.primary_",
        "Secondary": f"{orn_alias}.secondary",
        "Tertiary": f"{orn_alias}.tertiary",
        "Quarternary": f"{orn_alias}.quarternary",
        "Color / color1": f"{orn_alias}.color1",
        "Encrust color": f"{orn_alias}.encrustcolor1",
    }
    for label, values in frag_filters.items():
        col = label_to_col.get(label)
        if not col:
            continue
        col_expr = f"{col}::text"
        safe_label = label.replace(" ", "_")
        if isinstance(values, list) and values:
            param_name = f"frag_{safe_label}"
            params[param_name] = values
            conditions = " OR ".join(
                [f"{col_expr} ILIKE :{param_name}_{i}" for i, v in enumerate(values)]
            )
            clauses.append(f"({conditions})")
            for i, v in enumerate(values):
                params[f"{param_name}_{i}"] = f"%{v}%"
        elif isinstance(values, str) and values.strip():
            param_name = f"frag_{safe_label}"
            params[param_name] = f"%{values.strip()}%"
            clauses.append(f"{col_expr} ILIKE :{param_name}")


def _apply_arch_filters(
    clauses: list[str],
    params: dict[str, Any],
    arch_filters: dict[str, Any],
) -> None:
    """Apply archaeological finds field filters from the UI dropdowns.

    Maps UI labels to SQL column references using the 'fi' alias.
    Multi-select uses ILIKE with OR; single text inputs use ILIKE.
    """
    label_to_col: dict[str, str] = {
        "Find Type": "fi.find_type",
        "Material": "fi.material",
        "Coin": "fi.coin",
        "Denomination": "fi.denomination",
        "Mint": "fi.mint",
        "Year": "fi.year",
        "Inv No": "fi.inv_no",
        "Depth": "fi.depth_m",
        "Context": "fi.context",
    }
    for label, values in arch_filters.items():
        col = label_to_col.get(label)
        if not col:
            continue
        col_expr = f"{col}::text"
        safe_label = label.replace(" ", "_")
        if isinstance(values, list) and values:
            param_name = f"arch_{safe_label}"
            params[param_name] = values
            conditions = " OR ".join(
                [f"{col_expr} ILIKE :{param_name}_{i}" for i, v in enumerate(values)]
            )
            clauses.append(f"({conditions})")
            for i, v in enumerate(values):
                params[f"{param_name}_{i}"] = f"%{v}%"
        elif isinstance(values, str) and values.strip():
            param_name = f"arch_{safe_label}"
            params[param_name] = f"%{values.strip()}%"
            clauses.append(f"{col_expr} ILIKE :{param_name}")


def _apply_layer_filters(
    clauses: list[str],
    params: dict[str, Any],
    layer_filters: dict[str, Any],
    layer_alias: str = "l",
) -> None:
    """Apply layer field filters from the UI dropdowns.

    Maps UI labels to SQL column references using the given alias.
    Multi-select uses ANY/ILIKE; single text inputs use ILIKE.
    """
    label_to_col: dict[str, str] = {
        "Site": f"{layer_alias}.site",
        "Sector": f"{layer_alias}.sector",
        "Square": f"{layer_alias}.square",
        "Layer": f"{layer_alias}.layer",
    }
    for label, values in layer_filters.items():
        col = label_to_col.get(label)
        if not col:
            continue
        col_expr = f"{col}::text"
        safe_label = label.replace(" ", "_")
        if isinstance(values, list) and values:
            param_name = f"layer_{safe_label}"
            params[param_name] = values
            conditions = " OR ".join(
                [f"{col_expr} ILIKE :{param_name}_{i}" for i, v in enumerate(values)]
            )
            clauses.append(f"({conditions})")
            for i, v in enumerate(values):
                params[f"{param_name}_{i}"] = f"%{v}%"
        elif isinstance(values, str) and values.strip():
            param_name = f"layer_{safe_label}"
            params[param_name] = f"%{values.strip()}%"
            clauses.append(f"{col_expr} ILIKE :{param_name}")


def _build_where(
    *,
    query_id: str,
    site: Optional[str],
    sector: Optional[str],
    square: Optional[str],
    date_from: Optional[date],
    date_to: Optional[date],
    q: Optional[str],
    frag_filters: Optional[dict[str, Any]] = None,
    layer_filters: Optional[dict[str, Any]] = None,
    layer_alias: str = "l",
    frag_alias: str = "f",
    orn_alias: str = "o",
) -> tuple[str, dict[str, Any]]:
    """Build a safe WHERE clause using only whitelisted filters."""
    clauses: list[str] = []
    params: dict[str, Any] = {}

    # Layer-scoped filters (always safe; all queries include layer_alias)
    if layer_filters:
        _apply_layer_filters(clauses, params, layer_filters, layer_alias)
    else:
        if site:
            clauses.append(f"{layer_alias}.site ILIKE :site")
            params["site"] = f"%{site}%"
        if sector:
            clauses.append(f"{layer_alias}.sector ILIKE :sector")
            params["sector"] = f"%{sector}%"
        if square:
            clauses.append(f"{layer_alias}.square ILIKE :square")
            params["square"] = f"%{square}%"

    if date_from:
        clauses.append(f"{layer_alias}.recordenteredon >= :date_from")
        params["date_from"] = date_from
    if date_to:
        clauses.append(f"{layer_alias}.recordenteredon <= :date_to")
        params["date_to"] = date_to

    # Free-text: differs slightly by query (which aliases exist)
    if q:
        params["q"] = f"%{q}%"
        if query_id in ("q1", "q2"):
            clauses.append(
                "(COALESCE(f.inventory,'') ILIKE :q OR COALESCE(f.note,'') ILIKE :q OR COALESCE(f.piecetype::text,'') ILIKE :q)"
            )
        elif query_id == "finds":
            clauses.append(
                "(COALESCE(fi.description,'') ILIKE :q OR COALESCE(fi.findtype,'') ILIKE :q OR COALESCE(fi.inventory,'') ILIKE :q)"
            )

    # Fragment field filters (only applied for q2 which has f alias)
    if frag_filters and query_id in ("q2",):
        _apply_frag_filters(clauses, params, frag_filters, frag_alias, orn_alias)

    # Archaeological finds filters (only applied for finds_arch)
    if frag_filters and query_id == "finds_arch":
        _apply_arch_filters(clauses, params, frag_filters)

    if not clauses:
        return "", params
    return "WHERE " + " AND ".join(clauses), params


def _run_sql(
    db: Session,
    *,
    sql: str,
    params: dict[str, Any],
    limit: int,
    offset: int,
) -> list[RowMapping]:
    sql_paginated = f"{sql} LIMIT :limit OFFSET :offset"
    params2 = dict(params)
    params2["limit"] = limit
    params2["offset"] = offset
    return db.execute(text(sql_paginated), params2).mappings().all()


def _count_sql(db: Session, *, count_sql: str, params: dict[str, Any]) -> int:
    row = db.execute(text(count_sql), params).scalar_one()
    return int(row)


def query_q1_layers_fragments(
    db: Session,
    *,
    site: Optional[str] = None,
    sector: Optional[str] = None,
    square: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    q: Optional[str] = None,
    limit: int = 500,
    offset: int = 0,
    frag_filters: Optional[dict[str, Any]] = None,
    layer_filters: Optional[dict[str, Any]] = None,
) -> AnalyticsResult:
    """Filter #1: tbllayers INNER JOIN tblfragments (no ornaments)."""
    select_cols = _model_select_list("l_", "l", Tbllayer) + _model_select_list(
        "f_", "f", Tblfragment
    )
    base = f"""
    SELECT
      {", ".join(select_cols)}
    FROM tbllayers l
    INNER JOIN tblfragments f ON l.layerid = f.locationid
    """

    where_sql, params = _build_where(
        query_id="q1",
        site=site,
        sector=sector,
        square=square,
        date_from=date_from,
        date_to=date_to,
        q=q,
        frag_filters=frag_filters,
        layer_filters=layer_filters,
    )

    sql = f"{base}\n{where_sql}\nORDER BY l.layerid DESC, f.fragmentid DESC"
    count_sql = f"SELECT COALESCE(SUM(f_count), 0) FROM ({base}\n{where_sql}) x"

    rows = _run_sql(db, sql=sql, params=params, limit=limit, offset=offset)
    total = _count_sql(db, count_sql=count_sql, params=params)

    items = [dict(r) for r in rows]
    columns = (
        list(items[0].keys()) if items else [c.split(" AS ")[-1] for c in select_cols]
    )
    return AnalyticsResult(items=items, total=total, columns=columns)


def query_q2_layers_fragments_ornaments(
    db: Session,
    *,
    site: Optional[str] = None,
    sector: Optional[str] = None,
    square: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    q: Optional[str] = None,
    limit: int = 500,
    offset: int = 0,
    frag_filters: Optional[dict[str, Any]] = None,
    layer_filters: Optional[dict[str, Any]] = None,
) -> AnalyticsResult:
    """Filter #2: tbllayers LEFT JOIN tblfragments LEFT JOIN tblornaments.

    Uses a window function to de-duplicate f.count across ornament rows,
    so each fragment's count is summed only once in histograms and totals.
    Fragments without ornaments are included via LEFT JOIN.
    """
    select_cols = (
        _model_select_list("l_", "l", Tbllayer)
        + _model_select_list("f_", "f", Tblfragment)
        + _model_select_list("o_", "o", Tblornament)
    )
    base = f"""
    SELECT
      {", ".join(select_cols)},
      MAX(f.count) OVER (PARTITION BY f.fragmentid) AS f_count_deduped
    FROM tbllayers l
    INNER JOIN tblfragments f ON l.layerid = f.locationid
    LEFT JOIN tblornaments o ON f.fragmentid = o.fragmentid
    """

    where_sql, params = _build_where(
        query_id="q2",
        site=site,
        sector=sector,
        square=square,
        date_from=date_from,
        date_to=date_to,
        q=q,
        frag_filters=frag_filters,
        layer_filters=layer_filters,
        layer_alias="l",
    )

    sql = f"{base}\n{where_sql}\nORDER BY l.layerid DESC, f.fragmentid DESC, o.ornamentid DESC"
    count_where_sql, count_params = _build_where(
        query_id="q2",
        site=site,
        sector=sector,
        square=square,
        date_from=date_from,
        date_to=date_to,
        q=q,
        frag_filters=frag_filters,
        layer_filters=layer_filters,
        layer_alias="l2",
        frag_alias="f2",
        orn_alias="o2",
    )
    count_sql = f"""SELECT COALESCE((
        SELECT SUM(f2.count) FROM (
            SELECT DISTINCT f2.fragmentid, f2.count
            FROM tblfragments f2
            INNER JOIN tbllayers l2 ON l2.layerid = f2.locationid
            {count_where_sql}
        ) f2
    ), 0)"""

    rows = _run_sql(db, sql=sql, params=params, limit=limit, offset=offset)
    total = _count_sql(db, count_sql=count_sql, params=count_params)

    items = [dict(r) for r in rows]
    columns = (
        list(items[0].keys())
        if items
        else [c.split(" AS ")[-1] for c in select_cols] + ["f_count_deduped"]
    )
    return AnalyticsResult(items=items, total=total, columns=columns)


def query_finds(
    db: Session,
    *,
    site: Optional[str] = None,
    sector: Optional[str] = None,
    square: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    q: Optional[str] = None,
    limit: int = 500,
    offset: int = 0,
    frag_filters: Optional[dict[str, Any]] = None,
    layer_filters: Optional[dict[str, Any]] = None,
) -> AnalyticsResult:
    """Finds selector: tblfinds tied to layers/fragments/ornaments (left joins).

    Uses a window function to de-duplicate f.count across ornament rows.
    """
    select_cols = (
        _model_select_list("fi_", "fi", Tblfind)
        + _model_select_list("l_", "l", Tbllayer)
        + _model_select_list("f_", "f", Tblfragment)
        + _model_select_list("o_", "o", Tblornament)
    )

    base = f"""
    SELECT
      {", ".join(select_cols)},
      MAX(f.count) OVER (PARTITION BY f.fragmentid) AS f_count_deduped
    FROM tblfinds fi
    INNER JOIN tbllayers l ON l.layerid = fi.layerid
    LEFT JOIN tblfragments f ON f.fragmentid = fi.fragmentid
    LEFT JOIN tblornaments o ON o.ornamentid = fi.ornamentid
    """

    where_sql, params = _build_where(
        query_id="finds",
        site=site,
        sector=sector,
        square=square,
        date_from=date_from,
        date_to=date_to,
        q=q,
        frag_filters=frag_filters,
        layer_filters=layer_filters,
        layer_alias="l",
    )

    sql = f"{base}\n{where_sql}\nORDER BY fi.findid DESC"
    count_where_sql, count_params = _build_where(
        query_id="finds",
        site=site,
        sector=sector,
        square=square,
        date_from=date_from,
        date_to=date_to,
        q=q,
        frag_filters=frag_filters,
        layer_filters=layer_filters,
        layer_alias="l2",
        frag_alias="f2",
        orn_alias="o2",
    )
    count_sql = f"""SELECT COALESCE((
        SELECT SUM(f2.count) FROM (
            SELECT DISTINCT f2.fragmentid, f2.count
            FROM tblfinds fi2
            INNER JOIN tbllayers l2 ON l2.layerid = fi2.layerid
            LEFT JOIN tblfragments f2 ON f2.fragmentid = fi2.fragmentid
            LEFT JOIN tblornaments o2 ON o2.ornamentid = fi2.ornamentid
            {count_where_sql}
        ) f2
    ), 0)"""

    rows = _run_sql(db, sql=sql, params=params, limit=limit, offset=offset)
    total = _count_sql(db, count_sql=count_sql, params=count_params)

    items = [dict(r) for r in rows]
    columns = (
        list(items[0].keys())
        if items
        else [c.split(" AS ")[-1] for c in select_cols] + ["f_count_deduped"]
    )
    return AnalyticsResult(items=items, total=total, columns=columns)


def extract_image_urls(items: list[dict[str, Any]]) -> list[str]:
    """Collect unique image URLs from fragments/finds columns if present."""
    urls: list[str] = []
    seen: set[str] = set()

    for r in items:
        for key in ("f_image_url", "fi_image_url"):
            v = r.get(key)
            if isinstance(v, str) and v.strip():
                if v not in seen:
                    seen.add(v)
                    urls.append(v)

    return urls


# Column definitions for DISTINCT queries: (label, sql_col_expr, query_ids)
_DISTINCT_COL_DEFS: list[tuple[str, str, tuple[str, ...]]] = [
    ("Site", "l.site", ("q2", "finds")),
    ("Sector", "l.sector", ("q2", "finds")),
    ("Square", "l.square", ("q2", "finds")),
    ("Layer", "l.layer", ("q2", "finds")),
    ("Piecetype", "f.piecetype", ("q2",)),
    ("Technology", "f.technology", ("q2",)),
    ("Baking", "f.baking", ("q2",)),
    ("Color / Primary color", "f.primarycolor", ("q2",)),
    ("Covering", "f.covering", ("q2",)),
    ("Surface", "f.surface", ("q2",)),
    ("Wall thickness", "f.wallthickness", ("q2",)),
    ("Handle type", "f.handletype", ("q2",)),
    ("Handle size", "f.handlesize", ("q2",)),
    ("Bottom type", "f.bottomtype", ("q2",)),
    ("Category", "f.category", ("q2",)),
    ("Form", "f.form", ("q2",)),
    ("Type", "f.type", ("q2",)),
    ("Subtype", "f.subtype", ("q2",)),
    ("Variant", "f.variant", ("q2",)),
    ("Note", "f.note", ("q2",)),
    ("Inventory", "f.inventory", ("q2",)),
    ("Primary", "o.primary_", ("q2",)),
    ("Secondary", "o.secondary", ("q2",)),
    ("Tertiary", "o.tertiary", ("q2",)),
    ("Quarternary", "o.quarternary", ("q2",)),
    ("Color / color1", "o.color1", ("q2",)),
    ("Encrust color", "o.encrustcolor1", ("q2",)),
    # Archaeological finds columns
    ("Find Type", "fi.find_type", ("finds_arch",)),
    ("Material", "fi.material", ("finds_arch",)),
    ("Coin", "fi.coin", ("finds_arch",)),
    ("Denomination", "fi.denomination", ("finds_arch",)),
    ("Mint", "fi.mint", ("finds_arch",)),
    ("Year", "fi.year", ("finds_arch",)),
    ("Inv No", "fi.inv_no", ("finds_arch",)),
    ("Depth", "fi.depth_m", ("finds_arch",)),
    ("Context", "fi.context", ("finds_arch",)),
]


def get_distinct_values(
    db: Session,
    *,
    query_id: str,
    site: Optional[str] = None,
    sector: Optional[str] = None,
    square: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    q: Optional[str] = None,
    frag_filters: Optional[dict[str, Any]] = None,
    layer_filters: Optional[dict[str, Any]] = None,
    columns: Optional[set[str]] = None,
) -> dict[str, list[str]]:
    """Return DISTINCT values for filter dropdown columns via SQL.

    *columns* limits which columns are fetched; if None all applicable columns
    are returned.  The result is keyed by the UI label (e.g. ``"Piecetype"``).
    """
    # Determine which table aliases apply
    if query_id == "q2":
        base = (
            "FROM tbllayers l "
            "INNER JOIN tblfragments f ON l.layerid = f.locationid "
            "INNER JOIN tblornaments o ON f.fragmentid = o.fragmentid"
        )
    elif query_id == "finds":
        base = (
            "FROM tblfinds fi "
            "INNER JOIN tbllayers l ON l.layerid = fi.layerid "
            "LEFT JOIN tblfragments f ON f.fragmentid = fi.fragmentid "
            "LEFT JOIN tblornaments o ON o.ornamentid = fi.ornamentid"
        )
    elif query_id == "finds_arch":
        base = "FROM finds fi LEFT JOIN tbllayers l ON l.layerid = fi.layerid"
    else:
        return {}

    where_sql, params = _build_where(
        query_id=query_id,
        site=site,
        sector=sector,
        square=square,
        date_from=date_from,
        date_to=date_to,
        q=q,
        frag_filters=frag_filters,
        layer_filters=layer_filters,
    )

    # Build list of (label, col_expr) pairs
    if columns:
        active = [
            (lbl, expr, qids)
            for lbl, expr, qids in _DISTINCT_COL_DEFS
            if lbl in columns and query_id in qids
        ]
    else:
        active = [
            (lbl, expr, qids)
            for lbl, expr, qids in _DISTINCT_COL_DEFS
            if query_id in qids
        ]

    result: dict[str, list[str]] = {}
    for label, col_expr, _ in active:
        # where_sql is either "" or "WHERE ..."; merge with the IS NOT NULL guard
        if where_sql:
            where_clause = f"{where_sql} AND {col_expr} IS NOT NULL"
        else:
            where_clause = f"WHERE {col_expr} IS NOT NULL"
        sql = f"SELECT DISTINCT {col_expr}::text AS v {base} {where_clause} ORDER BY v"
        rows = db.execute(text(sql), params).mappings().all()
        result[label] = [r["v"] for r in rows if r["v"]]

    return result


def get_distinct_values_for_field(
    db: Session,
    *,
    query_id: str,
    field: str,
    site: Optional[str] = None,
    sector: Optional[str] = None,
    square: Optional[str] = None,
) -> list[str]:
    """Return DISTINCT values for a single layer field, filtered by parent selections.

    Hierarchy: Site -> Sector -> Square -> Layer
    Each level is filtered by the values selected above it.
    """
    if query_id == "q2":
        base = (
            "FROM tbllayers l "
            "INNER JOIN tblfragments f ON l.layerid = f.locationid "
            "INNER JOIN tblornaments o ON f.fragmentid = o.fragmentid"
        )
    elif query_id == "finds":
        base = (
            "FROM tblfinds fi "
            "INNER JOIN tbllayers l ON l.layerid = fi.layerid "
            "LEFT JOIN tblfragments f ON f.fragmentid = fi.fragmentid "
            "LEFT JOIN tblornaments o ON o.ornamentid = fi.ornamentid"
        )
    elif query_id == "finds_arch":
        base = "FROM finds fi LEFT JOIN tbllayers l ON l.layerid = fi.layerid"
    else:
        return []

    clauses: list[str] = []
    params: dict[str, Any] = {}

    if site:
        clauses.append("l.sector ILIKE :site")
        params["site"] = f"%{site}%"
    if sector:
        clauses.append("l.square ILIKE :sector")
        params["sector"] = f"%{sector}%"
    if square:
        clauses.append("l.layer ILIKE :square")
        params["square"] = f"%{square}%"

    col_map = {
        "Site": "l.sector",
        "Sector": "l.square",
        "Square": "l.layer",
        "Layer": "l.layer",
    }
    col_expr = col_map.get(field)
    if not col_expr:
        return []

    where = "WHERE " + " AND ".join(clauses) if clauses else "WHERE 1=1"
    sql = f"SELECT DISTINCT {col_expr}::text AS v {base} {where} AND {col_expr} IS NOT NULL ORDER BY v"
    rows = db.execute(text(sql), params).mappings().all()
    return [r["v"] for r in rows if r["v"]]


def get_layer_hierarchy(
    db: Session,
    *,
    query_id: str,
) -> dict[str, list[str]]:
    """Return the full site->sector->square->layer hierarchy as nested dicts.

    Returns:
        {
            "Site": {"A": {"Sector": ["S1", "S2"], ...}, ...},
            "Sector": {"S1": {"Square": ["Q1", "Q2"], ...}, ...},
            "Square": {"Q1": {"Layer": ["L1", "L2"], ...}, ...},
            "Layer": ["L1", "L2", ...],
            "all_sites": ["A", "B"],
            "all_sectors": ["S1", "S2"],
            "all_squares": ["Q1", "Q2"],
            "all_layers": ["L1", "L2"],
        }
    """
    if query_id == "q2":
        base = (
            "FROM tbllayers l "
            "INNER JOIN tblfragments f ON l.layerid = f.locationid "
            "INNER JOIN tblornaments o ON f.fragmentid = o.fragmentid"
        )
    elif query_id == "finds":
        base = (
            "FROM tblfinds fi "
            "INNER JOIN tbllayers l ON l.layerid = fi.layerid "
            "LEFT JOIN tblfragments f ON f.fragmentid = fi.fragmentid "
            "LEFT JOIN tblornaments o ON o.ornamentid = fi.ornamentid"
        )
    elif query_id == "finds_arch":
        base = "FROM finds fi LEFT JOIN tbllayers l ON l.layerid = fi.layerid"
    else:
        return {}

    # Fetch all combinations in one query
    if query_id == "finds_arch":
        id_col = "fi.findid"
    else:
        id_col = "l.layerid"
    sql = f"""
        SELECT DISTINCT l.site, l.sector, l.square, l.layer, {id_col}
        {base}
        WHERE l.sector IS NOT NULL AND l.square IS NOT NULL
          AND l.layer IS NOT NULL
        ORDER BY l.sector, l.square, l.layer
    """
    rows = db.execute(text(sql)).mappings().all()

    hierarchy: dict[str, Any] = {}
    all_sites: set[str] = set()
    all_sectors: set[str] = set()
    all_squares: set[str] = set()
    all_layers: set[str] = set()

    for r in rows:
        site = r.get("site")
        sector = r["sector"]
        square = r["square"]
        layer = r["layer"]
        if site:
            all_sites.add(site)
        all_sectors.add(sector)
        all_squares.add(square)
        all_layers.add(layer)

        if site:
            if site not in hierarchy:
                hierarchy[site] = {}
            if sector not in hierarchy[site]:
                hierarchy[site][sector] = {}
            if square not in hierarchy[site][sector]:
                hierarchy[site][sector][square] = set()
            hierarchy[site][sector][square].add(layer)

    # Convert sets to sorted lists
    for site in hierarchy:
        for sector in hierarchy[site]:
            hierarchy[site][sector] = dict(
                (sq, sorted(layers)) for sq, layers in hierarchy[site][sector].items()
            )

    return {
        "hierarchy": hierarchy,
        "all_sites": sorted(all_sites),
        "all_sectors": sorted(all_sectors),
        "all_squares": sorted(all_squares),
        "all_layers": sorted(all_layers),
    }


def query_finds_archaeology(
    db: Session,
    *,
    site: Optional[str] = None,
    sector: Optional[str] = None,
    square: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    q: Optional[str] = None,
    limit: int = 500,
    offset: int = 0,
    frag_filters: Optional[dict[str, Any]] = None,
    layer_filters: Optional[dict[str, Any]] = None,
) -> AnalyticsResult:
    """Archaeological finds: finds table with optional layer join."""
    select_cols = _model_select_list("fi_", "fi", Find) + _model_select_list(
        "l_", "l", Tbllayer
    )

    base = f"""
    SELECT
      {", ".join(select_cols)}
    FROM finds fi
    LEFT JOIN tbllayers l ON l.layerid = fi.layerid
    """

    where_sql, params = _build_where_finds(
        query_id="finds_arch",
        site=site,
        sector=sector,
        square=square,
        date_from=date_from,
        date_to=date_to,
        q=q,
        layer_filters=layer_filters,
        arch_filters=frag_filters,
    )

    sql = f"{base}\n{where_sql}\nORDER BY fi.findid DESC"
    count_sql = f"SELECT COUNT(*) FROM ({base}\n{where_sql}) x"

    rows = _run_sql(db, sql=sql, params=params, limit=limit, offset=offset)
    total = _count_sql(db, count_sql=count_sql, params=params)

    items = [dict(r) for r in rows]
    columns = (
        list(items[0].keys()) if items else [c.split(" AS ")[-1] for c in select_cols]
    )
    return AnalyticsResult(items=items, total=total, columns=columns)


def _build_where_finds(
    *,
    query_id: str,
    site: Optional[str],
    sector: Optional[str],
    square: Optional[str],
    date_from: Optional[date],
    date_to: Optional[date],
    q: Optional[str],
    layer_filters: Optional[dict[str, Any]] = None,
    arch_filters: Optional[dict[str, Any]] = None,
) -> tuple[str, dict[str, Any]]:
    """Build WHERE clause for the finds_arch query (finds table + layers)."""
    clauses: list[str] = []
    params: dict[str, Any] = {}

    if layer_filters:
        # For finds_arch, map layer filters to finds table columns
        label_to_col: dict[str, str] = {
            "Site": "fi.sector",
            "Sector": "fi.square",
            "Square": "fi.layer_mechanical",
            "Layer": "fi.context",
        }
        for label, values in layer_filters.items():
            col = label_to_col.get(label)
            if not col:
                continue
            col_expr = f"{col}::text"
            safe_label = label.replace(" ", "_")
            if isinstance(values, list) and values:
                param_name = f"layer_{safe_label}"
                params[param_name] = values
                conditions = " OR ".join(
                    [
                        f"{col_expr} ILIKE :{param_name}_{i}"
                        for i, v in enumerate(values)
                    ]
                )
                clauses.append(f"({conditions})")
                for i, v in enumerate(values):
                    params[f"{param_name}_{i}"] = f"%{v}%"
            elif isinstance(values, str) and values.strip():
                param_name = f"layer_{safe_label}"
                params[param_name] = f"%{values.strip()}%"
                clauses.append(f"{col_expr} ILIKE :{param_name}")
    else:
        if site:
            clauses.append("fi.sector ILIKE :site")
            params["site"] = f"%{site}%"
        if sector:
            clauses.append("fi.square ILIKE :sector")
            params["sector"] = f"%{sector}%"
        if square:
            clauses.append("fi.layer_mechanical ILIKE :square")
            params["square"] = f"%{square}%"

    if date_from:
        clauses.append("fi.date_found >= :date_from")
        params["date_from"] = date_from
    if date_to:
        clauses.append("fi.date_found <= :date_to")
        params["date_to"] = date_to

    if q:
        params["q"] = f"%{q}%"
        clauses.append(
            "(COALESCE(fi.description,'') ILIKE :q "
            "OR COALESCE(fi.find_type,'') ILIKE :q "
            "OR COALESCE(fi.material,'') ILIKE :q "
            "OR COALESCE(fi.inv_no::text,'') ILIKE :q)"
        )

    if arch_filters:
        _apply_arch_filters(clauses, params, arch_filters)

    if not clauses:
        return "", params
    return "WHERE " + " AND ".join(clauses), params
