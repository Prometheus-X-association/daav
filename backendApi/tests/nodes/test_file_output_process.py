"""
Unit tests for FileOutput.process: the four file formats, with a DataFrame or a parquet input,
replacing or appending, on the whole data or on a sample.
"""
import datetime
import json
import xml.etree.ElementTree as ET
from unittest.mock import AsyncMock, Mock

import pandas as pd
import pyarrow.parquet as pq
import pytest

from app.core.execution_context import ExecutionContext
from app.enums.status_node import StatusNode
from app.models.interface.dataset_interface import FileDataset
from app.models.interface.node_data import NodeDataPandasDf, NodeDataParquet
from app.nodes.outputs.file_output import FileOutput

pytestmark = pytest.mark.asyncio

ROWS = [{"a": i, "b": f"row{i}", "c": i / 2} for i in range(250)]  # three chunks of 100
OLD_ROWS = [{"a": -2, "b": "old1", "c": 0.5}, {"a": -1, "b": "old2", "c": 1.5}]
NULL_ROWS = [{"a": 1, "b": "x", "c": 1.5}, {"a": 2, "b": None, "c": None}]
DATE_ROWS = [{"a": 1, "d": pd.Timestamp("2026-01-02 03:04:05")}, {"a": 2, "d": pd.Timestamp("2026-11-11 18:30:00")}]
FORMATS = ["csv", "json", "xml", "parquet"]
KINDS = ["dataframe", "parquet"]


def control(value):
    return {"value": value}


# ---------- files: written here without the node, and read back ----------

def write_file(path, file_type, rows):
    df = pd.DataFrame(rows)
    if file_type == "csv":
        df.to_csv(path, index=False)
    elif file_type == "json":
        with open(path, "w", encoding="utf-8") as f:
            json.dump(rows, f)
    elif file_type == "xml":
        df.to_xml(path, index=False, parser="etree")
    else:
        df.to_parquet(path)


def read_file(path, file_type):
    """Rows of a file; XML values are text, None for an empty element."""
    if file_type == "csv":
        return pd.read_csv(path).to_dict(orient="records")
    if file_type == "json":
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    if file_type == "xml":
        return [{child.tag: child.text for child in row} for row in ET.parse(path).getroot()]
    return pd.read_parquet(path).to_dict(orient="records")


def as_read(rows, file_type):
    if file_type == "xml":
        return [{key: str(value) for key, value in row.items()} for row in rows]
    return rows


# ---------- node ----------

def connected_input(node_data):
    node_input = Mock()
    node_input.get_connected_node.return_value = Mock()
    node_input.get_node_data.return_value = node_data
    return node_input


def unconnected_input():
    node_input = Mock()
    node_input.get_connected_node.return_value = None
    return node_input


def pandas_data(rows=ROWS):
    df = pd.DataFrame(rows)
    return NodeDataPandasDf(nodeSchema=[], data=df, dataExample=df.head(20), name="in")


def parquet_data(tmp_path, rows=ROWS):
    path = str(tmp_path / "in.parquet")
    pd.DataFrame(rows).to_parquet(path)
    return NodeDataParquet(data=path, nodeSchema=pq.ParquetFile(path).schema, name="in")


def input_data(kind, tmp_path, rows=ROWS):
    return pandas_data(rows) if kind == "dataframe" else parquet_data(tmp_path, rows)


def output_to_dataset(node_data, path, file_type, file_exist, **data):
    """A node that writes into the file of an existing dataset."""
    node = FileOutput(id="out", data={"selectDataSource": {"value": "ds1", "list": []}, "fileType": control(file_type),
                                      "fileExist": control(file_exist), **data})
    dataset = Mock(filePath=str(path), metadata=Mock(fileType=file_type))
    node.datasetService = Mock(get_dataset=AsyncMock(return_value=dataset), add_connection=AsyncMock())
    node.inputs = {"in": connected_input(node_data)}
    return node


