"""Tests for gkrp_data_portal.ui.pages.analytics_common."""

from __future__ import annotations

from datetime import date


from gkrp_data_portal.ui.pages.analytics_common import (
    QUERY_OPTIONS,
    build_histogram,
    build_histogram_series,
    is_ui_hidden_column,
    norm_bucket,
    parse_date,
    plotly_bar,
    plotly_grouped_bar,
    ui_columns,
)


class TestQueryOptions:
    def test_contains_expected_queries(self):
        assert "q2" in QUERY_OPTIONS.values()
        assert "finds" in QUERY_OPTIONS.values()

    def test_values_are_strings(self):
        for k, v in QUERY_OPTIONS.items():
            assert isinstance(k, str)
            assert isinstance(v, str)


class TestIsUiHiddenColumn:
    def test_hides_recordenteredon(self):
        assert is_ui_hidden_column("l_recordenteredon") is True

    def test_hides_fragmentid(self):
        assert is_ui_hidden_column("f_fragmentid") is True

    def test_not_hidden_unknown(self):
        assert is_ui_hidden_column("l_site") is False

    def test_case_insensitive(self):
        assert is_ui_hidden_column("L_RECORDENTEREDON") is True

    def test_handles_none(self):
        assert is_ui_hidden_column(None) is False

    def test_handles_empty_string(self):
        assert is_ui_hidden_column("") is False

    def test_handles_whitespace(self):
        assert is_ui_hidden_column("  ") is False

    def test_hides_f_count(self):
        assert is_ui_hidden_column("f_count") is True


class TestUiColumns:
    def test_filters_hidden_columns(self):
        columns = ["l_site", "l_recordenteredon", "f_inventory", "l_layerid"]
        result = ui_columns(columns)
        assert "l_site" in result
        assert "f_inventory" in result
        assert "l_recordenteredon" not in result
        assert "l_layerid" not in result

    def test_preserves_original_casing(self):
        columns = ["L_Site", "f_Inventory"]
        result = ui_columns(columns)
        assert "L_Site" in result
        assert "f_Inventory" in result

    def test_returns_empty_for_all_hidden(self):
        columns = ["l_recordenteredon", "l_layerid"]
        assert ui_columns(columns) == []


class TestParseDate:
    def test_parses_valid_date(self):
        result = parse_date("2024-01-15")
        assert result == date(2024, 1, 15)

    def test_returns_none_for_empty_string(self):
        assert parse_date("") is None

    def test_returns_none_for_none(self):
        assert parse_date(None) is None

    def test_returns_none_for_invalid_date(self):
        assert parse_date("not-a-date") is None

    def test_returns_none_for_malformed(self):
        assert parse_date("2024/01/15") is None


class TestNormBucket:
    def test_returns_null_for_none(self):
        assert norm_bucket(None) == "(null)"

    def test_strips_whitespace(self):
        assert norm_bucket("  value  ") == "value"

    def test_returns_null_for_empty_string(self):
        assert norm_bucket("") == "(null)"

    def test_returns_string_as_is(self):
        assert norm_bucket("hello") == "hello"

    def test_converts_int_to_string(self):
        assert norm_bucket(42) == "42"


