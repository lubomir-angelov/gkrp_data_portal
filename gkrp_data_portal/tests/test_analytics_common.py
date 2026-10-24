"""Tests for gkrp_data_portal.ui.pages.analytics_common."""

from __future__ import annotations

import inspect
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from nicegui import ui
from nicegui.elements.markdown import prepare_content

from gkrp_data_portal.ui.repository.analytics_repo import build_chart_histogram
from gkrp_data_portal.ui.pages.analytics_common import (
    CHART_GUIDE_PATH,
    PLOTLY_EXPORT_JS,
    QUERY_OPTIONS,
    TABLE_GUIDE_PATH,
    build_histogram,
    build_histogram_series,
    is_ui_hidden_column,
    parse_date,
    plotly_bar,
    plotly_grouped_bar,
    ui_columns,
)


class TestQueryOptions:
    def test_contains_expected_queries(self):
        assert "q2" in QUERY_OPTIONS.values()
        assert "finds_arch" in QUERY_OPTIONS.values()

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
        assert "f_inventory" not in result
        assert "l_recordenteredon" not in result
        assert "l_layerid" not in result

    def test_preserves_original_casing(self):
        columns = ["L_Site", "F_Piecetype"]
        result = ui_columns(columns)
        assert "L_Site" in result
        assert "F_Piecetype" in result

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


class TestBuildHistogram:
    def test_empty(self):
        assert build_histogram([]) == ([], [])

    def test_preserves_sql_input_order(self):
        rows = [{"bucket": "b", "count": 2}, {"bucket": "a", "count": 5}]
        assert build_histogram(rows) == (["b", "a"], [2, 5])

    def test_ties_keep_input_order(self):
        rows = [{"bucket": "x", "count": 3}, {"bucket": "y", "count": 3}]
        assert build_histogram(rows) == (["x", "y"], [3, 3])

    def test_null_bucket_passes_through(self):
        rows = [{"bucket": None, "count": 1}]
        assert build_histogram(rows) == ([None], [1])

    def test_missing_count_raises(self):
        with pytest.raises(KeyError):
            build_histogram([{"bucket": "a"}])


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


class TestColumnToLabel:
    def test_column_to_label_mapping(self):
        from gkrp_data_portal.ui.pages.analytics_common import LOCALE, _column_to_label

        assert _column_to_label("f_technology") == LOCALE["frag_technology"]
        assert _column_to_label("f_piecetype") == LOCALE["frag_piecetype"]
        assert _column_to_label("f_surface") == LOCALE["frag_surface"]
        assert _column_to_label("o_primary_") == LOCALE["frag_primary"]
        assert _column_to_label("l_site") == LOCALE["label_site"]
        assert _column_to_label("fi_find_type") == LOCALE["label_find_type"]

    def test_unmapped_column_raises(self):
        from gkrp_data_portal.ui.pages.analytics_common import _column_to_label

        with pytest.raises(KeyError):
            _column_to_label("unknown_col")


def _srow(x, s, c):
    return {"x_bucket": x, "series_bucket": s, "count": c}