def output_to_new_file(node_data, file_name, file_type, **data):
    """A node that creates a file, named in the node, in the upload folder.

    As in the frontend, the node has no fileExist control when no dataset is selected.
    """
    node = FileOutput(id="out", data={
        "selectDataSource": {"value": None, "list": []}, "fileName": {"value": file_name, "label": file_name},
        "fileType": control(file_type), **data})
    node.datasetService = Mock(add_connection=AsyncMock())
    node.inputs = {"in": connected_input(node_data)}
    return node


@pytest.fixture
def upload_dir(tmp_path, monkeypatch):
    uploads = tmp_path / "uploads"
    uploads.mkdir()
    monkeypatch.setattr("app.nodes.outputs.file_output.settings.upload_dir", str(uploads))
    return uploads


@pytest.fixture
def user(monkeypatch):
    user = Mock(id="user1", username="bob")
    monkeypatch.setattr(ExecutionContext, "get_user", staticmethod(lambda: user))
    monkeypatch.setattr(ExecutionContext, "get_workflow", staticmethod(lambda: Mock()))
    return user


@pytest.fixture
def no_user(monkeypatch):
    monkeypatch.setattr(ExecutionContext, "get_user", staticmethod(lambda: None))
    monkeypatch.setattr(ExecutionContext, "get_workflow", staticmethod(lambda: None))


# ===========================
# MATRIX
# ===========================

@pytest.mark.parametrize("sample", [False, True], ids=["full", "sample"])
@pytest.mark.parametrize("file_exist", ["replace", "append", None], ids=["replace", "append", "not_set"])
@pytest.mark.parametrize("existing", [True, False], ids=["existing_file", "new_file"])
@pytest.mark.parametrize("file_type", FORMATS)
@pytest.mark.parametrize("kind", KINDS)
async def test_matrix(tmp_path, kind, file_type, existing, file_exist, sample):
    """The file holds the rows of the input (20 for a sample), after the rows it had when appending."""
    path = tmp_path / f"out.{file_type}"
    if existing:
        write_file(path, file_type, OLD_ROWS)
    node = output_to_dataset(input_data(kind, tmp_path), path, file_type, file_exist)

    status = await node.process(sample=sample)

    assert status == StatusNode.Valid, node.statusMessage
    kept = OLD_ROWS if existing and file_exist == "append" else []
    written = ROWS[:20] if sample else ROWS
    assert read_file(path, file_type) == as_read(kept + written, file_type)


@pytest.mark.parametrize("file_type", FORMATS)
@pytest.mark.parametrize("kind", KINDS)
async def test_file_can_be_appended_twice(tmp_path, kind, file_type):
    path = tmp_path / f"out.{file_type}"
    for _ in range(3):
        node = output_to_dataset(input_data(kind, tmp_path, ROWS[:3]), path, file_type, "append")
        assert await node.process() == StatusNode.Valid, node.statusMessage

    assert read_file(path, file_type) == as_read(ROWS[:3] * 3, file_type)


# ===========================
# CSV
# ===========================

@pytest.mark.parametrize("kind", KINDS)
async def test_csv_delimiter_and_encoding(tmp_path, kind):
    path = tmp_path / "out.csv"
    rows = [{"a": 1, "b": "été"}, {"a": 2, "b": "noël"}]
    node = output_to_dataset(input_data(kind, tmp_path, rows), path, "csv", "replace",
                             delimiter=control(";"), encoding=control("latin-1"))

    assert await node.process() == StatusNode.Valid
    assert path.read_bytes().decode("latin-1").splitlines() == ["a;b", "1;été", "2;noël"]


