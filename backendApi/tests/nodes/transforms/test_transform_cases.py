"""
FlattenTransform.process and FilterTransform.process: input types, output modes and errors.
"""
from unittest.mock import Mock

import pandas as pd
import pytest

from app.enums.status_node import StatusNode
from app.models.interface.node_data import NodeDataPandasDf, NodeDataParquet
from app.nodes.transforms.filter_transform import FilterTransform
from app.nodes.transforms.flatten_transform import FlattenTransform
from app.utils.utils import generate_pandas_schema


# ===========================
# FlattenTransform.process
# ===========================

RECORDS = [
    {"id": 1, "user": {"name": "a"}, "orders": [{"p": "x", "q": 1}, {"p": "y", "q": 2}], "tags": []},
    {"id": 2, "user": {"name": "b"}, "orders": [], "tags": []},
]


def _flatten(parquet_save=False, data=None):
    node = FlattenTransform(id="fl", data={"parquetSave": {"value": parquet_save}} if data is None else data)
    node.inputs = {"datasource": Mock()}
    node.outputs = {"out": Mock()}
    return node


def _published(node):
    return node.outputs["out"].set_node_data.call_args.args[0]


@pytest.mark.parametrize("sample", [False, True])
def test_flatten_parquet_input(tmp_path, sample):
    df = pd.DataFrame([{"id": 1, "user": {"name": "a"}}])
    data_path, example_path = tmp_path / "data.parquet", tmp_path / "example.parquet"
    df.to_parquet(data_path)
    pd.DataFrame([{"id": 9, "user": {"name": "z"}}]).to_parquet(example_path)
    node = _flatten()
    node.inputs["datasource"].get_node_data.return_value = NodeDataParquet.model_construct(
        data=str(data_path), dataExample=str(example_path), nodeSchema=None, name="p")

    assert node.process(sample) == StatusNode.Valid
    result = _published(node)
    frame = result.dataExample if sample else result.data
    assert frame.to_dict("records") == ([{"id": 9, "user_name": "z"}] if sample else [{"id": 1, "user_name": "a"}])


def test_flatten_dataframe_input_and_lists():
    df = pd.DataFrame(RECORDS)
    node = _flatten()
    node.inputs["datasource"].get_node_data.return_value = NodeDataPandasDf(
        nodeSchema=generate_pandas_schema(df), data=df, dataExample=df.head(1), name="d")

    assert node.process() == StatusNode.Valid
    result = _published(node)
    rows = result.data.to_dict("records")
    assert [(r["id"], r["user_name"]) for r in rows] == [(1, "a"), (1, "a"), (2, "b")]
    assert [r["orders_p"] for r in rows[:2]] == ["x", "y"]
    assert pd.isna(rows[2]["orders_p"])
    assert all(r["tags"] == [] for r in rows)
    assert result.name == "Flattened Data"
    assert len(result.dataExample) == 3


def test_flatten_sample_uses_the_example():
    df = pd.DataFrame(RECORDS)
    node = _flatten()
    node.inputs["datasource"].get_node_data.return_value = NodeDataPandasDf(
        nodeSchema=generate_pandas_schema(df), data=df, dataExample=df.head(1), name="d")

    assert node.process(True) == StatusNode.Valid
    result = _published(node)
    assert result.data is None
    assert result.dataExample["orders_p"].tolist() == ["x", "y"]


def test_flatten_column_of_empty_lists_is_kept():
    df = pd.DataFrame([{"id": 1, "tags": []}, {"id": 2, "tags": []}])
    node = _flatten()
    node.inputs["datasource"].get_node_data.return_value = NodeDataPandasDf(
        nodeSchema=generate_pandas_schema(df), data=df, dataExample=df, name="d")

    assert node.process() == StatusNode.Valid
    assert _published(node).data.to_dict("records") == [{"id": 1, "tags": []}, {"id": 2, "tags": []}]


@pytest.mark.parametrize("node, input_data, message", [
    (_flatten(parquet_save=True), None, "Parquet output no supported actually for flatten transform"),
    (_flatten(data={}), None, "Data Mapping is required"),
    (_flatten(), "not node data", "Input data is not a handled format"),
])
def test_flatten_errors(node, input_data, message):
    node.inputs["datasource"].get_node_data.return_value = input_data

    assert node.process() == StatusNode.Error
    assert node.statusMessage == message
    assert node.errorStackTrace
    node.outputs["out"].set_node_data.assert_not_called()


# ===========================
# FilterTransform.process
# ===========================

PEOPLE = pd.DataFrame({"name": ["a", "b", "c"], "age": [10, 20, 30]})
AGE_20 = {"condition": "AND", "rules": [{"field": "age", "operator": ">=", "value": 20}]}


def _filter(parquet_save=False, rules=AGE_20):
    node = FilterTransform(id="flt", data={"dataSource": "ds", "filterRules": rules,
                                           "parquetSave": {"value": parquet_save}})
    node.inputs = {"ds": Mock()}
    node.outputs = {"out": Mock()}
    return node


