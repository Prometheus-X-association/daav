"""
Reference tests for the folder reader and the pandas schema generation.
"""
import base64
from datetime import datetime
import json
import os
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

from app.models.interface.dataset_interface import FileContentResponse, Pagination
from app.utils.utils import folder, generate_pandas_schema


# ===========================
# folder
# ===========================

@pytest.fixture
def files_dir(tmp_path):
    (tmp_path / "data.yaml").write_text("config:\n  debug: true\n  port: 8080\n")
    (tmp_path / "data.yml").write_text("- a\n- b\n")
    (tmp_path / "data.xml").write_text("<root><a>1</a></root>")
    (tmp_path / "schema.xsd").write_text("<xs:schema/>")
    (tmp_path / "notes.md").write_text("# Title")
    (tmp_path / "broken.json").write_text("{not json")
    (tmp_path / "broken.yaml").write_text("a: [1, 2\n")
    (tmp_path / "latin1.txt").write_bytes("caf\xe9".encode("latin-1"))
    (tmp_path / "image.png").write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * 100)
    (tmp_path / "blob.bin").write_bytes(b"\x00\x01\x02")
    (tmp_path / "noext").write_text("plain text without extension")
    return tmp_path


def _by_name(result):
    return {item["file"]: item for item in result}


def test_folder_reads_each_file_type(files_dir):
    with patch("app.utils.utils.settings.max_file_size", 10_000):
        result = _by_name(folder(str(files_dir)))

    assert set(result) == {"data.yaml", "data.yml", "data.xml", "schema.xsd", "notes.md", "broken.json",
                           "broken.yaml", "latin1.txt", "image.png", "blob.bin", "noext"}
    assert result["data.yaml"]["content"] == {"config": {"debug": True, "port": 8080}}
    assert result["data.yml"]["content"] == ["a", "b"]
    assert result["data.xml"]["content"] == "<root><a>1</a></root>"
    assert result["schema.xsd"]["content"] == "<xs:schema/>"
    assert result["notes.md"]["content"] == "# Title"
    assert result["noext"]["content"] == "plain text without extension"
    png = (files_dir / "image.png").read_bytes()
    assert result["image.png"]["media"] == base64.b64encode(png).decode("utf-8")
    assert result["image.png"]["content"] is None
    assert result["blob.bin"]["content"] is None
    assert result["blob.bin"]["media"] is None
    for item in result.values():
        assert item["folder"] == str(files_dir)
        assert item["path"] == os.path.join(str(files_dir), item["file"])
        assert set(item) == {"media", "path", "folder", "file", "mime_type", "size", "created", "modified", "content"}


def test_folder_keeps_unparsable_files_without_content(files_dir, capsys):
    result = _by_name(folder(str(files_dir)))

    assert result["broken.json"]["content"] is None
    assert result["broken.yaml"]["content"] is None
    assert result["latin1.txt"]["content"] is None
    output = capsys.readouterr().out
    assert "Error opening JSON file broken.json" in output
    assert "Error opening YAML file broken.yaml" in output
    assert "Error opening text file latin1.txt" in output


def test_folder_media_above_the_maximum_size(files_dir, capsys):
    with patch("app.utils.utils.settings.max_file_size", 10):
        result = _by_name(folder(str(files_dir)))

    assert result["image.png"]["media"] is None
    assert "Media file image.png too large" in capsys.readouterr().out


def test_folder_media_read_error(files_dir, capsys):
    real_open = open

    def failing_open(path, mode="r", *args, **kwargs):
        if str(path).endswith("image.png") and "b" in mode:
            raise OSError("disk error")
        return real_open(path, mode, *args, **kwargs)

    with patch("builtins.open", side_effect=failing_open):
        result = _by_name(folder(str(files_dir)))

    assert result["image.png"]["media"] is None
    assert "Error during base64 conversion of media file image.png: disk error" in capsys.readouterr().out


def test_folder_metadata(tmp_path):
    path = tmp_path / "a.json"
    path.write_text(json.dumps({"k": 1}))
    os.utime(path, (1640995200, 1640995200))

    item = folder(str(tmp_path))[0]

    assert item["content"] == {"k": 1}
    assert item["mime_type"] == "application/json"
    assert item["size"] == "8.0 B"
    assert item["modified"] == str(datetime.fromtimestamp(1640995200))
    assert "+00:00" not in item["created"]
    assert len(item["created"]) == 19


def test_folder_unreadable_file_is_skipped_but_counted(tmp_path, capsys):
    (tmp_path / "ok.txt").write_text("ok")
    locked = tmp_path / "locked.json"
    locked.write_text("{}")
    locked.chmod(0)
    try:
        response = folder(str(tmp_path), Pagination(page=1, perPage=10))
    finally:
        locked.chmod(0o644)

    assert [item["file"] for item in response.data] == ["ok.txt"]
    assert response.total_rows == 2
    assert "Access error to" in capsys.readouterr().out


def test_folder_unreadable_subfolder(tmp_path, capsys):
    (tmp_path / "ok.txt").write_text("ok")
    locked = tmp_path / "locked"
    locked.mkdir()
    (locked / "inner.txt").write_text("x")
    locked.chmod(0)
    try:
        result = folder(str(tmp_path))
    finally:
        locked.chmod(0o755)

    assert [item["file"] for item in result] == ["ok.txt"]
    assert "Access error to folder" in capsys.readouterr().out


