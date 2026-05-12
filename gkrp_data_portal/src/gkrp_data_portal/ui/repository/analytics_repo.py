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
) -> None:
    """Apply fragment field filters from the UI dropdowns.

    Maps UI labels to SQL column references using the 'f' alias.
    Multi-select uses ANY/ILIKE; single text inputs use ILIKE.
    """
    label_to_col: dict[str, str] = {
        "Piecetype": "f.piecetype",
        "Technology": "f.technology",
        "Baking": "f.baking",
        "Color / Primary color": "f.primarycolor",
        "Covering": "f.covering",
        "Surface": "f.surface",
        "Wall thickness": "f.wallthickness",
        "Handle type": "f.handletype",
        "Handle size": "f.handlesize",
        "Bottom type": "f.bottomtype",
        "Category": "f.category",
        "Form": "f.form",
        "Type": "f.type",
        "Subtype": "f.subtype",
        "Variant": "f.variant",
        "Primary": "o.primary_",
        "Secondary": "o.secondary",
        "Tertiary": "o.tertiary",
        "Quarternary": "o.quarternary",
        "Color / color1": "o.color1",
        "Encrust color": "o.encrustcolor1",
    }
    for label, values in frag_filters.items():
        col = label_to_col.get(label)
        if not col:
            continue
        col_expr = f"{col}::text"
        if isinstance(values, list) and values:
            param_name = f"frag_{label}"
            params[param_name] = values
            conditions = " OR ".join(
                [f"{col_expr} ILIKE :{param_name}_{i}" for i, v in enumerate(values)]
            )
            clauses.append(f"({conditions})")
            for i, v in enumerate(values):
                params[f"{param_name}_{i}"] = f"%{v}%"
        elif isinstance(values, str) and values.strip():
            param_name = f"frag_{label}"
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
) -> tuple[str, dict[str, Any]]:
    """Build a safe WHERE clause using only whitelisted filters."""
    clauses: list[str] = []
    params: dict[str, Any] = {}

    # Layer-scoped filters (always safe; all queries include l alias)
    if site:
        clauses.append("l.site ILIKE :site")
        params["site"] = f"%{site}%"
    if sector:
        clauses.append("l.sector ILIKE :sector")
        params["sector"] = f"%{sector}%"
    if square:
        clauses.append("l.square ILIKE :square")
        params["square"] = f"%{square}%"

    if date_from:
        clauses.append("l.recordenteredon >= :date_from")
        params["date_from"] = date_from
    if date_to:
        clauses.append("l.recordenteredon <= :date_to")
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

    # Fragment field filters (only applied for q1/q2 which have f alias)
    if frag_filters and query_id in ("q1", "q2"):
        _apply_frag_filters(clauses, params, frag_filters)

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
) -> AnalyticsResult:
    """Filter #1: tbllayers INNER JOIN tblfragments."""
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
) -> AnalyticsResult:
    """Filter #2: tbllayers INNER JOIN tblfragments INNER JOIN tblornaments."""
    select_cols = (
        _model_select_list("l_", "l", Tbllayer)
        + _model_select_list("f_", "f", Tblfragment)
        + _model_select_list("o_", "o", Tblornament)
    )
    base = f"""
    SELECT
      {", ".join(select_cols)}
    FROM tbllayers l
    INNER JOIN tblfragments f ON l.layerid = f.locationid
    INNER JOIN tblornaments o ON f.fragmentid = o.fragmentid
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
    )

    sql = f"{base}\n{where_sql}\nORDER BY l.layerid DESC, f.fragmentid DESC, o.ornamentid DESC"
    count_sql = f"SELECT COALESCE(SUM(f_count), 0) FROM ({base}\n{where_sql}) x"

    rows = _run_sql(db, sql=sql, params=params, limit=limit, offset=offset)
    total = _count_sql(db, count_sql=count_sql, params=params)

    items = [dict(r) for r in rows]
    columns = (
        list(items[0].keys()) if items else [c.split(" AS ")[-1] for c in select_cols]
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
) -> AnalyticsResult:
    """Finds selector: tblfinds tied to layers/fragments/ornaments (left joins)."""
    select_cols = (
        _model_select_list("fi_", "fi", Tblfind)
        + _model_select_list("l_", "l", Tbllayer)
        + _model_select_list("f_", "f", Tblfragment)
        + _model_select_list("o_", "o", Tblornament)
    )

    base = f"""
    SELECT
      {", ".join(select_cols)}
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
    )

    sql = f"{base}\n{where_sql}\nORDER BY fi.findid DESC"
    count_sql = f"SELECT COALESCE(SUM(f_count), 0) FROM ({base}\n{where_sql}) x"

    rows = _run_sql(db, sql=sql, params=params, limit=limit, offset=offset)
    total = _count_sql(db, count_sql=count_sql, params=params)

    items = [dict(r) for r in rows]
    columns = (
        list(items[0].keys()) if items else [c.split(" AS ")[-1] for c in select_cols]
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
    ("Piecetype", "f.piecetype", ("q1", "q2")),
    ("Technology", "f.technology", ("q1", "q2")),
    ("Baking", "f.baking", ("q1", "q2")),
    ("Color / Primary color", "f.primarycolor", ("q1", "q2")),
    ("Covering", "f.covering", ("q1", "q2")),
    ("Surface", "f.surface", ("q1", "q2")),
    ("Wall thickness", "f.wallthickness", ("q1", "q2")),
    ("Handle type", "f.handletype", ("q1", "q2")),
    ("Handle size", "f.handlesize", ("q1", "q2")),
    ("Bottom type", "f.bottomtype", ("q1", "q2")),
    ("Category", "f.category", ("q1", "q2")),
    ("Form", "f.form", ("q1", "q2")),
    ("Type", "f.type", ("q1", "q2")),
    ("Subtype", "f.subtype", ("q1", "q2")),
    ("Variant", "f.variant", ("q1", "q2")),
    ("Note", "f.note", ("q1", "q2")),
    ("Inventory", "f.inventory", ("q1", "q2")),
    ("Primary", "o.primary_", ("q2",)),
    ("Secondary", "o.secondary", ("q2",)),
    ("Tertiary", "o.tertiary", ("q2",)),
    ("Quarternary", "o.quarternary", ("q2",)),
    ("Color / color1", "o.color1", ("q2",)),
    ("Encrust color", "o.encrustcolor1", ("q2",)),
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
    columns: Optional[set[str]] = None,
) -> dict[str, list[str]]:
    """Return DISTINCT values for filter dropdown columns via SQL.

    *columns* limits which columns are fetched; if None all applicable columns
    are returned.  The result is keyed by the UI label (e.g. ``"Piecetype"``).
    """
    # Determine which table aliases apply
    if query_id == "q1":
        base = "FROM tbllayers l INNER JOIN tblfragments f ON l.layerid = f.locationid"
    elif query_id == "q2":
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
    )

    # Build list of (label, col_expr) pairs
    if columns:
        active = [(lbl, expr, qids) for lbl, expr, qids in _DISTINCT_COL_DEFS
                  if lbl in columns and query_id in qids]
    else:
        active = [(lbl, expr, qids) for lbl, expr, qids in _DISTINCT_COL_DEFS
                  if query_id in qids]

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
