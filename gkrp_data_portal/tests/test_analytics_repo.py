"""Tests for gkrp_data_portal.ui.repository.analytics_repo."""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock

import pytest
from sqlalchemy import text


from gkrp_data_portal.ui.repository.analytics_repo import (
    CHART_COL_EXPR,
    ARCH_FILTER_COLS,
    _DISTINCT_COL_DEFS,
    FINDS_LOCATION_FILTER_COLS,
    FRAGMENT_FILTER_COLS,
    LAYER_FILTER_COLS,
    ORNAMENT_FILTER_COLS,
    AnalyticsResult,
    _apply_arch_filters,
    _apply_frag_filters,
    _apply_layer_filters,
    _build_where,
    _build_where_finds,
    get_groupby_columns,
    _model_select_list,
    build_chart_histogram,
    query_finds,
    query_q2_layers_fragments_ornaments,
)


class TestModelSelectList:
    def test_returns_prefixed_columns(self):
        from gkrp_data_portal.models.archaeology import Tbllayer

        result = _model_select_list("f_", "f", Tbllayer)
        assert isinstance(result, list)
        assert len(result) > 0
        for col in result:
            assert " AS f_" in col

    def test_uses_correct_alias(self):
        from gkrp_data_portal.models.archaeology import Tbllayer

        result = _model_select_list("o_", "o", Tbllayer)
        for col in result:
            assert " AS o_" in col


class TestBuildWhere:
    def test_returns_empty_with_no_filters(self):
        sql, params = _build_where(
            query_id="q2",
            site=None,
            sector=None,
            square=None,
            date_from=None,
            date_to=None,
            q=None,
        )
        assert sql == ""
        assert params == {}

    def test_filters_by_site(self):
        sql, params = _build_where(
            query_id="q2",
            site="Sofia",
            sector=None,
            square=None,
            date_from=None,
            date_to=None,
            q=None,
        )
        assert "l.site ILIKE :site" in sql
        assert params["site"] == "%Sofia%"

    def test_filters_by_sector(self):
        sql, params = _build_where(
            query_id="q2",
            site=None,
            sector="Alpha",
            square=None,
            date_from=None,
            date_to=None,
            q=None,
        )
        assert "l.sector ILIKE :sector" in sql

    def test_filters_by_square(self):
        sql, params = _build_where(
            query_id="q2",
            site=None,
            sector=None,
            square="B4",
            date_from=None,
            date_to=None,
            q=None,
        )
        assert "l.square ILIKE :square" in sql

    def test_filters_by_date_range(self):
        from_ = date(2024, 1, 1)
        to = date(2024, 12, 31)
        sql, params = _build_where(
            query_id="q2",
            site=None,
            sector=None,
            square=None,
            date_from=from_,
            date_to=to,
            q=None,
        )
        assert "l.recordenteredon >= :date_from" in sql
        assert "l.recordenteredon <= :date_to" in sql
        assert params["date_from"] == from_
        assert params["date_to"] == to

    def test_free_text_q2(self):
        sql, params = _build_where(
            query_id="q2",
            site=None,
            sector=None,
            square=None,
            date_from=None,
            date_to=None,
            q="decoration",
        )
        assert "COALESCE(f.inventory,'') ILIKE :q" in sql
        assert "COALESCE(f.note,'') ILIKE :q" in sql
        assert "COALESCE(f.piecetype::text,'') ILIKE :q" in sql

    def test_free_text_finds(self):
        sql, params = _build_where(
            query_id="finds",
            site=None,
            sector=None,
            square=None,
            date_from=None,
            date_to=None,
            q="metal",
        )
        assert "COALESCE(fi.description,'') ILIKE :q" in sql
        assert "COALESCE(fi.findtype,'') ILIKE :q" in sql
        assert "COALESCE(fi.inventory,'') ILIKE :q" in sql

    def test_combines_filters(self):
        from_ = date(2024, 1, 1)
        sql, params = _build_where(
            query_id="q2",
            site="Sofia",
            sector=None,
            square="A1",
            date_from=from_,
            date_to=None,
            q="pottery",
        )
        assert "l.site ILIKE :site" in sql
        assert "l.square ILIKE :square" in sql
        assert "l.recordenteredon >= :date_from" in sql
        assert "COALESCE(f.inventory,'') ILIKE :q" in sql
        assert " AND " in sql