def test_folder_pages(tmp_path):
    for i in range(3):
        (tmp_path / f"f{i}.txt").write_text(str(i))
    sub = tmp_path / "sub"
    sub.mkdir()
    for i in range(2):
        (sub / f"s{i}.txt").write_text(str(i))

    all_files = [item["file"] for item in folder(str(tmp_path))]
    pages = [folder(str(tmp_path), Pagination(page=page, perPage=2)) for page in (1, 2, 3, 4)]

    assert len(all_files) == 5
    for page in pages:
        assert isinstance(page, FileContentResponse)
        assert page.total_rows == 5
        assert page.limit == 2
    assert [page.current_page for page in pages] == [1, 2, 3, 4]
    assert [[item["file"] for item in page.data] for page in pages] == [
        all_files[0:2], all_files[2:4], all_files[4:5], []]


def test_folder_access_denied(tmp_path):
    with patch("app.utils.security.FileAccessController.can_read_file", return_value=False):
        with pytest.raises(PermissionError, match="Access denied to directory"):
            folder(str(tmp_path))


# ===========================
# generate_pandas_schema
# ===========================

def _col(name, dtype, nullable=False, count=1, nested=None):
    return {"name": name, "dtype": dtype, "nullable": nullable, "count": count, "nested": nested}


SCHEMA_CORPUS = {
    "simple_columns": (
        pd.DataFrame({"a": [1, 2, None], "b": ["x", "y", "z"], "c": [True, False, True]}),
        [_col("a", "float", True, 3), _col("b", "str", False, 3), _col("c", "bool", False, 3)],
    ),
    "nested_dicts": (
        pd.DataFrame([{"id": 1, "addr": {"city": "P", "geo": {"lat": 1.5}}},
                      {"id": 2, "addr": {"city": "L", "geo": {"lat": 2.5}}}]),
        [_col("id", "int", count=2),
         _col("addr", "str", count=2, nested=[
             _col("city", "str"),
             _col("geo", "dict", nested=[_col("lat", "float")])])],
    ),
    "list_of_objects": (
        pd.DataFrame([{"id": 1, "items": [{"sku": "a", "q": 1}]}, {"id": 2, "items": []}]),
        [_col("id", "int", count=2),
         _col("items", "str", count=2, nested=[_col("sku", "str"), _col("q", "int")])],
    ),
    "list_of_scalars": (
        pd.DataFrame([{"id": 1, "tags": ["a", "b"]}, {"id": 2, "tags": ["c"]}]),
        [_col("id", "int", count=2),
         _col("tags", "Array[str]", count=2, nested=[_col("#value", "Array[str]")])],
    ),
    "empty_dataframe": (pd.DataFrame(), []),
    "empty_dataframe_with_columns": (
        pd.DataFrame({"a": pd.Series([], dtype=object), "n": pd.Series([], dtype="int64")}),
        [_col("a", "str", count=0, nested=[]), _col("n", "int", count=0, nested=[])],
    ),
    "all_null_column": (
        pd.DataFrame({"a": [None, None], "b": [1, 2]}),
        [_col("a", "str", True, 2), _col("b", "int", count=2)],
    ),
    "all_nan_column": (pd.DataFrame({"a": [np.nan, np.nan]}), [_col("a", "float", True, 2)]),
    "named_index": (
        pd.DataFrame({"a": [1, 2]}, index=pd.Index(["x", "y"], name="key")),
        [_col("a", "int", count=2, nested=[_col("#array_item#", "int", count=2)])],
    ),
    "offset_range_index": (
        pd.DataFrame({"a": [1, 2]}, index=pd.RangeIndex(5, 7)),
        [_col("a", "int", count=2, nested=[_col("#array_item#", "int", count=2)])],
    ),
    "filtered_dataframe": (
        pd.DataFrame({"a": [1, 2]}).query("a > 5"),
        [_col("a", "int", count=0, nested=[])],
    ),
    "dict": (
        {"a": 1, "b": None, "c": {"d": [{"e": 1}]}, "f": [1, 2], "g": []},
        [_col("a", "int"), _col("b", "NoneType", True, 0),
         _col("c", "dict", nested=[_col("d", "list", nested=[_col("e", "int")])]),
         _col("f", "list"), _col("g", "list")],
    ),
    "dict_with_pandas_values": (
        {"x": pd.DataFrame({"a": [1]}), "s": pd.Series([1])},
        [_col("x", "DataFrame", nested=[_col("a", "int")]),
         _col("s", "int", nested=[_col("#array_item#", "int")])],
    ),
    "series_of_scalars": (pd.Series([1, 2, 3]), [_col("#array_item#", "int", count=3)]),
    "empty_series": (pd.Series([], dtype=float), []),
    "series_all_null": (pd.Series([None, None]), [_col("#array_item#", "str", True, 0)]),
    "series_of_dicts": (pd.Series([{"a": 1}, {"a": 2}]), [_col("a", "int")]),
    "series_first_value_null": (pd.Series([None, {"a": 1}]), [_col("a", "int")]),
    "series_of_lists": (pd.Series([[1, 2], [3]]), [_col("#value", "Array[int]")]),
    "series_with_labels": (
        pd.Series({"x": {"a": 1}, "y": None, "z": [1, 2], "w": [{"k": 1}]}),
        [_col("x", "dict", nested=[_col("a", "int")]),
         _col("y", "NaN", True, 0),
         _col("#value", "Array[int]"),
         _col("w", "list", nested=[_col("k", "int")])],
    ),
    "series_with_labels_and_empty_list": (
        pd.Series({"x": [], "y": {"a": 1}}),
        [_col("x", "list"), _col("y", "dict", nested=[_col("a", "int")])],
    ),
}


@pytest.mark.parametrize("data, expected", SCHEMA_CORPUS.values(), ids=SCHEMA_CORPUS.keys())
def test_generate_pandas_schema_reference(data, expected):
    assert generate_pandas_schema(data).model_dump() == expected


def test_generate_pandas_schema_of_other_types():
    assert generate_pandas_schema([1, 2]).model_dump() == []
    assert generate_pandas_schema(None).model_dump() == []