@pytest.mark.parametrize("sample", [False, True], ids=["full", "sample"])
@pytest.mark.parametrize("kind", KINDS)
async def test_csv_header_is_written_once(tmp_path, kind, sample):
    path = tmp_path / "out.csv"
    write_file(path, "csv", OLD_ROWS)
    node = output_to_dataset(input_data(kind, tmp_path, ROWS[:2]), path, "csv", "append")

    assert await node.process(sample=sample) == StatusNode.Valid
    assert path.read_text().splitlines() == ["a,b,c", "-2,old1,0.5", "-1,old2,1.5", "0,row0,0.0", "1,row1,0.5"]


# ===========================
# XML
# ===========================

@pytest.mark.parametrize("file_exist", ["replace", "append"])
@pytest.mark.parametrize("kind", KINDS)
async def test_xml_rows_are_row_elements_of_the_data_root(tmp_path, kind, file_exist):
    path = tmp_path / "out.xml"
    write_file(path, "xml", OLD_ROWS)
    node = output_to_dataset(input_data(kind, tmp_path, ROWS[:3]), path, "xml", file_exist)

    assert await node.process() == StatusNode.Valid
    root = ET.parse(path).getroot()
    assert root.tag == "data"
    assert {row.tag for row in root} == {"row"}
    assert path.read_text().startswith("<?xml version='1.0' encoding='utf-8'?>")


@pytest.mark.parametrize("file_exist", ["replace", "append"])
@pytest.mark.parametrize("kind", KINDS)
async def test_xml_missing_value_is_an_empty_element(tmp_path, kind, file_exist):
    path = tmp_path / "out.xml"
    write_file(path, "xml", OLD_ROWS)
    node = output_to_dataset(input_data(kind, tmp_path, NULL_ROWS), path, "xml", file_exist)

    assert await node.process() == StatusNode.Valid
    assert read_file(path, "xml")[-2:] == [{"a": "1", "b": "x", "c": "1.5"}, {"a": "2", "b": None, "c": None}]
    assert "None" not in path.read_text()
    assert "nan" not in path.read_text()


@pytest.mark.parametrize("file_exist", ["replace", "append"])
@pytest.mark.parametrize("kind", KINDS)
async def test_xml_column_name_is_made_a_valid_element_name(tmp_path, kind, file_exist):
    path = tmp_path / "out.xml"
    write_file(path, "xml", [{"a": 0}])
    rows = [{"my col": "x", "1st": 1, "a/b<c>": 2, "é-t.é_": 3, "xml:lang": 4}]
    node = output_to_dataset(input_data(kind, tmp_path, rows), path, "xml", file_exist)

    assert await node.process() == StatusNode.Valid
    assert read_file(path, "xml")[-1] == {"my_col": "x", "_1st": "1", "a_b_c_": "2", "é-t.é_": "3", "xml_lang": "4"}


async def test_xml_encoding(tmp_path):
    path = tmp_path / "out.xml"
    node = output_to_dataset(pandas_data([{"b": "été"}]), path, "xml", "replace", encoding=control("latin-1"))

    assert await node.process() == StatusNode.Valid
    assert "été" in path.read_bytes().decode("latin-1")
    assert read_file(path, "xml") == [{"b": "été"}]


@pytest.mark.parametrize("kind", KINDS)
async def test_xml_append_to_an_unreadable_file_starts_a_new_document(tmp_path, kind):
    path = tmp_path / "out.xml"
    path.write_text("<data><row>")
    node = output_to_dataset(input_data(kind, tmp_path, ROWS[:2]), path, "xml", "append")

    assert await node.process() == StatusNode.Valid
    assert read_file(path, "xml") == as_read(ROWS[:2], "xml")


# ===========================
# JSON
# ===========================

@pytest.mark.parametrize("file_exist", ["replace", "append"])
@pytest.mark.parametrize("kind", KINDS)
async def test_json_missing_value_is_null(tmp_path, kind, file_exist):
    path = tmp_path / "out.json"
    write_file(path, "json", OLD_ROWS)
    node = output_to_dataset(input_data(kind, tmp_path, NULL_ROWS), path, "json", file_exist)

    assert await node.process() == StatusNode.Valid, node.statusMessage
    assert "NaN" not in path.read_text()
    assert read_file(path, "json")[-2:] == NULL_ROWS


