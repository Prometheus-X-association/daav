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


class TestBuildCondition:

    @pytest.mark.parametrize("operator", ["IN", "NOT IN"])
    @pytest.mark.parametrize("value, expected", [
        ({"2": "b", "1": "a"}, ["a", "b"]),
        (["x", "y", "z"], ["x", "y", "z"]),
        ("solo", ["solo"]),
    ])
    def test_in_operators_value_shapes(self, converter, operator, value, expected):
        sql, params = converter._build_condition({"path": "name", "operator": operator, "value": value})
        placeholders = ", ".join(["?"] * len(expected))
        assert sql == f'"name" {operator} ({placeholders})'
        assert params == expected

    @pytest.mark.parametrize("operator", ["BETWEEN", "NOT BETWEEN"])
    @pytest.mark.parametrize("value, expected", [
        ("1,5", ["1", "5"]),
        ("1,5,9", ["1", "5,9"]),
        ({"2": 9, "1": 3}, [3, 9]),
        ([1, 2, 3], [1, 2]),
        ("7", ["7", "7"]),
        ([4], [[4], [4]]),
        ({"1": 4}, [{"1": 4}, {"1": 4}]),
    ])
    def test_between_value_shapes(self, converter, operator, value, expected):
        sql, params = converter._build_condition({"path": "age", "operator": operator, "value": value})
        assert sql == f'"age" {operator} ? AND ?'
        assert params == expected

    @pytest.mark.parametrize("operator, expected", [
        ("STARTS_WITH", "ab%"), ("ENDS_WITH", "%ab"), ("CONTAINS", "%ab%"),
    ])
    def test_like_operators(self, converter, operator, expected):
        assert converter._build_condition({"path": "name", "operator": operator, "value": "ab"}) == (
            '"name" LIKE ?', [expected])

    @pytest.mark.parametrize("operator", ["IS NULL", "IS NOT NULL"])
    def test_null_operators(self, converter, operator):
        assert converter._build_condition({"path": "name", "operator": operator, "value": "x"}) == (
            f'"name" {operator}', [])

    @pytest.mark.parametrize("operator, sql_operator", [
        ("=", "="), ("<>", "!="), (">", ">"), (">=", ">="), ("<", "<"), ("<=", "<="),
    ])
    def test_comparison_operators(self, converter, operator, sql_operator):
        assert converter._build_condition({"path": "age", "operator": operator, "value": 3}) == (
            f'"age" {sql_operator} ?', [3])

    def test_defaults(self, converter):
        assert converter._build_condition({}) == ('"" = ?', [None])

    def test_unknown_operator(self, converter):
        with pytest.raises(ValueError, match="Unsupported filter operator"):
            converter._build_condition({"path": "age", "operator": "LIKE", "value": 3})


class TestConvertFiltersToWhere:

    def test_no_filters(self, converter):
        assert converter.convert_filters_to_where({}) == ("", [])

    def test_shortcut_syntax(self, converter):
        assert converter.convert_filters_to_where({"name": "a"}) == ('"name" = ?', ["a"])
        assert converter.convert_filters_to_where({"name": {"value": "b"}}) == ('"name" = ?', ["b"])
        assert converter.convert_filters_to_where({"name": {"other": "c"}}) == ('"name" = ?', [{"other": "c"}])

    def test_unknown_conjunction(self, converter):
        filters = {
            "g": {"group": {"conjunction": "XOR"}},
            "a": {"condition": {"path": "name", "value": "a", "memberOf": "g"}},
        }
        with pytest.raises(ValueError, match="Unsupported filter group conjunction: 'XOR'"):
            converter.convert_filters_to_where(filters)

    def test_unknown_conjunction_of_an_empty_group_is_ignored(self, converter):
        filters = {
            "g": {"group": {"conjunction": "XOR"}},
            "a": {"condition": {"path": "name", "value": "a"}},
        }
        assert converter.convert_filters_to_where(filters) == ('"name" = ?', ["a"])

    def test_default_conjunction_is_and(self, converter):
        filters = {
            "g": {"group": {}},
            "a": {"condition": {"path": "name", "value": "a", "memberOf": "g"}},
            "b": {"condition": {"path": "age", "operator": ">", "value": 1, "memberOf": "g"}},
        }
        assert converter.convert_filters_to_where(filters) == ('("name" = ? AND "age" > ?)', ["a", 1])

    def test_empty_group(self, converter):
        assert converter.convert_filters_to_where({"g": {"group": {"conjunction": "OR"}}}) == ("", [])

    def test_member_of_an_undeclared_group_is_dropped(self, converter):
        filters = {
            "a": {"condition": {"path": "name", "value": "a", "memberOf": "missing"}},
            "b": {"condition": {"path": "age", "value": 2}},
        }
        assert converter.convert_filters_to_where(filters) == ('"age" = ?', [2])

    def test_conditions_declared_before_their_group(self, converter):
        filters = {
            "a": {"condition": {"path": "name", "value": "a", "memberOf": "g"}},
            "g": {"group": {"conjunction": "OR"}},
            "c": {"condition": {"path": "name", "value": "c", "memberOf": "g"}},
        }
        # The order of the query parameters must not matter
        assert converter.convert_filters_to_where(filters) == ('("name" = ? OR "name" = ?)', ["a", "c"])

    def test_root_parameters_come_before_group_parameters(self, converter):
        filters = {
            "g1": {"group": {"conjunction": "OR"}},
            "a": {"condition": {"path": "name", "value": "a", "memberOf": "g1"}},
            "b": {"condition": {"path": "name", "operator": "IN", "value": ["b", "c"], "memberOf": "g1"}},
            "r1": {"condition": {"path": "age", "operator": ">", "value": 5}},
            "g2": {"group": {"conjunction": "and"}},
            "d": {"condition": {"path": "age", "operator": "BETWEEN", "value": "1,9", "memberOf": "g2"}},
            "r2": "zz",
        }
        where, params = converter.convert_filters_to_where(filters)
        assert where == ('"age" > ? AND "r2" = ? AND ("name" = ? OR "name" IN (?, ?))'
                         ' AND ("age" BETWEEN ? AND ?)')
        assert params == [5, "zz", "a", "b", "c", "1", "9"]


class TestShortcutValues:
    """A shortcut value is plain text: the words 'group' and 'condition' in it mean nothing."""

    @pytest.mark.parametrize("value", ["conditional", "group", "condition", "my group name"])
    def test_shortcut_value_containing_a_keyword(self, converter, value):
        where, params = converter.convert_query_string_to_where(f"filter[status]={value.replace(' ', '%20')}")
        assert where == '"status" = ?'
        assert params == [value]