class TestBuildHistogram:
    def test_returns_empty_for_no_rows(self):
        xs, ys = build_histogram([], "col")
        assert xs == []
        assert ys == []

    def test_returns_empty_for_no_key(self):
        xs, ys = build_histogram([{"other": "v"}], "col")
        # When key is missing, r.get("col") returns None, which norm_bucket converts to "(null)"
        # f_count is absent so the sum defaults to 0
        assert xs == ["(null)"]
        assert ys == [0]

    def test_builds_top_n(self):
        rows = [
            {"color": "бял", "f_count": 3},
            {"color": "бял", "f_count": 5},
            {"color": "бял", "f_count": 2},
            {"color": "червен", "f_count": 2},
            {"color": "червен", "f_count": 4},
            {"color": "жълт", "f_count": 1},
        ]
        xs, ys = build_histogram(rows, "color", top_n=3)
        assert xs == ["бял", "червен", "жълт"]
        assert ys == [10, 6, 1]

    def test_nulls_counted(self):
        rows = [
            {"color": None, "f_count": 3},
            {"color": None, "f_count": 5},
            {"color": "бял", "f_count": 2},
        ]
        xs, ys = build_histogram(rows, "color")
        assert "(null)" in xs
        assert ys[xs.index("(null)")] == 8

    def test_fragment_cols_sum_f_count(self):
        rows = [
            {"f_piecetype": "бял", "f_count": 3},
            {"f_piecetype": "бял", "f_count": 5},
            {"f_piecetype": "червен", "f_count": 2},
        ]
        xs, ys = build_histogram(rows, "f_piecetype")
        assert xs == ["бял", "червен"]
        assert ys == [8, 2]

    def test_fragment_cols_sum_f_count_category(self):
        rows = [
            {"f_category": "A", "f_count": 10},
            {"f_category": "B", "f_count": 4},
            {"f_category": "A", "f_count": 6},
        ]
        xs, ys = build_histogram(rows, "f_category")
        assert xs == ["A", "B"]
        assert ys == [16, 4]

    def test_non_fragment_cols_sum_f_count(self):
        rows = [
            {"f_piecetype": "бял", "f_count": 3},
            {"f_piecetype": "бял", "f_count": 5},
            {"f_piecetype": "червен", "f_count": 2},
        ]
        # all columns sum f_count now
        xs, ys = build_histogram(rows, "f_piecetype")
        assert ys == [8, 2]
        # l_site also sums f_count (not row count)
        rows2 = [
            {"l_site": "S1", "f_piecetype": "бял", "f_count": 3},
            {"l_site": "S1", "f_piecetype": "бял", "f_count": 5},
            {"l_site": "S2", "f_piecetype": "червен", "f_count": 2},
        ]
        xs2, ys2 = build_histogram(rows2, "l_site")
        assert xs2 == ["S1", "S2"]
        assert ys2 == [8, 2]

    def test_fragment_cols_without_f_count_count_rows(self):
        rows = [
            {"f_piecetype": "бял", "other": 3},
            {"f_piecetype": "бял", "other": 5},
            {"f_piecetype": "червен", "other": 2},
        ]
        # No f_count column present → defaults to 0 for each bucket
        xs, ys = build_histogram(rows, "f_piecetype")
        assert xs == ["бял", "червен"]
        assert ys == [0, 0]


class TestPlotlyBar:
    def test_returns_expected_structure(self):
        result = plotly_bar(["a", "b"], [1, 2], "Test Title")
        assert "data" in result
        assert "layout" in result
        assert len(result["data"]) == 1
        assert result["data"][0]["type"] == "bar"
        assert result["data"][0]["x"] == ["a", "b"]
        assert result["data"][0]["y"] == [1, 2]
        assert result["layout"]["title"]["text"] == "Test Title"