@pytest.mark.parametrize("file_exist", ["replace", "append"])
@pytest.mark.parametrize("kind", KINDS)
async def test_json_date_is_iso_8601_text(tmp_path, kind, file_exist):
    path = tmp_path / "out.json"
    write_file(path, "json", [{"a": 0, "d": "2025-12-31T00:00:00"}])
    rows = DATE_ROWS + [{"a": 3, "d": None}]
    node = output_to_dataset(input_data(kind, tmp_path, rows), path, "json", file_exist)

    assert await node.process() == StatusNode.Valid, node.statusMessage
    assert read_file(path, "json")[-3:] == [{"a": 1, "d": "2026-01-02T03:04:05"}, {"a": 2, "d": "2026-11-11T18:30:00"},
                                            {"a": 3, "d": None}]


@pytest.mark.parametrize("file_exist", ["replace", "append"])
@pytest.mark.parametrize("kind", KINDS)
async def test_json_day_is_iso_8601_text(tmp_path, kind, file_exist):
    path = tmp_path / "out.json"
    rows = [{"a": 1, "day": datetime.date(2026, 1, 2)}, {"a": 2, "day": None}]
    node = output_to_dataset(input_data(kind, tmp_path, rows), path, "json", file_exist)

    assert await node.process() == StatusNode.Valid, node.statusMessage
    assert read_file(path, "json") == [{"a": 1, "day": "2026-01-02"}, {"a": 2, "day": None}]


@pytest.mark.parametrize("kind", KINDS)
async def test_json_of_an_empty_input_is_an_empty_list(tmp_path, kind):
    path = tmp_path / "out.json"
    node = output_to_dataset(input_data(kind, tmp_path, pd.DataFrame({"a": pd.Series([], dtype="int64")})), path,
                             "json", "replace")

    assert await node.process() == StatusNode.Valid, node.statusMessage
    assert read_file(path, "json") == []


@pytest.mark.parametrize("kind", KINDS)
async def test_json_keeps_non_ascii_text(tmp_path, kind):
    path = tmp_path / "out.json"
    node = output_to_dataset(input_data(kind, tmp_path, [{"b": "été"}]), path, "json", "replace")

    assert await node.process() == StatusNode.Valid
    assert "été" in path.read_text(encoding="utf-8")


@pytest.mark.parametrize("content", ["not json", '{"a": 1}'], ids=["unreadable", "not_a_list"])
@pytest.mark.parametrize("kind", KINDS)
async def test_json_append_to_a_file_without_list_starts_a_new_list(tmp_path, kind, content):
    path = tmp_path / "out.json"
    path.write_text(content)
    node = output_to_dataset(input_data(kind, tmp_path, ROWS[:2]), path, "json", "append")

    assert await node.process() == StatusNode.Valid
    assert read_file(path, "json") == ROWS[:2]


# ===========================
# DATES IN THE OTHER FORMATS
# ===========================

@pytest.mark.parametrize("file_exist", ["replace", "append"])
@pytest.mark.parametrize("file_type", ["csv", "xml", "parquet"])
@pytest.mark.parametrize("kind", KINDS)
async def test_date_column_is_written(tmp_path, kind, file_type, file_exist):
    path = tmp_path / f"out.{file_type}"
    write_file(path, file_type, [{"a": 0, "d": pd.Timestamp("2025-12-31")}])
    node = output_to_dataset(input_data(kind, tmp_path, DATE_ROWS), path, file_type, file_exist)

    assert await node.process() == StatusNode.Valid, node.statusMessage
    rows = read_file(path, file_type)
    assert len(rows) == (3 if file_exist == "append" else 2)
    assert str(rows[-1]["d"]) == "2026-11-11 18:30:00"


# ===========================
# NEW FILE AND NEW DATASET
# ===========================

