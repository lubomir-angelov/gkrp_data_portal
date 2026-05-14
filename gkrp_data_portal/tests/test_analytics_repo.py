"""Tests for gkrp_data_portal.ui.repository.analytics_repo."""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock


from gkrp_data_portal.ui.repository.analytics_repo import (
    AnalyticsResult,
    _build_where,
    _model_select_list,
    extract_image_urls,
    query_finds,
    query_q1_layers_fragments,
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
            query_id="q1",
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
            query_id="q1",
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
            query_id="q1",
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
            query_id="q1",
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
            query_id="q1",
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

    def test_free_text_q1(self):
        sql, params = _build_where(
            query_id="q1",
            site=None,
            sector=None,
            square=None,
            date_from=None,
            date_to=None,
            q="pottery",
        )
        assert "COALESCE(f.inventory,'') ILIKE :q" in sql
        assert "COALESCE(f.note,'') ILIKE :q" in sql
        assert "COALESCE(f.piecetype::text,'') ILIKE :q" in sql

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
            query_id="q1",
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


class TestExtractImageUrls:
    def test_returns_unique_urls(self):
        items = [
            {"f_image_url": "http://example.com/1.jpg"},
            {"f_image_url": "http://example.com/2.jpg"},
            {"f_image_url": "http://example.com/1.jpg"},
        ]
        urls = extract_image_urls(items)
        assert urls == ["http://example.com/1.jpg", "http://example.com/2.jpg"]

    def test_skips_none_values(self):
        items = [{"f_image_url": None}, {"f_image_url": "http://example.com/1.jpg"}]
        urls = extract_image_urls(items)
        assert urls == ["http://example.com/1.jpg"]

    def test_skips_empty_strings(self):
        items = [
            {"f_image_url": ""},
            {"f_image_url": "   "},
            {"f_image_url": "http://example.com/1.jpg"},
        ]
        urls = extract_image_urls(items)
        assert urls == ["http://example.com/1.jpg"]

    def test_collects_from_finds_column(self):
        items = [
            {"fi_image_url": "http://example.com/find1.jpg"},
        ]
        urls = extract_image_urls(items)
        assert urls == ["http://example.com/find1.jpg"]

    def test_returns_empty_for_no_images(self):
        items = [{"some_other_col": "value"}]
        assert extract_image_urls(items) == []

    def test_skips_non_string_values(self):
        items = [{"f_image_url": 123}, {"f_image_url": "http://example.com/1.jpg"}]
        urls = extract_image_urls(items)
        assert urls == ["http://example.com/1.jpg"]


class TestQueryQ1LayersFragments:
    def test_returns_analytics_result(self):
        mock_db = MagicMock()
        mock_row = MagicMock()
        mock_row.mappings.return_value.all.return_value = []
        mock_db.execute.return_value = mock_row
        mock_row.scalar_one.return_value = 0

        result = query_q1_layers_fragments(mock_db)
        assert isinstance(result, AnalyticsResult)
        assert result.items == []
        assert result.total == 0

    def test_passes_filters_to_query(self):
        mock_db = MagicMock()
        mock_row = MagicMock()
        mock_row.mappings.return_value.all.return_value = []
        mock_db.execute.return_value = mock_row
        mock_row.scalar_one.return_value = 0

        query_q1_layers_fragments(
            mock_db,
            site="Sofia",
            sector="Alpha",
            date_from=date(2024, 1, 1),
            date_to=date(2024, 12, 31),
            q="pottery",
        )

        calls = mock_db.execute.call_args_list
        assert len(calls) == 2  # count query + data query
        all_sql = " ".join(str(c) for c in calls)
        assert "Sofia" in all_sql

    def test_count_uses_sum_f_count(self):
        mock_db = MagicMock()
        mock_row = MagicMock()
        mock_row.mappings.return_value.all.return_value = []
        mock_db.execute.return_value = mock_row
        mock_row.scalar_one.return_value = 0

        query_q1_layers_fragments(mock_db)

        calls = mock_db.execute.call_args_list
        count_sql = str(calls[1][0][0])
        assert "SUM(f_count)" in count_sql
        assert "COUNT(*)" not in count_sql


class TestQueryQ2LayersFragmentsOrnaments:
    def test_returns_analytics_result(self):
        mock_db = MagicMock()
        mock_row = MagicMock()
        mock_row.mappings.return_value.all.return_value = []
        mock_db.execute.return_value = mock_row
        mock_row.scalar_one.return_value = 0

        result = query_q2_layers_fragments_ornaments(mock_db)
        assert isinstance(result, AnalyticsResult)

    def test_count_uses_sum_f_count(self):
        mock_db = MagicMock()
        mock_row = MagicMock()
        mock_row.mappings.return_value.all.return_value = []
        mock_db.execute.return_value = mock_row
        mock_row.scalar_one.return_value = 0

        query_q2_layers_fragments_ornaments(mock_db)

        calls = mock_db.execute.call_args_list
        count_sql = str(calls[1][0][0])
        assert "SUM(f_count)" in count_sql
        assert "COUNT(*)" not in count_sql


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

    def test_count_uses_sum_f_count(self):
        mock_db = MagicMock()
        mock_row = MagicMock()
        mock_row.mappings.return_value.all.return_value = []
        mock_db.execute.return_value = mock_row
        mock_row.scalar_one.return_value = 0

        query_finds(mock_db)

        calls = mock_db.execute.call_args_list
        count_sql = str(calls[1][0][0])
        assert "SUM(f_count)" in count_sql
        assert "COUNT(*)" not in count_sql