class TestQueryQ2LayersFragmentsOrnaments:
    def test_returns_analytics_result(self):
        mock_db = MagicMock()
        mock_row = MagicMock()
        mock_row.mappings.return_value.all.return_value = []
        mock_db.execute.return_value = mock_row
        mock_row.scalar_one.return_value = 0

        result = query_q2_layers_fragments_ornaments(mock_db)
        assert isinstance(result, AnalyticsResult)

    def test_count_uses_deduped_fragment_count(self):
        mock_db = MagicMock()
        mock_row = MagicMock()
        mock_row.mappings.return_value.all.return_value = []
        mock_db.execute.return_value = mock_row
        mock_row.scalar_one.return_value = 0

        query_q2_layers_fragments_ornaments(mock_db)

        calls = mock_db.execute.call_args_list
        count_sql = str(calls[1][0][0])
        assert "SUM(f2.count)" in count_sql
        assert "DISTINCT f2.fragmentid" in count_sql
        assert "COUNT(*)" not in count_sql

    def test_includes_f_count_deduped_column(self):
        mock_db = MagicMock()
        mock_row = MagicMock()
        mock_row.mappings.return_value.all.return_value = []
        mock_db.execute.return_value = mock_row
        mock_row.scalar_one.return_value = 0

        query_q2_layers_fragments_ornaments(mock_db)

        calls = mock_db.execute.call_args_list
        data_sql = str(calls[0][0][0])
        assert "f_count_deduped" in data_sql


class TestQueryFinds:
    def test_returns_analytics_result(self):
        mock_db = MagicMock()
        mock_row = MagicMock()
        mock_row.mappings.return_value.all.return_value = []
        mock_db.execute.return_value = mock_row
        mock_row.scalar_one.return_value = 0

        result = query_finds(mock_db)
        assert isinstance(result, AnalyticsResult)

    def test_includes_find_columns(self):
        mock_db = MagicMock()
        mock_row = MagicMock()
        mock_row.mappings.return_value.all.return_value = []
        mock_db.execute.return_value = mock_row
        mock_row.scalar_one.return_value = 0

        query_finds(mock_db)
        call_str = str(mock_db.execute.call_args_list[0][0][0])
        assert "tblfinds" in call_str.lower()

    def test_count_uses_count_star(self):
        mock_db = MagicMock()
        mock_row = MagicMock()
        mock_row.mappings.return_value.all.return_value = []
        mock_db.execute.return_value = mock_row
        mock_row.scalar_one.return_value = 0

        query_finds(mock_db)

        calls = mock_db.execute.call_args_list
        count_sql = str(calls[1][0][0])
        assert "COUNT(*)" in count_sql
        assert "SUM(f2.count)" not in count_sql

    def test_no_f_count_deduped_column(self):
        mock_db = MagicMock()
        mock_row = MagicMock()
        mock_row.mappings.return_value.all.return_value = []
        mock_db.execute.return_value = mock_row
        mock_row.scalar_one.return_value = 0

        query_finds(mock_db)

        calls = mock_db.execute.call_args_list
        data_sql = str(calls[0][0][0])
        assert "f_count_deduped" not in data_sql