class TestBuildHistogramSeries:
    def test_empty(self):
        assert build_histogram_series([]) == ([], {})

    def test_pivot_and_zero_fill(self):
        rows = [_srow("A", "X", 3), _srow("A", "Y", 5), _srow("B", "X", 2)]
        xs, data = build_histogram_series(rows)
        assert xs == ["A", "B"]
        assert data == {"X": [3, 2], "Y": [5, 0]}

    def test_x_order_is_first_appearance(self):
        rows = [_srow("B", "X", 1), _srow("A", "X", 9), _srow("B", "Y", 4)]
        xs, data = build_histogram_series(rows)
        assert xs == ["B", "A"]
        assert data == {"X": [1, 9], "Y": [4, 0]}

    def test_count_coerced_to_int(self):
        xs, data = build_histogram_series([_srow("A", "X", Decimal("4"))])
        assert data == {"X": [4]}
        assert isinstance(data["X"][0], int)

    def test_missing_series_bucket_raises(self):
        with pytest.raises(KeyError):
            build_histogram_series([{"x_bucket": "A", "count": 1}])

    def test_producer_consumer_contract(self):
        mock_db = MagicMock()
        mock_row = MagicMock()
        mock_row.mappings.return_value.all.return_value = [
            {"x_bucket": "Sofia", "series_bucket": "Body", "cnt": 100},
            {"x_bucket": "Sofia", "series_bucket": "Rim", "cnt": 50},
            {"x_bucket": "Plovdiv", "series_bucket": "Body", "cnt": 30},
        ]
        mock_db.execute.return_value = mock_row
        result = build_chart_histogram(
            mock_db,
            query_id="q2",
            x_key="l_site",
            series_key="f_piecetype",
            layer_filters=None,
            frag_filters=None,
        )
        xs, data = build_histogram_series(result)
        assert xs == ["Sofia", "Plovdiv"]
        assert data == {"Body": [100, 30], "Rim": [50, 0]}


class TestPlotlyExportJs:
    """Regression: chart download buttons silently no-op unless the JS
    targets the "c"-prefixed element DOM id and loads Plotly from the
    "nicegui-plotly" ES module (window.Plotly is never set by NiceGUI)."""

    def test_uses_c_prefixed_dom_id(self):
        assert "getElementById('c' + id)" in PLOTLY_EXPORT_JS

    def test_resolves_plotly_via_esm_module(self):
        assert "import('nicegui-plotly')" in PLOTLY_EXPORT_JS

    def test_exposes_helper_functions(self):
        for name in (
            "window.__gkrpPlotly",
            "window.__gkrpPlotlyEl",
            "window.__gkrpPlotlyDownload",
            "window.__gkrpPlotlyResize",
            "window.__gkrpPlotlyPrint",
        ):
            assert name in PLOTLY_EXPORT_JS

    def test_print_helper_does_not_swallow_errors(self):
        print_js = PLOTLY_EXPORT_JS[
            PLOTLY_EXPORT_JS.index("window.__gkrpPlotlyPrint") :
        ]
        assert "catch(() => {})" not in print_js


class TestPlotlyGroupedBar:
    def test_returns_expected_structure(self):
        series_data = {
            "Tech 1": [10, 20, 30],
            "Tech 2": [5, 10, 15],
        }
        result = plotly_grouped_bar(
            ["A", "B", "C"], series_data, "Test Title", series_label="Тип"
        )
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
        result = plotly_grouped_bar([], {}, "Empty", series_label="Тип")
        assert len(result["data"]) == 1
        assert result["data"][0]["type"] == "bar"
        assert result["data"][0]["x"] == []
        assert result["data"][0]["y"] == []

    def test_single_series(self):
        series_data = {"Only": [1, 2, 3]}
        result = plotly_grouped_bar(
            ["A", "B", "C"], series_data, "Single", series_label="Тип"
        )
        assert len(result["data"]) == 1
        assert result["data"][0]["name"] == "Only"

    def test_legend_configured(self):
        series_data = {"X": [1], "Y": [2]}
        result = plotly_grouped_bar(
            ["A"], series_data, "Legend Test", series_label="Тип"
        )
        legend = result["layout"]["legend"]
        assert legend["orientation"] == "h"
        assert legend["title"]["text"] == "Тип"


class TestGuides:
    @pytest.mark.parametrize("path", [CHART_GUIDE_PATH, TABLE_GUIDE_PATH])
    def test_guide_file_exists(self, path):
        assert path.is_file()

    @pytest.mark.parametrize("path", [CHART_GUIDE_PATH, TABLE_GUIDE_PATH])
    def test_guide_renders_tables_and_heading(self, path):
        extras = inspect.signature(ui.markdown).parameters["extras"].default
        html = prepare_content(path.read_text(encoding="utf-8"), " ".join(extras))
        assert "<table>" in html
        assert "<h1>" in html
