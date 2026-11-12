"""
The rule of the merge node: each target column holds its sources end to end, and a target column shorter than
the longest one is completed with missing values.
"""
from unittest.mock import Mock

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from app.enums.status_node import StatusNode
from app.models.interface.node_data import NodeDataPandasDf, NodeDataParquet
from app.nodes.transforms.merge_transform import MergeTransform


def frame(start, count, prefix="r"):
    return pd.DataFrame({"n": range(start, start + count), "s": [f"{prefix}{i}" for i in range(start, start + count)]})


def pandas_data(df, sample_rows=20):
    return NodeDataPandasDf(nodeSchema=[], data=df, dataExample=df.head(sample_rows), name="in")


def parquet_data(tmp_path, name, df, group_sizes=None):
    """A parquet file; its row groups have exactly the given sizes, else it has one row group."""
    path = str(tmp_path / f"{name}.parquet")
    table = pa.Table.from_pandas(df, preserve_index=False)
    with pq.ParquetWriter(path, table.schema) as writer:
        start = 0
        for size in group_sizes or [len(df)]:
            writer.write_table(table.slice(start, size))
            start += size
    assert pq.ParquetFile(path).metadata.num_rows == len(df)
    return NodeDataParquet(data=path, nodeSchema=pq.ParquetFile(path).schema, name=name)


def with_nulls(count, null_from, null_to):
    """A frame whose two columns are missing in the given rows."""
    df = frame(0, count)
    df["n"] = df["n"].astype("float64")
    df.loc[null_from:null_to - 1, ["n", "s"]] = None
    return df


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


# ===========================
# PARQUET OPTION: THE FILE HOLDS THE SAME ROWS AS THE IN-MEMORY MERGE
# ===========================

RENAME = [target("number", ("ds1", "n")), target("label", ("ds1", "s"))]
STACK = [target("number", ("ds1", "n"), ("ds2", "n")), target("label", ("ds1", "s"), ("ds2", "s"))]
MIXED = [target("short", ("ds2", "s")), target("stacked", ("ds1", "n"), ("ds2", "n"), ("ds3", "n")),
         target("label", ("ds3", "s"), ("ds1", "s"))]


def assert_same_as_in_memory(mapping, inputs, sample=False):
    expected = values(merge(mapping, inputs, parquet_save=False, sample=sample))
    assert values(merge(mapping, inputs, parquet_save=True, sample=sample)) == expected
    return expected


def test_parquet_output_file_and_node_data(upload_dir):
    node = merge_node(RENAME, {"ds1": pandas_data(frame(0, 250))}, parquet_save=True)

    assert node.process() == StatusNode.Valid
    node_data = node.outputs["out"].set_node_data.call_args.args[0]
    node.outputs["out"].set_node_data.assert_called_once_with(node_data, node)
    assert node_data.data == str(upload_dir / "merged_data_merge1.parquet")
    assert node_data.name == "merged_data"
    assert node_data.nodeSchema.names == ["number", "label"]
    parquet_file = pq.ParquetFile(node_data.data)
    assert [parquet_file.metadata.row_group(i).num_rows for i in range(parquet_file.num_row_groups)] == [100, 100, 50]
    assert str(parquet_file.schema_arrow.field("number").type) == "int64"


def test_parquet_dataframe_over_several_batches():
    expected = assert_same_as_in_memory(RENAME, {"ds1": pandas_data(frame(0, 250))})
    assert expected["number"] == list(range(250))


@pytest.mark.parametrize("group_sizes", [None, [50] * 6, [100, 100, 50], [50, 50, 30], [30] * 8 + [10], [70, 70, 70, 40],
                                         [10, 240], [1, 99, 1, 149], [250, 1]],
                         ids=lambda sizes: "-".join(str(size) for size in sizes) if sizes else "one_group")
def test_parquet_source_with_any_row_groups(tmp_path, group_sizes):
    count = sum(group_sizes) if group_sizes else 250
    inputs = {"ds1": parquet_data(tmp_path, "a", frame(0, count), group_sizes)}

    expected = assert_same_as_in_memory(RENAME, inputs)

    assert expected["number"] == list(range(count))
    assert expected["label"] == [f"r{i}" for i in range(count)]


