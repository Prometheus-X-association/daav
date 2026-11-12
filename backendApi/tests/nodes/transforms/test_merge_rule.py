"""
The rule of the merge node: each target column holds its sources end to end, and a target column shorter than
the longest one is completed with missing values.
"""
from unittest.mock import Mock

import pandas as pd
import pytest

from app.enums.status_node import StatusNode
from app.models.interface.node_data import NodeDataPandasDf, NodeDataParquet
from app.nodes.transforms.merge_transform import MergeTransform


def frame(start, count, prefix="r"):
    return pd.DataFrame({"n": range(start, start + count), "s": [f"{prefix}{i}" for i in range(start, start + count)]})


def pandas_data(df, sample_rows=20):
    return NodeDataPandasDf(nodeSchema=[], data=df, dataExample=df.head(sample_rows), name="in")


def target(name, *sources):
    """A mapping item: the target column holds the given (dataset, column) sources end to end, in this order."""
    return {"id": f"m-{name}", "targetName": name,
            "sources": [{"id": f"{position}", "name": column, "type": "string", "datasetId": dataset}
                        for position, (dataset, column) in enumerate(sources)]}


def merge_node(mapping, inputs, parquet_save):
    node = MergeTransform(id="merge1", data={"dataMapping": mapping, "parquetSave": {"value": parquet_save}})
    node.inputs = {dataset: Mock(**{"get_node_data.return_value": node_data}) for dataset, node_data in inputs.items()}
    node.outputs = {"out": Mock()}
    return node


def merge(mapping, inputs, parquet_save=False, sample=False):
    """Result of the merge as a DataFrame: read from the file it wrote with the parquet option."""
    node = merge_node(mapping, inputs, parquet_save)
    status = node.process(sample=sample)
    assert status == StatusNode.Valid, node.statusMessage
    node_data = node.outputs["out"].set_node_data.call_args.args[0]
    if parquet_save:
        assert isinstance(node_data, NodeDataParquet)
        return pd.read_parquet(node_data.data)
    return node_data.dataExample if sample else node_data.data


def values(df):
    """Columns as lists, with None for every missing value."""
    return {column: [None if pd.isna(value) else value for value in df[column].tolist()] for column in df.columns}


@pytest.fixture(autouse=True)
def upload_dir(tmp_path, monkeypatch):
    uploads = tmp_path / "uploads"
    uploads.mkdir()
    monkeypatch.setattr("app.nodes.transforms.merge_transform.settings.upload_dir", str(uploads))
    return uploads


# ===========================
# IN MEMORY
# ===========================

TWO_INPUTS = {"ds1": pandas_data(frame(0, 250)), "ds2": pandas_data(frame(1000, 50))}


def test_sources_are_put_end_to_end():
    mapping = [target("number", ("ds1", "n"), ("ds2", "n")), target("label", ("ds1", "s"), ("ds2", "s"))]

    result = values(merge(mapping, TWO_INPUTS))

    assert result["number"] == list(range(250)) + list(range(1000, 1050))
    assert result["label"][249:251] == ["r249", "r1000"]


def test_shorter_target_column_is_completed_when_it_comes_last():
    mapping = [target("long", ("ds1", "n")), target("short", ("ds2", "n"))]

    result = values(merge(mapping, TWO_INPUTS))

    assert result["long"] == list(range(250))
    assert result["short"] == list(range(1000, 1050)) + [None] * 200


def test_shorter_target_column_is_completed_when_it_comes_first():
    mapping = [target("short", ("ds2", "n")), target("long", ("ds1", "n"))]

    result = merge(mapping, TWO_INPUTS)

    assert list(result.columns) == ["short", "long"]
    assert values(result) == {"short": list(range(1000, 1050)) + [None] * 200, "long": list(range(250))}


def test_no_row_is_lost_between_stacked_and_single_columns():
    mapping = [target("short", ("ds2", "s")), target("stacked", ("ds2", "n"), ("ds1", "n"), ("ds2", "n"))]

    result = values(merge(mapping, TWO_INPUTS))

    assert result["stacked"] == list(range(1000, 1050)) + list(range(250)) + list(range(1000, 1050))
    assert result["short"] == [f"r{i}" for i in range(1000, 1050)] + [None] * 300


def test_sample_merges_the_examples():
    mapping = [target("short", ("ds2", "n")), target("stacked", ("ds1", "n"), ("ds2", "n"))]
    inputs = {"ds1": pandas_data(frame(0, 250), sample_rows=20), "ds2": pandas_data(frame(1000, 50), sample_rows=5)}

    result = values(merge(mapping, inputs, sample=True))

    assert result == {"short": list(range(1000, 1005)) + [None] * 20,
                      "stacked": list(range(20)) + list(range(1000, 1005))}


def test_target_without_connected_source_has_no_column():
    mapping = [target("number", ("ds1", "n")), target("gone", ("missing", "n"))]

    result = merge(mapping, TWO_INPUTS)

    assert list(result.columns) == ["number"]
    assert len(result) == 250


def test_no_connected_source_gives_an_empty_result():
    result = merge([target("gone", ("missing", "n"))], {})

    assert result.empty and list(result.columns) == []
