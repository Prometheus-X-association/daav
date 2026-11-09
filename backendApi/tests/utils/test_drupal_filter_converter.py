"""
Tests for the Drupal JSON:API filter to SQL WHERE converter.
"""
import json
import urllib.parse

import pytest

from app.utils.drupal_filter_converter import DrupalFilterConverter
from app.utils.utils import filter_data_with_duckdb


@pytest.fixture
def converter():
    return DrupalFilterConverter()


@pytest.fixture
def data_file(tmp_path):
    path = tmp_path / "data.json"
    path.write_text(json.dumps([
        {"name": "a", "age": 10},
        {"name": "b", "age": 20},
        {"name": "c", "age": 30},
    ]))
    return str(path)


def _query(params: dict) -> str:
    return urllib.parse.urlencode(params)


class TestDrupalFilterConverter:

    def test_simple_condition(self, converter):
        where, params = converter.convert_query_string_to_where(_query({
            "filter[f][condition][path]": "model",
            "filter[f][condition][operator]": "STARTS_WITH",
            "filter[f][condition][value]": "M",
        }))
        assert where == '"model" LIKE ?'
        assert params == ["M%"]

    def test_in_operator_uses_qmark_placeholders(self, converter):
        where, params = converter.convert_query_string_to_where(_query({
            "filter[f][condition][path]": "name",
            "filter[f][condition][operator]": "IN",
            "filter[f][condition][value][1]": "a",
            "filter[f][condition][value][2]": "c",
        }))
        assert where == '"name" IN (?, ?)'
        assert sorted(params) == ["a", "c"]

    @pytest.mark.parametrize("operator, expected", [("IN", ["a", "c"]), ("NOT IN", ["b"])])
    def test_in_operators_with_duckdb(self, converter, data_file, operator, expected):
        where, params = converter.convert_query_string_to_where(_query({
            "filter[f][condition][path]": "name",
            "filter[f][condition][operator]": operator,
            "filter[f][condition][value][1]": "a",
            "filter[f][condition][value][2]": "c",
        }))
        rows = filter_data_with_duckdb(data_file, where=where, params=params)
        assert sorted(row["name"] for row in rows) == expected

    def test_path_is_quoted_as_identifier(self, converter):
        where, _ = converter.convert_query_string_to_where(_query({
            "filter[f][condition][path]": 'name" OR 1=1 --',
            "filter[f][condition][value]": "zz",
        }))
        assert where == '"name"" OR 1=1 --" = ?'

    def test_path_injection_is_not_executed(self, converter, data_file):
        where, params = converter.convert_query_string_to_where(_query({
            "filter[f][condition][path]": "name = (select content from read_text('/etc/hostname')) OR name",
            "filter[f][condition][operator]": "<>",
            "filter[f][condition][value]": "zz",
        }))
        # The whole path is treated as an (unknown) column name, not as SQL
        with pytest.raises(Exception) as exc_info:
            filter_data_with_duckdb(data_file, where=where, params=params)
        assert "read_text" in str(exc_info.value)
        assert "not found" in str(exc_info.value).lower()

    def _group_query(self, conjunction: str) -> str:
        return _query({
            "filter[g][group][conjunction]": conjunction,
            "filter[a][condition][path]": "name",
            "filter[a][condition][value]": "a",
            "filter[a][condition][memberOf]": "g",
            "filter[c][condition][path]": "name",
            "filter[c][condition][value]": "c",
            "filter[c][condition][memberOf]": "g",
        })

    @pytest.mark.parametrize("conjunction", ["OR", "or"])
    def test_group_conjunction(self, converter, data_file, conjunction):
        where, params = converter.convert_query_string_to_where(self._group_query(conjunction))
        assert where == '("name" = ? OR "name" = ?)'
        rows = filter_data_with_duckdb(data_file, where=where, params=params)
        assert sorted(row["name"] for row in rows) == ["a", "c"]

    def test_group_conjunction_is_whitelisted(self, converter):
        with pytest.raises(ValueError, match="conjunction"):
            converter.convert_query_string_to_where(self._group_query("OR 1=1 OR"))

    def test_duckdb_query_cannot_access_files(self, data_file):
        # Defense in depth: even an injected clause cannot read files once the data is loaded
        with pytest.raises(Exception) as exc_info:
            filter_data_with_duckdb(
                data_file,
                where="name IN (SELECT content FROM read_text(?))",
                params=[data_file],
            )
        assert "disabled by configuration" in str(exc_info.value)