@pytest.mark.parametrize("file_type", FORMATS)
@pytest.mark.parametrize("kind", KINDS)
async def test_new_file_matrix(tmp_path, upload_dir, user, kind, file_type):
    node = output_to_new_file(input_data(kind, tmp_path), "report", file_type)

    assert await node.process() == StatusNode.Valid, node.statusMessage
    assert read_file(upload_dir / "user1" / f"report.{file_type}", file_type) == as_read(ROWS, file_type)
    assert node.datasetService.add_connection.await_args.args[0].metadata.fileType == file_type


@pytest.mark.parametrize("kind", KINDS)
async def test_new_file_is_written_in_the_user_folder_and_registered(tmp_path, upload_dir, user, kind):
    node = output_to_new_file(input_data(kind, tmp_path, ROWS[:3]), "report", "csv", delimiter=control(";"))

    assert await node.process() == StatusNode.Valid, node.statusMessage
    path = upload_dir / "user1" / "report.csv"
    assert path.read_text().splitlines() == ["a;b;c", "0;row0;0.0", "1;row1;0.5", "2;row2;1.0"]

    node.datasetService.add_connection.assert_awaited_once()
    new_dataset, owner = node.datasetService.add_connection.await_args.args
    assert owner is user
    assert isinstance(new_dataset, FileDataset)
    assert (new_dataset.name, new_dataset.filePath, new_dataset.type) == ("report", str(path), "file")
    assert (new_dataset.csvDelimiter, new_dataset.encoding, new_dataset.inputType) == (";", "utf-8", "file")
    assert new_dataset.metadata.fileType == "csv"
    assert node.data["selectDataSource"] == {"value": new_dataset.id,
                                             "list": [{"value": new_dataset.id, "label": "report"}]}
    assert node.data["fileName"] == {"value": None, "label": None}


@pytest.mark.parametrize("kind", KINDS)
async def test_new_json_file_has_no_csv_delimiter(tmp_path, upload_dir, user, kind):
    node = output_to_new_file(input_data(kind, tmp_path, ROWS[:3]), "report.json", "json")

    assert await node.process() == StatusNode.Valid, node.statusMessage
    assert read_file(upload_dir / "user1" / "report.json", "json") == ROWS[:3]
    new_dataset = node.datasetService.add_connection.await_args.args[0]
    assert (new_dataset.name, new_dataset.csvDelimiter, new_dataset.metadata.fileType) == ("report", None, "json")


@pytest.mark.parametrize("kind", KINDS)
async def test_without_user_the_file_is_written_but_no_dataset_is_registered(tmp_path, upload_dir, no_user, kind):
    node = output_to_new_file(input_data(kind, tmp_path, ROWS[:3]), "report", "csv")

    assert await node.process() == StatusNode.Valid, node.statusMessage
    assert read_file(upload_dir / "report.csv", "csv") == ROWS[:3]
    node.datasetService.add_connection.assert_not_called()
    assert node.data["selectDataSource"] == {"value": None, "list": []}
    assert node.data["fileName"] == {"value": "report", "label": "report"}


@pytest.mark.parametrize("kind", KINDS)
async def test_new_file_written_twice_is_replaced(tmp_path, upload_dir, no_user, kind):
    for rows in (ROWS[:3], ROWS[5:7]):
        node = output_to_new_file(input_data(kind, tmp_path, rows), "report", "csv")
        assert await node.process() == StatusNode.Valid

    assert read_file(upload_dir / "report.csv", "csv") == ROWS[5:7]


@pytest.mark.parametrize("kind", KINDS)
async def test_existing_dataset_is_not_registered_again(tmp_path, user, kind):
    path = tmp_path / "out.csv"
    node = output_to_dataset(input_data(kind, tmp_path, ROWS[:3]), path, "csv", "replace")

    assert await node.process() == StatusNode.Valid
    node.datasetService.add_connection.assert_not_called()
    assert node.data["selectDataSource"] == {"value": "ds1", "list": []}


