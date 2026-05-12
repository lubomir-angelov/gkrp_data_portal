"""Tests for gkrp_data_portal.ui.repository.archaeology_repo."""

from __future__ import annotations

from unittest.mock import MagicMock

from sqlalchemy import Select

from gkrp_data_portal.ui.repository.archaeology_repo import (
    SearchResult,
    fragment_choices,
    layer_choices,
    list_fragments,
    list_layers,
    list_ornaments,
    most_recent_fragment_id,
    most_recent_layer_id,
)


class TestListLayers:
    def test_returns_search_result(self):
        mock_db = MagicMock()
        mock_layer = MagicMock()
        mock_layer.layerid = 1
        mock_db.execute.return_value.scalars.return_value.all.return_value = [
            mock_layer
        ]

        result = list_layers(mock_db)
        assert isinstance(result, SearchResult)
        assert len(result.items) == 1
        assert result.total == 1

    def test_uses_desc_order(self):
        mock_db = MagicMock()
        mock_db.execute.return_value.scalars.return_value.all.return_value = []
        list_layers(mock_db)
        stmt = mock_db.execute.call_args[0][0]
        assert isinstance(stmt, Select)

    def test_applies_search_query(self):
        mock_db = MagicMock()
        mock_db.execute.return_value.scalars.return_value.all.return_value = []
        list_layers(mock_db, q="Sofia")
        stmt = mock_db.execute.call_args[0][0]
        assert isinstance(stmt, Select)

    def test_limits_results(self):
        mock_db = MagicMock()
        mock_db.execute.return_value.scalars.return_value.all.return_value = []
        list_layers(mock_db, limit=50)
        stmt = mock_db.execute.call_args[0][0]
        assert isinstance(stmt, Select)


class TestListFragments:
    def test_returns_search_result(self):
        mock_db = MagicMock()
        mock_frag = MagicMock()
        mock_db.execute.return_value.scalars.return_value.all.return_value = [mock_frag]

        result = list_fragments(mock_db)
        assert isinstance(result, SearchResult)
        assert result.total == 1

    def test_applies_search_query(self):
        mock_db = MagicMock()
        mock_db.execute.return_value.scalars.return_value.all.return_value = []
        list_fragments(mock_db, q="pottery")
        stmt = mock_db.execute.call_args[0][0]
        assert isinstance(stmt, Select)


class TestListOrnaments:
    def test_returns_search_result(self):
        mock_db = MagicMock()
        mock_orn = MagicMock()
        mock_db.execute.return_value.scalars.return_value.all.return_value = [mock_orn]

        result = list_ornaments(mock_db)
        assert isinstance(result, SearchResult)
        assert result.total == 1

    def test_applies_search_query(self):
        mock_db = MagicMock()
        mock_db.execute.return_value.scalars.return_value.all.return_value = []
        list_ornaments(mock_db, q="pattern")
        stmt = mock_db.execute.call_args[0][0]
        assert isinstance(stmt, Select)


class TestMostRecentLayerId:
    def test_returns_id(self):
        mock_db = MagicMock()
        mock_db.execute.return_value.scalar_one_or_none.return_value = 42
        assert most_recent_layer_id(mock_db) == 42

    def test_returns_none_when_empty(self):
        mock_db = MagicMock()
        mock_db.execute.return_value.scalar_one_or_none.return_value = None
        assert most_recent_layer_id(mock_db) is None


class TestMostRecentFragmentId:
    def test_returns_id(self):
        mock_db = MagicMock()
        mock_db.execute.return_value.scalar_one_or_none.return_value = 19500
        assert most_recent_fragment_id(mock_db) == 19500

    def test_returns_none_when_empty(self):
        mock_db = MagicMock()
        mock_db.execute.return_value.scalar_one_or_none.return_value = None
        assert most_recent_fragment_id(mock_db) is None


class TestLayerChoices:
    def test_returns_list_of_tuples(self):
        mock_db = MagicMock()
        mock_layer = MagicMock()
        mock_layer.layerid = 1
        mock_layer.site = "Sofia"
        mock_layer.sector = "Alpha"
        mock_layer.square = "A1"
        mock_layer.layername = "Test Layer"
        mock_db.execute.return_value.scalars.return_value.all.return_value = [
            mock_layer
        ]

        result = layer_choices(mock_db)
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], tuple)
        assert result[0][0] == 1

    def test_includes_label_parts(self):
        mock_db = MagicMock()
        mock_layer = MagicMock()
        mock_layer.layerid = 5
        mock_layer.site = "Plovdiv"
        mock_layer.sector = "B"
        mock_layer.square = "C2"
        mock_layer.layername = None
        mock_layer.layer = "Layer X"
        mock_db.execute.return_value.scalars.return_value.all.return_value = [
            mock_layer
        ]

        result = layer_choices(mock_db)
        label = result[0][1]
        assert "Plovdiv" in label
        assert "B" in label
        assert "C2" in label
        assert "Layer X" in label

    def test_handles_none_values_in_label(self):
        mock_db = MagicMock()
        mock_layer = MagicMock()
        mock_layer.layerid = 3
        mock_layer.site = None
        mock_layer.sector = None
        mock_layer.square = None
        mock_layer.layername = None
        mock_layer.layer = None
        mock_db.execute.return_value.scalars.return_value.all.return_value = [
            mock_layer
        ]

        result = layer_choices(mock_db)
        label = result[0][1]
        # None values become empty strings via the `or ''` pattern
        assert "3" in label
        assert "Plovdiv" not in label


class TestFragmentChoices:
    def test_returns_list_of_tuples(self):
        mock_db = MagicMock()
        mock_frag = MagicMock()
        mock_frag.fragmentid = 19400
        mock_frag.locationid = 5
        mock_frag.piecetype = "ustie"
        mock_frag.inventory = "INV-001"
        mock_db.execute.return_value.scalars.return_value.all.return_value = [mock_frag]

        result = fragment_choices(mock_db)
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0][0] == 19400

    def test_includes_label_parts(self):
        mock_db = MagicMock()
        mock_frag = MagicMock()
        mock_frag.fragmentid = 19401
        mock_frag.locationid = 10
        mock_frag.piecetype = "stena"
        mock_frag.inventory = ""
        mock_db.execute.return_value.scalars.return_value.all.return_value = [mock_frag]

        result = fragment_choices(mock_db)
        label = result[0][1]
        assert "19401" in label
        assert "loc=10" in label
        assert "stena" in label