class TestBuildChartHistogram:
    def test_returns_empty_for_unknown_query_id(self):
        mock_db = MagicMock()
        result = build_chart_histogram(mock_db, query_id="nonexistent", x_key="l_site")
        assert result == []

    def test_returns_empty_for_unknown_x_key(self):
        mock_db = MagicMock()
        result = build_chart_histogram(mock_db, query_id="q2", x_key="unknown_col")
        assert result == []

    def test_q2_single_axis_returns_buckets(self):
        mock_db = MagicMock()
        mock_row = MagicMock()
        mock_row.mappings.return_value.all.return_value = [
            {"bucket": "Sofia", "cnt": 150},
            {"bucket": "Plovdiv", "cnt": 80},
            {"bucket": "Varna", "cnt": 45},
        ]
        mock_db.execute.return_value = mock_row

        result = build_chart_histogram(mock_db, query_id="q2", x_key="l_site", top_n=30)
        assert len(result) == 3
        assert result[0]["bucket"] == "Sofia"
        assert result[0]["count"] == 150
        assert result[1]["bucket"] == "Plovdiv"
        assert result[1]["count"] == 80

    def test_q2_series_returns_pivoted_data(self):
        mock_db = MagicMock()
        mock_row = MagicMock()
        mock_row.mappings.return_value.all.return_value = [
            {"x_bucket": "Sofia", "series_bucket": "Body", "cnt": 100},
            {"x_bucket": "Sofia", "series_bucket": "Rim", "cnt": 50},
            {"x_bucket": "Plovdiv", "series_bucket": "Body", "cnt": 30},
        ]
        mock_db.execute.return_value = mock_row

        result = build_chart_histogram(
            mock_db, query_id="q2", x_key="l_site", series_key="f_piecetype", top_n=30
        )
        # Should return one row per (x_bucket, series_bucket) combo for top-N x_buckets
        assert len(result) == 3
        buckets = {r["x_bucket"] for r in result}
        assert "Sofia" in buckets
        assert "Plovdiv" in buckets

    def test_finds_arch_counts_rows(self):
        mock_db = MagicMock()
        mock_row = MagicMock()
        mock_row.mappings.return_value.all.return_value = [
            {"bucket": "Metal", "cnt": 25},
            {"bucket": "Glass", "cnt": 12},
        ]
        mock_db.execute.return_value = mock_row

        result = build_chart_histogram(
            mock_db, query_id="finds_arch", x_key="fi_find_type", top_n=30
        )
        assert len(result) == 2
        assert result[0]["bucket"] == "Metal"
        assert result[0]["count"] == 25

    def test_finds_counts_rows(self):
        mock_db = MagicMock()
        mock_row = MagicMock()
        mock_row.mappings.return_value.all.return_value = [
            {"bucket": "Sofia", "cnt": 10},
        ]
        mock_db.execute.return_value = mock_row

        result = build_chart_histogram(
            mock_db, query_id="finds", x_key="l_site", top_n=30
        )
        assert len(result) == 1
        assert result[0]["bucket"] == "Sofia"
        assert result[0]["count"] == 10

    def test_applies_site_filter(self):
        mock_db = MagicMock()
        mock_row = MagicMock()
        mock_row.mappings.return_value.all.return_value = [
            {"bucket": "TypeA", "cnt": 5},
        ]
        mock_db.execute.return_value = mock_row

        build_chart_histogram(
            mock_db, query_id="q2", x_key="f_piecetype", site="Sofia", top_n=30
        )

        calls = mock_db.execute.call_args_list
        sql = str(calls[0][0][0])
        params = calls[0][0][1]
        assert "site ILIKE" in sql
        assert params["site"] == "%Sofia%"

    def test_applies_frag_filter(self):
        mock_db = MagicMock()
        mock_row = MagicMock()
        mock_row.mappings.return_value.all.return_value = [{"bucket": "X", "cnt": 1}]
        mock_db.execute.return_value = mock_row

        build_chart_histogram(
            mock_db,
            query_id="q2",
            x_key="l_site",
            frag_filters={"Piecetype": ["Body"]},
            top_n=30,
        )

        calls = mock_db.execute.call_args_list
        sql = str(calls[0][0][0])
        params = calls[0][0][1]
        assert "piecetype::text ILIKE" in sql
        assert params["frag_piecetype_0"] == "%Body%"


def _chart_where_and_params(**kwargs):
    """Run build_chart_histogram against a mock db; return (WHERE text, params)."""
    db = MagicMock()
    db.execute.return_value.mappings.return_value.all.return_value = []
    build_chart_histogram(db, **kwargs)
    sql = str(db.execute.call_args[0][0])
    where = sql.split(") sub", 1)[1].split("GROUP BY")[0]
    return " ".join(where.split()), db.execute.call_args[0][1]