@pytest.mark.parametrize("first, second", [(3, 3), (250, 250), (50, 250), (250, 50), (100, 100), (99, 101), (1, 300)])
@pytest.mark.parametrize("kinds", ["dataframe+dataframe", "parquet+parquet", "dataframe+parquet", "parquet+dataframe"])
def test_parquet_sources_are_put_end_to_end(tmp_path, kinds, first, second):
    def node_data(kind, name, df):
        return pandas_data(df) if kind == "dataframe" else parquet_data(tmp_path, name, df, [30] * (len(df) // 30) + [len(df) % 30])

    first_kind, second_kind = kinds.split("+")
    inputs = {"ds1": node_data(first_kind, "a", frame(0, first)), "ds2": node_data(second_kind, "b", frame(1000, second))}

    expected = assert_same_as_in_memory(STACK, inputs)

    assert expected["number"] == list(range(first)) + list(range(1000, 1000 + second))


def test_parquet_mixed_sources_of_different_lengths(tmp_path):
    inputs = {"ds1": pandas_data(frame(0, 130)), "ds2": parquet_data(tmp_path, "b", frame(1000, 45), [10, 35]),
              "ds3": parquet_data(tmp_path, "c", frame(5000, 270, "p"), [100, 100, 70])}

    expected = assert_same_as_in_memory(MIXED, inputs)

    assert expected["stacked"] == list(range(130)) + list(range(1000, 1045)) + list(range(5000, 5270))
    assert expected["short"] == [f"r{i}" for i in range(1000, 1045)] + [None] * 400
    assert expected["label"][268:272] == ["p5268", "p5269", "r0", "r1"]
    assert len(expected["label"]) == 445 and expected["label"][400:] == [None] * 45


def test_parquet_shorter_target_column_is_completed(tmp_path):
    for mapping in ([target("long", ("ds1", "n")), target("short", ("ds2", "n"))],
                    [target("short", ("ds2", "n")), target("long", ("ds1", "n"))]):
        inputs = {"ds1": pandas_data(frame(0, 250)), "ds2": parquet_data(tmp_path, "b", frame(1000, 50))}
        expected = assert_same_as_in_memory(mapping, inputs)
        assert expected["short"] == list(range(1000, 1050)) + [None] * 200


@pytest.mark.parametrize("null_from, null_to", [(0, 100), (0, 150), (100, 200), (200, 250), (120, 130), (0, 250)],
                         ids=["first_batch", "first_batches", "second_batch", "last_batch", "inside_a_batch", "everywhere"])
@pytest.mark.parametrize("kind", ["dataframe", "parquet"])
def test_parquet_column_entirely_null_in_a_batch(tmp_path, kind, null_from, null_to):
    df = with_nulls(250, null_from, null_to)
    inputs = {"ds1": pandas_data(df) if kind == "dataframe" else parquet_data(tmp_path, "a", df, [50] * 5)}

    expected = assert_same_as_in_memory(RENAME, inputs)

    assert expected["number"][null_from:null_to] == [None] * (null_to - null_from)
    assert expected["label"][null_from:null_to] == [None] * (null_to - null_from)
    assert len(expected["number"]) == 250


def test_parquet_integer_then_float_sources_give_a_float_column(tmp_path):
    floats = pd.DataFrame({"n": [0.5, 1.5, None]})
    inputs = {"ds1": pandas_data(frame(0, 150)), "ds2": parquet_data(tmp_path, "b", floats)}

    expected = assert_same_as_in_memory([target("number", ("ds1", "n"), ("ds2", "n"))], inputs)

    assert expected["number"] == list(range(150)) + [0.5, 1.5, None]


def test_parquet_dates_and_text(tmp_path):
    df = pd.DataFrame({"d": pd.date_range("2026-01-01", periods=130, freq="h"), "s": ["été"] * 130})
    inputs = {"ds1": pandas_data(df), "ds2": parquet_data(tmp_path, "b", df, [100, 30])}

    expected = assert_same_as_in_memory([target("day", ("ds1", "d"), ("ds2", "d")), target("text", ("ds2", "s"))], inputs)

    assert expected["day"][129] == pd.Timestamp("2026-01-06 09:00:00") and len(expected["day"]) == 260


def test_parquet_sample(tmp_path):
    inputs = {"ds1": pandas_data(frame(0, 250), sample_rows=20), "ds2": pandas_data(frame(1000, 50), sample_rows=5),
              "ds3": parquet_data(tmp_path, "c", frame(5000, 120), [50, 50, 20])}

    expected = assert_same_as_in_memory(MIXED, inputs, sample=True)

    # A parquet source is read entirely, in both modes
    assert expected["stacked"] == list(range(20)) + list(range(1000, 1005)) + list(range(5000, 5120))


def test_parquet_source_of_an_unconnected_dataset_is_ignored():
    mapping = [target("number", ("ds1", "n"), ("gone", "n")), target("nothing", ("gone", "n"))]

    expected = assert_same_as_in_memory(mapping, {"ds1": pandas_data(frame(0, 250))})

    assert list(expected) == ["number"]


@pytest.mark.parametrize("kind", ["dataframe", "parquet"])
def test_parquet_empty_input_gives_an_empty_file(tmp_path, kind):
    inputs = {"ds1": pandas_data(frame(0, 0)) if kind == "dataframe" else parquet_data(tmp_path, "a", frame(0, 0))}

    result = merge(RENAME, inputs, parquet_save=True)

    assert list(result.columns) == ["number", "label"] and len(result) == 0


def test_parquet_no_connected_source_gives_an_empty_file():
    result = merge([target("gone", ("missing", "n"))], {}, parquet_save=True)

    assert result.empty and list(result.columns) == []


def test_parquet_file_of_a_previous_run_is_replaced(upload_dir):
    merge(RENAME, {"ds1": pandas_data(frame(0, 250))}, parquet_save=True)

    result = merge(RENAME, {"ds1": pandas_data(frame(0, 0))}, parquet_save=True)

    assert len(result) == 0
    assert pq.ParquetFile(upload_dir / "merged_data_merge1.parquet").metadata.num_rows == 0


def test_parquet_sources_of_types_that_cannot_be_merged():
    inputs = {"ds1": pandas_data(frame(0, 3)), "ds2": pandas_data(frame(10, 3))}
    node = merge_node([target("mixed", ("ds1", "n"), ("ds2", "s"))], inputs, parquet_save=True)

    assert node.process() == StatusNode.Error
    assert node.statusMessage == ("The sources of column 'mixed' have types that cannot be merged in a parquet file: "
                                  "int64, string")
    assert "ValueError" in "".join(node.errorStackTrace)


def test_parquet_unknown_input_type():
    node = merge_node(RENAME, {"ds1": object()}, parquet_save=True)

    assert node.process() == StatusNode.Error
    assert node.statusMessage == "Unkown input type"
    assert "TypeError" in "".join(node.errorStackTrace)