def _source(kind, tmp_path, df=PEOPLE):
    if kind == "dataframe":
        return NodeDataPandasDf(nodeSchema=generate_pandas_schema(df), data=df, dataExample=df.head(2), name="d")
    path = tmp_path / "in.parquet"
    df.to_parquet(path)
    return NodeDataParquet.model_construct(data=str(path), dataExample=None, nodeSchema=None, name="p")


@pytest.mark.parametrize("kind", ["dataframe", "parquet"])
def test_filter_to_dataframe(tmp_path, kind):
    node = _filter()
    node.inputs["ds"].get_node_data.return_value = _source(kind, tmp_path)

    assert node.process() == StatusNode.Valid
    result = _published(node)
    assert isinstance(result, NodeDataPandasDf)
    assert result.data.to_dict("records") == [{"name": "b", "age": 20}, {"name": "c", "age": 30}]
    assert len(result.dataExample) == 2
    assert result.name == "Filtered Data"


@pytest.mark.parametrize("kind", ["dataframe", "parquet"])
def test_filter_to_parquet(tmp_path, kind):
    node = _filter(parquet_save=True)
    node.inputs["ds"].get_node_data.return_value = _source(kind, tmp_path)

    assert node.process() == StatusNode.Valid
    result = _published(node)
    assert isinstance(result, NodeDataParquet)
    assert result.name == "filtered_data"
    assert result.data.endswith("filtered_data_flt.parquet")
    assert pd.read_parquet(result.data).to_dict("records") == [{"name": "b", "age": 20}, {"name": "c", "age": 30}]


def test_filter_sample_dataframe_uses_the_example(tmp_path):
    node = _filter()
    node.inputs["ds"].get_node_data.return_value = _source("dataframe", tmp_path)

    assert node.process(True) == StatusNode.Valid
    result = _published(node)
    assert result.data is None
    assert result.dataExample.to_dict("records") == [{"name": "b", "age": 20}]


def test_filter_sample_parquet_mode_uses_the_example(tmp_path):
    node = _filter(parquet_save=True)
    node.inputs["ds"].get_node_data.return_value = _source("dataframe", tmp_path)

    assert node.process(True) == StatusNode.Valid
    assert pd.read_parquet(_published(node).data)["name"].tolist() == ["b"]


@pytest.mark.parametrize("parquet_save", [False, True])
def test_filter_empty_result_of_a_parquet_input(tmp_path, parquet_save):
    """A filter that matches no row is a valid, empty result that keeps its columns."""
    node = _filter(parquet_save=parquet_save,
                   rules={"condition": "AND", "rules": [{"field": "age", "operator": ">", "value": 99}]})
    node.inputs["ds"].get_node_data.return_value = _source("parquet", tmp_path)

    assert node.process() == StatusNode.Valid
    result = _published(node)
    frame = pd.read_parquet(result.data) if parquet_save else result.data
    assert len(frame) == 0
    assert list(frame.columns) == ["name", "age"]


def test_filter_without_rules_keeps_everything(tmp_path):
    node = _filter(rules={"condition": "AND", "rules": []})
    node.inputs["ds"].get_node_data.return_value = _source("dataframe", tmp_path)

    assert node.process() == StatusNode.Valid
    assert len(_published(node).data) == 3


@pytest.mark.parametrize("rules, message", [
    ({"condition": "XOR", "rules": [{"field": "age", "operator": "=", "value": 1}]},
     "Error in filter conditions: WARNING: Invalid condition Unsupported conjunction: 'XOR'. Only AND/OR are allowed."),
    ({"condition": "AND", "rules": [{"field": "age", "operator": "like", "value": 1}]},
     "Error in filter conditions: WARNING: Invalid condition WARNING: Invalid condition Unsupported numeric operator: 'like'"),
    ({"condition": "AND", "rules": [{"other": 1}]},
     "Error in filter conditions: WARNING: Invalid condition WARNING: Invalid condition WARNING: Invalid condition {'other': 1}"),
])
def test_filter_invalid_rules(tmp_path, rules, message):
    node = _filter(rules=rules)
    node.inputs["ds"].get_node_data.return_value = _source("dataframe", tmp_path)

    assert node.process() == StatusNode.Error
    assert node.statusMessage == message


@pytest.mark.parametrize("parquet_save", [False, True])
def test_filter_unknown_input(parquet_save):
    node = _filter(parquet_save=parquet_save)
    node.inputs["ds"].get_node_data.return_value = "not node data"

    assert node.process() == StatusNode.Error
    assert node.statusMessage == "Unkown data input"
    assert node.errorStackTrace


def test_filter_missing_configuration():
    node = FilterTransform(id="flt", data={"dataSource": "ds", "filterRules": AGE_20})

    assert node.process() == StatusNode.Error
    assert node.statusMessage == "Input required"