class TestFilterSqlPins:
    """Pin the exact SQL/params emitted by the ILIKE filter builders."""

    def test_frag_filters(self):
        clauses: list[str] = []
        params: dict = {}
        _apply_frag_filters(
            clauses,
            params,
            {
                "Piecetype": ["A", "B"],
                "Primary": "  x ",
                "Encrust color": [],
                "Technology": None,
            },
            "f2",
            "o2",
        )
        assert clauses == [
            "(f2.piecetype::text ILIKE :frag_piecetype_0 OR f2.piecetype::text ILIKE :frag_piecetype_1)",
            "o2.primary_::text ILIKE :frag_primary_",
        ]
        assert params == {
            "frag_piecetype_0": "%A%",
            "frag_piecetype_1": "%B%",
            "frag_primary_": "%x%",
        }

    def test_layer_filters(self):
        clauses: list[str] = []
        params: dict = {}
        _apply_layer_filters(
            clauses, params, {"Site": ["S"], "Layer": " L1 ", "Square": None}, "l2"
        )
        assert clauses == [
            "(l2.site::text ILIKE :layer_site_0)",
            "l2.layer::text ILIKE :layer_layer",
        ]
        assert params == {
            "layer_site_0": "%S%",
            "layer_layer": "%L1%",
        }

    def test_arch_filters(self):
        clauses: list[str] = []
        params: dict = {}
        _apply_arch_filters(clauses, params, {"Find Type": ["coin"], "Depth": "1.2"})
        assert clauses == [
            "(fi.find_type::text ILIKE :arch_find_type_0)",
            "fi.depth_m::text ILIKE :arch_depth_m",
        ]
        assert params == {
            "arch_find_type_0": "%coin%",
            "arch_depth_m": "%1.2%",
        }

    def test_build_where_finds(self):
        sql, params = _build_where_finds(
            query_id="finds_arch",
            site=None,
            sector=None,
            square=None,
            date_from=None,
            date_to=None,
            q=None,
            layer_filters={"Sector": ["A"], "Layer": ["m1", "m2"]},
            arch_filters={"Material": ["Fe"]},
        )
        assert sql == (
            "WHERE (fi.sector::text ILIKE :layer_sector_0) AND "
            "(fi.layer_mechanical::text ILIKE :layer_layer_mechanical_0 OR "
            "fi.layer_mechanical::text ILIKE :layer_layer_mechanical_1) AND "
            "(fi.material::text ILIKE :arch_material_0)"
        )
        assert params == {
            "layer_sector_0": "%A%",
            "layer_layer_mechanical_0": "%m1%",
            "layer_layer_mechanical_1": "%m2%",
            "arch_material_0": "%Fe%",
        }

    def test_chart_histogram_q2_where(self):
        where, params = _chart_where_and_params(
            query_id="q2",
            x_key="l_site",
            layer_filters={"Site": ["S"], "Layer": "L"},
            frag_filters={"Piecetype": ["A", "B"], "Primary": ["p"]},
        )
        assert where == (
            "WHERE (site::text ILIKE :layer_site_0) AND layer::text ILIKE :layer_layer "
            "AND (piecetype::text ILIKE :frag_piecetype_0 OR "
            "piecetype::text ILIKE :frag_piecetype_1) AND "
            "(primary_::text ILIKE :frag_primary__0)"
        )
        assert params == {
            "layer_site_0": "%S%",
            "layer_layer": "%L%",
            "frag_piecetype_0": "%A%",
            "frag_piecetype_1": "%B%",
            "frag_primary__0": "%p%",
        }

    def test_chart_histogram_finds_arch_where(self):
        where, params = _chart_where_and_params(
            query_id="finds_arch",
            x_key="fi_material",
            layer_filters={"Sector": ["A"], "Layer": ["m"]},
            frag_filters={"Find Type": ["coin"]},
        )
        assert where == (
            "WHERE (sector::text ILIKE :layer_sector_0) AND "
            "(layer_mechanical::text ILIKE :layer_layer_mechanical_0) AND "
            "(find_type::text ILIKE :arch_find_type_0)"
        )
        assert params == {
            "layer_sector_0": "%A%",
            "layer_layer_mechanical_0": "%m%",
            "arch_find_type_0": "%coin%",
        }

    def test_chart_histogram_finds_where(self):
        where, params = _chart_where_and_params(
            query_id="finds", x_key="l_site", layer_filters={"Square": ["Q"]}
        )
        assert where == "WHERE (square::text ILIKE :layer_square_0)"
        assert params == {"layer_square_0": "%Q%"}

    def test_distinct_col_defs(self):
        assert _DISTINCT_COL_DEFS == [
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
            ("Find Type", "fi.find_type", ("finds_arch",)),
            ("Material", "fi.material", ("finds_arch",)),
            ("Coin", "fi.coin", ("finds_arch",)),
            ("Denomination", "fi.denomination", ("finds_arch",)),
            ("Mint", "fi.mint", ("finds_arch",)),
            ("Year", "fi.year", ("finds_arch",)),
            ("Inv No", "fi.inv_no", ("finds_arch",)),
            ("Depth", "fi.depth_m", ("finds_arch",)),
            ("Context", "fi.context", ("finds_arch",)),
            ("Sector", "fi.sector", ("finds_arch",)),
            ("Square", "fi.square", ("finds_arch",)),
            ("Layer", "fi.layer_mechanical", ("finds_arch",)),
        ]

    def test_chart_col_expr(self):
        assert CHART_COL_EXPR == {
            "l_site": "l.site",
            "l_sector": "l.sector",
            "l_square": "l.square",
            "l_layer": "l.layer",
            "f_piecetype": "f.piecetype",
            "f_technology": "f.technology",
            "f_baking": "f.baking",
            "f_primarycolor": "f.primarycolor",
            "f_covering": "f.covering",
            "f_surface": "f.surface",
            "f_wallthickness": "f.wallthickness",
            "f_handletype": "f.handletype",
            "f_handlesize": "f.handlesize",
            "f_bottomtype": "f.bottomtype",
            "f_category": "f.category",
            "f_form": "f.form",
            "f_type": "f.type",
            "f_subtype": "f.subtype",
            "f_variant": "f.variant",
            "f_note": "f.note",
            "f_inventory": "f.inventory",
            "o_primary_": "o.primary_",
            "o_secondary": "o.secondary",
            "o_tertiary": "o.tertiary",
            "o_quarternary": "o.quarternary",
            "o_color1": "o.color1",
            "o_encrustcolor1": "o.encrustcolor1",
            "fi_find_type": "fi.find_type",
            "fi_material": "fi.material",
            "fi_coin": "fi.coin",
            "fi_denomination": "fi.denomination",
            "fi_mint": "fi.mint",
            "fi_year": "fi.year",
            "fi_inv_no": "fi.inv_no",
            "fi_depth_m": "fi.depth_m",
            "fi_context": "fi.context",
            "fi_sector": "fi.sector",
            "fi_square": "fi.square",
            "fi_layer_mechanical": "fi.layer_mechanical",
        }

    def test_groupby_columns_q2(self):
        assert get_groupby_columns("q2") == [
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
            "f_note",
            "f_inventory",
            "o_primary_",
            "o_secondary",
            "o_tertiary",
            "o_quarternary",
            "o_color1",
            "o_encrustcolor1",
        ]

    def test_groupby_columns_finds(self):
        assert get_groupby_columns("finds") == [
            "l_site",
            "l_sector",
            "l_square",
            "l_layer",
        ]

    def test_groupby_columns_finds_arch(self):
        assert get_groupby_columns("finds_arch") == [
            "fi_find_type",
            "fi_material",
            "fi_coin",
            "fi_denomination",
            "fi_mint",
            "fi_year",
            "fi_inv_no",
            "fi_depth_m",
            "fi_context",
            "fi_sector",
            "fi_square",
            "fi_layer_mechanical",
        ]