@pytest.mark.parametrize("kind", KINDS)
async def test_registration_failure_is_a_node_error(tmp_path, upload_dir, user, kind):
    node = output_to_new_file(input_data(kind, tmp_path, ROWS[:3]), "report", "csv")
    node.datasetService.add_connection.side_effect = RuntimeError("database is down")

    assert await node.process() == StatusNode.Error
    assert node.statusMessage == "database is down"
    assert node.data["fileName"] == {"value": "report", "label": "report"}


# ===========================
# ERRORS AND INPUTS
# ===========================

@pytest.mark.parametrize("kind", KINDS)
async def test_file_type_different_from_the_dataset(tmp_path, kind):
    path = tmp_path / "out.csv"
    node = output_to_dataset(input_data(kind, tmp_path), path, "csv", "replace")
    node.data["fileType"] = control("json")

    assert await node.process() == StatusNode.Error
    assert node.statusMessage == "Output type 'json' does not match dataset type 'csv'"
    assert "ValueError" in "".join(node.errorStackTrace)
    assert not path.exists()


@pytest.mark.parametrize("kind", KINDS)
async def test_unsupported_file_type(tmp_path, kind):
    path = tmp_path / "out.yaml"
    node = output_to_dataset(input_data(kind, tmp_path), path, "yaml", "replace")

    assert await node.process() == StatusNode.Error
    assert node.statusMessage == "Unsupported file type: yaml"
    assert not path.exists()


@pytest.mark.parametrize("kind", KINDS)
async def test_unsupported_file_type_registers_no_dataset(tmp_path, upload_dir, user, kind):
    node = output_to_new_file(input_data(kind, tmp_path), "report", "yaml")

    assert await node.process() == StatusNode.Error
    assert node.statusMessage == "Unsupported file type: yaml"
    assert list((upload_dir / "user1").iterdir()) == []
    node.datasetService.add_connection.assert_not_called()
    assert node.data["fileName"] == {"value": "report", "label": "report"}


async def test_unsupported_data_type(tmp_path):
    node = output_to_dataset(object(), tmp_path / "out.csv", "csv", "replace")

    assert await node.process() == StatusNode.Error
    assert node.statusMessage == "Unsupported data type: <class 'object'>"
    assert "TypeError" in "".join(node.errorStackTrace)


async def test_missing_dataframe(tmp_path):
    node_data = NodeDataPandasDf(nodeSchema=[], dataExample=pd.DataFrame(ROWS), name="in")
    node = output_to_dataset(node_data, tmp_path / "out.csv", "csv", "replace")

    assert await node.process() == StatusNode.Error
    assert node.statusMessage == "Input data is not a pandas DataFrame"


async def test_neither_dataset_nor_file_name():
    node = FileOutput(id="out", data={"fileType": control("csv")})
    node.datasetService = Mock()
    node.inputs = {"in": connected_input(pandas_data())}

    assert await node.process() == StatusNode.Error
    assert node.statusMessage == "Either a data source must be selected or a filename must be provided"
    assert "ValueError" in "".join(node.errorStackTrace)


@pytest.mark.parametrize("kind", KINDS)
async def test_only_the_first_connected_input_is_written(tmp_path, kind):
    path = tmp_path / "out.csv"
    node = output_to_dataset(None, path, "csv", "append")
    node.inputs = {"free": unconnected_input(), "in": connected_input(input_data(kind, tmp_path, ROWS[:2])),
                   "in2": connected_input(pandas_data(ROWS[5:7]))}

    assert await node.process() == StatusNode.Valid
    assert read_file(path, "csv") == ROWS[:2]


async def test_no_connected_input_writes_nothing(tmp_path):
    path = tmp_path / "out.csv"
    node = output_to_dataset(pandas_data(), path, "csv", "replace")
    node.inputs = {"free": unconnected_input()}

    assert await node.process() == StatusNode.Valid
    assert not path.exists()