class TestBuildHistogramSeries:
    def test_returns_empty_for_no_rows(self):
        xs, series_data = build_histogram_series([], "col", "series")
        assert xs == []
        assert series_data == {}

    def test_returns_empty_for_no_x_key(self):
        xs, series_data = build_histogram_series([{"series": "A"}], "", "series")
        assert xs == []
        assert series_data == {}

    def test_returns_empty_for_no_series_key(self):
        xs, series_data = build_histogram_series([{"col": "A"}], "col", "")
        assert xs == []
        assert series_data == {}

    def test_groups_by_series(self):
        rows = [
            {"col": "A", "series": "X", "f_count": 3},
            {"col": "A", "series": "Y", "f_count": 5},
            {"col": "B", "series": "X", "f_count": 2},
            {"col": "B", "series": "Y", "f_count": 4},
        ]
        xs, series_data = build_histogram_series(rows, "col", "series", top_n=10)
        assert xs == ["A", "B"]
        assert "X" in series_data
        assert "Y" in series_data
        assert series_data["X"] == [3, 2]
        assert series_data["Y"] == [5, 4]

    def test_pads_missing_series_values(self):
        rows = [
            {"col": "A", "series": "X", "f_count": 10},
            {"col": "B", "series": "Y", "f_count": 5},
            {"col": "C", "series": "X", "f_count": 3},
        ]
        xs, series_data = build_histogram_series(rows, "col", "series", top_n=10)
        assert xs == ["A", "B", "C"]
        assert "X" in series_data
        assert "Y" in series_data
        assert series_data["X"] == [10, 0, 3]
        assert series_data["Y"] == [0, 5, 0]

    def test_respects_top_n(self):
        rows = [
            {"col": "A", "series": "X", "f_count": 100},
            {"col": "B", "series": "X", "f_count": 80},
            {"col": "C", "series": "X", "f_count": 60},
            {"col": "D", "series": "X", "f_count": 40},
        ]
        xs, series_data = build_histogram_series(rows, "col", "series", top_n=2)
        assert xs == ["A", "B"]
        assert series_data["X"] == [100, 80]

    def test_null_series_values(self):
        rows = [
            {"col": "A", "series": None, "f_count": 3},
            {"col": "A", "series": "X", "f_count": 5},
        ]
        xs, series_data = build_histogram_series(rows, "col", "series")
        assert "(null)" in series_data
        assert "X" in series_data
        assert xs == ["A"]

    def test_multiple_rows_same_bucket_series(self):
        rows = [
            {"col": "A", "series": "X", "f_count": 3},
            {"col": "A", "series": "X", "f_count": 7},
            {"col": "A", "series": "Y", "f_count": 2},
        ]
        xs, series_data = build_histogram_series(rows, "col", "series", top_n=10)
        assert xs == ["A"]
        assert series_data["X"] == [10]
        assert series_data["Y"] == [2]

    def test_column_to_label_mapping(self):
        from gkrp_data_portal.ui.pages.analytics_common import _column_to_label

        assert _column_to_label("f_technology") == "Technology"
        assert _column_to_label("f_piecetype") == "Piecetype"
        assert _column_to_label("f_surface") == "Surface"
        assert _column_to_label("o_primary") == "Ornament primary"
        assert _column_to_label("l_site") == "Site"
        assert _column_to_label("unknown_col") == "unknown_col"


class TestPlotlyGroupedBar:
    def test_returns_expected_structure(self):
        series_data = {
            "Tech 1": [10, 20, 30],
            "Tech 2": [5, 10, 15],
        }
        result = plotly_grouped_bar(["A", "B", "C"], series_data, "Test Title")
        assert "data" in result
        assert "layout" in result
        assert len(result["data"]) == 2
        assert result["data"][0]["type"] == "bar"
        assert result["data"][0]["name"] == "Tech 1"
        assert result["data"][0]["x"] == ["A", "B", "C"]
        assert result["data"][0]["y"] == [10, 20, 30]
        assert result["data"][1]["name"] == "Tech 2"
        assert result["data"][1]["y"] == [5, 10, 15]
        assert result["layout"]["title"]["text"] == "Test Title"
        assert result["layout"]["barmode"] == "group"
        assert result["layout"]["showlegend"] is True

    def test_empty_data_returns_bar_chart(self):
        result = plotly_grouped_bar([], {}, "Empty")
        assert len(result["data"]) == 1
        assert result["data"][0]["type"] == "bar"
        assert result["data"][0]["x"] == []
        assert result["data"][0]["y"] == []

    def test_single_series(self):
        series_data = {"Only": [1, 2, 3]}
        result = plotly_grouped_bar(["A", "B", "C"], series_data, "Single")
        assert len(result["data"]) == 1
        assert result["data"][0]["name"] == "Only"

    def test_legend_configured(self):
        series_data = {"X": [1], "Y": [2]}
        result = plotly_grouped_bar(["A"], series_data, "Legend Test")
        legend = result["layout"]["legend"]
        assert legend["orientation"] == "h"
        assert legend["title"]["text"] == "Series"
