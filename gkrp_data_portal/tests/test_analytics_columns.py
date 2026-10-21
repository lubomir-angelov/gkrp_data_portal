"""Fitness tests: UI column tables must only reference real result columns."""

from __future__ import annotations

import pytest

from gkrp_data_portal.models.archaeology import (
    Find,
    Tblfind,
    Tblfragment,
    Tbllayer,
    Tblornament,
)
from gkrp_data_portal.ui.pages import analytics_chart_finds as finds_page
from gkrp_data_portal.ui.pages import analytics_chart_fragments as fragments_page
from gkrp_data_portal.ui.pages.analytics_chart_finds import ARCH_LABELS_NOT_SHOWN
from gkrp_data_portal.ui.pages.analytics_common import (
    _COLUMN_LABEL_KEYS,
    LOCALE,
    _UI_HIDDEN_COLUMNS,
    QUERY_OPTIONS,
)
from gkrp_data_portal.ui.pages.analytics_table import _SORT_DIR
from gkrp_data_portal.ui.repository.analytics_repo import (
    _CHART_SUBQUERIES,
    _DISTINCT_COL_DEFS,
    ARCH_FILTER_COLS,
    CHART_COL_EXPR,
    get_groupby_columns,
)


def _prefixed(prefix: str, model) -> set[str]:
    return {f"{prefix}{c.name}" for c in model.__table__.columns}


# Result columns of each query selectable in the table page.
_TABLE_QUERY_COLUMNS: dict[str, set[str]] = {
    "q2": (
        _prefixed("l_", Tbllayer)
        | _prefixed("f_", Tblfragment)
        | _prefixed("o_", Tblornament)
        | {"f_count_deduped"}
    ),
    "finds_arch": _prefixed("fi_", Find),
}
# Every column any analytics query (incl. the tblfinds chart/DISTINCT paths) can emit.
_ALL_RESULT_COLUMNS = set().union(*_TABLE_QUERY_COLUMNS.values()) | _prefixed(
    "fi_", Tblfind
)


def _visible(columns: set[str]) -> set[str]:
    return {c for c in columns if c.lower() not in _UI_HIDDEN_COLUMNS}


def test_table_queries_covered():
    assert set(QUERY_OPTIONS.values()) == set(_TABLE_QUERY_COLUMNS)


def test_hidden_columns_are_real_result_columns():
    assert _UI_HIDDEN_COLUMNS <= _ALL_RESULT_COLUMNS


def test_sort_dir_keys_are_visible_table_columns():
    visible_any = set().union(*(_visible(c) for c in _TABLE_QUERY_COLUMNS.values()))
    assert set(_SORT_DIR) <= visible_any


@pytest.mark.parametrize("query_id", sorted(_TABLE_QUERY_COLUMNS))
def test_every_table_query_has_visible_columns(query_id):
    assert _visible(_TABLE_QUERY_COLUMNS[query_id])


def test_groupby_exclude_members_are_offered_options():
    assert fragments_page._GROUPBY_EXCLUDE <= set(get_groupby_columns("q2"))
    assert finds_page._GROUPBY_EXCLUDE <= set(get_groupby_columns("finds_arch"))


def test_default_x_is_an_option():
    assert fragments_page.DEFAULT_X in fragments_page.GROUPBY_OPTIONS
    assert finds_page.DEFAULT_X in finds_page.GROUPBY_OPTIONS


def test_finds_groupby_options_pinned():
    assert finds_page.GROUPBY_OPTIONS == [
        "fi_find_type",
        "fi_material",
        "fi_coin",
        "fi_denomination",
        "fi_mint",
        "fi_year",
        "fi_depth_m",
        "fi_context",
        "fi_sector",
        "fi_square",
        "fi_layer_mechanical",
    ]


def test_groupby_dropdown_options_pinned():
    assert fragments_page.GROUPBY_OPTIONS == [
        "l_site",
        "l_sector",
        "l_square",
        "l_layer",
        "f_piecetype",
        "f_technology",
        "f_baking",
        "f_primarycolor",
        "f_covering",
        "f_surface",
        "f_wallthickness",
        "f_handletype",
        "f_handlesize",
        "f_bottomtype",
        "f_category",
        "f_form",
        "f_type",
        "f_subtype",
        "f_variant",
        "o_primary_",
        "o_secondary",
        "o_tertiary",
        "o_quarternary",
    ]


def _projected_names(subquery_sql: str) -> set[str]:
    select_list = subquery_sql.split("SELECT", 1)[1].split("FROM ", 1)[0]
    names = set()
    for item in select_list.split(","):
        item = item.strip()
        names.add(
            item.rsplit(" AS ", 1)[1].strip()
            if " AS " in item
            else item.rsplit(".", 1)[-1].strip()
        )
    return names


def test_chart_subquery_ids_match_query_options():
    assert set(_CHART_SUBQUERIES) == set(QUERY_OPTIONS.values())
    assert set(_CHART_SUBQUERIES) <= set(CHART_COL_EXPR)


@pytest.mark.parametrize("query_id", sorted(_CHART_SUBQUERIES))
def test_chart_subqueries_project_every_mapped_column(query_id):
    projected = _projected_names(_CHART_SUBQUERIES[query_id])
    missing = {
        expr
        for _label, expr, qids in _DISTINCT_COL_DEFS
        if query_id in qids and expr.split(".", 1)[1] not in projected
    }
    assert not missing


def test_q2_chart_subquery_projects_fragment_identity_and_count():
    projected = _projected_names(_CHART_SUBQUERIES["q2"])
    assert {"fragmentid", "frag_count"} <= projected


def test_label_keys_equal_reachable_chart_columns():
    reachable = set(fragments_page.GROUPBY_OPTIONS) | set(finds_page.GROUPBY_OPTIONS)
    assert set(_COLUMN_LABEL_KEYS) == reachable


def test_label_keys_exist_in_locale_both_languages():
    for key in set(_COLUMN_LABEL_KEYS.values()):
        assert key in LOCALE and f"{key}_en" in LOCALE


def test_finds_page_hidden_arch_labels_are_real():
    assert ARCH_LABELS_NOT_SHOWN <= ARCH_FILTER_COLS.keys()