def _assert_binds_supplied(sql: str, params: dict) -> None:
    """Every :bind referenced by *sql* must be present in *params*."""
    assert set(text(sql)._bindparams) <= set(params)


def _chart_sql_and_params(**kwargs):
    db = MagicMock()
    db.execute.return_value.mappings.return_value.all.return_value = []
    build_chart_histogram(db, **kwargs)
    return str(db.execute.call_args[0][0]), db.execute.call_args[0][1]


_FRAG_AND_ORN_LABELS = [*FRAGMENT_FILTER_COLS, *ORNAMENT_FILTER_COLS]
_NO_DATES = dict(
    site=None, sector=None, square=None, date_from=None, date_to=None, q=None
)


class TestFilterBindCompleteness:
    """Every label of every canonical filter map yields fully bound SQL."""

    @pytest.mark.parametrize("label", list(LAYER_FILTER_COLS))
    def test_layer_labels_q2(self, label):
        where, params = _build_where(
            query_id="q2", layer_filters={label: ["x", "y"]}, **_NO_DATES
        )
        _assert_binds_supplied(where, params)

    @pytest.mark.parametrize("label", _FRAG_AND_ORN_LABELS)
    def test_fragment_and_ornament_labels_q2(self, label):
        where, params = _build_where(
            query_id="q2", frag_filters={label: ["x", "y"]}, **_NO_DATES
        )
        assert "ILIKE" in where
        _assert_binds_supplied(where, params)

    @pytest.mark.parametrize("label", list(ARCH_FILTER_COLS))
    def test_arch_labels_finds_arch(self, label):
        where, params = _build_where(
            query_id="finds_arch", frag_filters={label: ["x", "y"]}, **_NO_DATES
        )
        assert "ILIKE" in where
        _assert_binds_supplied(where, params)

    @pytest.mark.parametrize("label", list(FINDS_LOCATION_FILTER_COLS))
    def test_location_labels_build_where_finds(self, label):
        where, params = _build_where_finds(
            query_id="finds_arch", layer_filters={label: ["x", "y"]}, **_NO_DATES
        )
        _assert_binds_supplied(where, params)

    @pytest.mark.parametrize("label", list(ARCH_FILTER_COLS))
    def test_arch_labels_build_where_finds(self, label):
        where, params = _build_where_finds(
            query_id="finds_arch", arch_filters={label: ["x", "y"]}, **_NO_DATES
        )
        _assert_binds_supplied(where, params)

    @pytest.mark.parametrize("label", list(LAYER_FILTER_COLS))
    @pytest.mark.parametrize("query_id", ["q2", "finds"])
    def test_chart_layer_labels(self, query_id, label):
        sql, params = _chart_sql_and_params(
            query_id=query_id, x_key="l_site", layer_filters={label: ["x", "y"]}
        )
        _assert_binds_supplied(sql, params)

    @pytest.mark.parametrize("label", list(FINDS_LOCATION_FILTER_COLS))
    def test_chart_location_labels_finds_arch(self, label):
        sql, params = _chart_sql_and_params(
            query_id="finds_arch",
            x_key="fi_material",
            layer_filters={label: ["x", "y"]},
        )
        _assert_binds_supplied(sql, params)

    @pytest.mark.parametrize("label", _FRAG_AND_ORN_LABELS)
    def test_chart_fragment_and_ornament_labels(self, label):
        sql, params = _chart_sql_and_params(
            query_id="q2", x_key="l_site", frag_filters={label: ["x", "y"]}
        )
        assert "ILIKE" in sql
        _assert_binds_supplied(sql, params)

    @pytest.mark.parametrize("label", list(ARCH_FILTER_COLS))
    def test_chart_arch_labels(self, label):
        sql, params = _chart_sql_and_params(
            query_id="finds_arch", x_key="fi_material", frag_filters={label: ["x", "y"]}
        )
        assert "ILIKE" in sql
        _assert_binds_supplied(sql, params)


class TestFilterBuilderInvariants:
    def test_unknown_label_raises(self):
        with pytest.raises(KeyError):
            _apply_layer_filters([], {}, {"Bogus": ["x"]})

    @pytest.mark.parametrize(
        "cols",
        [
            LAYER_FILTER_COLS,
            FINDS_LOCATION_FILTER_COLS,
            ARCH_FILTER_COLS,
            {**FRAGMENT_FILTER_COLS, **ORNAMENT_FILTER_COLS},
        ],
    )
    def test_column_names_unique_within_map(self, cols):
        assert len(set(cols.values())) == len(cols)

    def test_chart_ornament_primary_uses_projected_column(self):
        sql, _ = _chart_sql_and_params(query_id="q2", x_key="o_primary_")
        assert "GROUP BY primary_" in sql
        assert "o.primary_," in sql
        assert "AS o_primary" not in sql
