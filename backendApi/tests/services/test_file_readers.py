"""
Tests for the file readers: get_file_content and csv_file (routes/datasets.py),
DatasetService.getDfFileContentData and DatasetService._process_file_dataset.
"""
import base64
import json
from unittest.mock import patch

import pandas as pd
import pyarrow as pa
import pyarrow.feather as pf
import pyarrow.orc as po
import pytest
from fastapi import HTTPException
from fastavro import parse_schema, writer

from app.models.interface.dataset_interface import FileContentResponse, FileDataset, Pagination
from app.routes.datasets import csv_file, get_file_content
from app.services.dataset_service import DatasetService

ROWS = [{"name": "a", "age": 10}, {"name": "b", "age": 20}, {"name": "c", "age": 30}]


def _dataset(path=None, folder=None, header="0", delimiter=",", name="ds"):
    return FileDataset.model_construct(id="ds1", type="file", name=name, filePath=path, folder=folder,
                                       csvHeader=header, csvDelimiter=delimiter, metadata=None)


def _write(path, rows=ROWS):
    """Write the rows in the format given by the file extension."""
    suffix = path.suffix
    df = pd.DataFrame(rows)
    if suffix == ".json":
        path.write_text(json.dumps(rows))
    elif suffix == ".csv":
        df.to_csv(path, index=False)
    elif suffix == ".tsv":
        df.to_csv(path, index=False, sep="\t")
    elif suffix == ".parquet":
        df.to_parquet(path)
    elif suffix == ".feather":
        pf.write_feather(pa.Table.from_pandas(df, preserve_index=False), str(path))
    elif suffix == ".orc":
        po.write_table(pa.Table.from_pandas(df, preserve_index=False), str(path))
    elif suffix in (".xlsx",):
        df.to_excel(path, index=False)
    elif suffix == ".avro":
        schema = parse_schema({"type": "record", "name": "r", "fields": [
            {"name": "name", "type": "string"}, {"name": "age", "type": "long"}]})
        with open(path, "wb") as out:
            writer(out, schema, rows)
    elif suffix == ".xml":
        items = "".join(f"<row><name>{r['name']}</name><age>{r['age']}</age></row>" for r in rows)
        path.write_text(f"<rows>{items}</rows>")
    return path


def _http_error(func, *args):
    with pytest.raises(HTTPException) as exc_info:
        func(*args)
    return exc_info.value.status_code, exc_info.value.detail


PAGE_1 = Pagination(page=1, perPage=10)


# ===========================
# get_file_content
# ===========================

class TestGetFileContent:

    @pytest.mark.parametrize("suffix", [".json", ".csv", ".parquet", ".feather", ".orc", ".xlsx", ".avro"])
    def test_tabular_formats(self, tmp_path, suffix):
        path = _write(tmp_path / f"data{suffix}")

        response = get_file_content(_dataset(str(path)), PAGE_1)

        assert isinstance(response, FileContentResponse)
        assert response.data == ROWS
        assert response.total_rows == 3
        assert response.limit == 10

    def test_tsv(self, tmp_path):
        path = _write(tmp_path / "data.tsv")

        assert get_file_content(_dataset(str(path)), PAGE_1).data == ROWS

    def test_xml_values_are_text(self, tmp_path):
        path = _write(tmp_path / "data.xml")

        assert get_file_content(_dataset(str(path)), PAGE_1).data == [
            {"name": r["name"], "age": str(r["age"])} for r in ROWS]

    def test_txt(self, tmp_path):
        path = tmp_path / "notes.txt"
        path.write_text("hello\nworld")

        assert get_file_content(_dataset(str(path)), PAGE_1).data == [{"text": "hello\nworld"}]

    def test_media(self, tmp_path):
        path = tmp_path / "Image.PNG"
        path.write_bytes(b"\x89PNG-data")

        response = get_file_content(_dataset(str(path)), PAGE_1)

        assert response.data == [{
            "media": base64.b64encode(b"\x89PNG-data").decode(),
            "file": "Image.PNG",
            "mime_type": "image/png",
            "size": 9,
            "path": str(path),
        }]
        assert response.total_rows == 1

    def test_media_with_unknown_mime_type(self, tmp_path):
        path = tmp_path / "clip.m4v"
        path.write_bytes(b"data")
        with patch("mimetypes.guess_type", return_value=(None, None)):
            response = get_file_content(_dataset(str(path)), PAGE_1)

        assert response.data[0]["mime_type"] == "application/octet-stream"

    def test_media_too_large_is_a_413(self, tmp_path):
        path = tmp_path / "big.mp3"
        path.write_bytes(b"0" * 20)
        with patch("app.routes.datasets.settings.max_file_size", 10):
            assert _http_error(get_file_content, _dataset(str(path)), PAGE_1) == (
                413, "Media file too large: 20 bytes (max: 10)")

    def test_unsupported_format_is_a_422(self, tmp_path):
        path = tmp_path / "data.bin"
        path.write_bytes(b"x")

        assert _http_error(get_file_content, _dataset(str(path)), PAGE_1) == (
            422, "File format not supported: .bin")

    def test_invalid_json_is_a_422(self, tmp_path):
        path = tmp_path / "data.json"
        path.write_text("{oops")

        status, detail = _http_error(get_file_content, _dataset(str(path)), PAGE_1)

        assert status == 422
        assert detail.startswith("Can't read JSON file: ")

    def test_missing_path_is_a_400(self):
        assert _http_error(get_file_content, _dataset(None), PAGE_1) == (400, "File path is required")
        assert _http_error(get_file_content, _dataset(""), PAGE_1) == (400, "File path is required")

    def test_missing_file_is_a_404(self, tmp_path):
        path = str(tmp_path / "missing.csv")

        assert _http_error(get_file_content, _dataset(path), PAGE_1) == (404, f"File not found: {path}")

    def test_directory_as_file_is_a_400(self, tmp_path):
        assert _http_error(get_file_content, _dataset(str(tmp_path)), PAGE_1) == (
            400, f"Path is not a file: {tmp_path}")

    def test_forbidden_file_is_a_403(self, tmp_path):
        path = _write(tmp_path / "data.csv")
        with patch("app.routes.datasets.FileAccessController.can_read_file", return_value=False):
            assert _http_error(get_file_content, _dataset(str(path)), PAGE_1) == (
                403, f"Permission error: Access denied to directory: {path}")

    def test_dangerous_path_is_refused(self, tmp_path):
        with patch("app.routes.datasets.PathSecurityValidator.validate_file_path",
                   side_effect=HTTPException(status_code=400, detail="Dangerous path pattern detected: x")):
            assert _http_error(get_file_content, _dataset("../x.csv"), PAGE_1) == (
                400, "Dangerous path pattern detected: x")

    def test_unreadable_file_is_a_500(self, tmp_path):
        path = tmp_path / "data.parquet"
        path.write_bytes(b"not a parquet file")

        status, detail = _http_error(get_file_content, _dataset(str(path)), PAGE_1)

        assert status == 500
        assert detail.startswith("Unexpected error: ")

    def test_file_not_found_while_reading_is_a_404(self, tmp_path):
        path = _write(tmp_path / "data.json")
        with patch("app.routes.datasets.json_file", side_effect=FileNotFoundError("gone")):
            assert _http_error(get_file_content, _dataset(str(path)), PAGE_1) == (404, "File not found: gone")
        with patch("app.routes.datasets.json_file", side_effect=NotADirectoryError("nodir")):
            assert _http_error(get_file_content, _dataset(str(path)), PAGE_1) == (
                404, "Directory not found: nodir")
        with patch("app.routes.datasets.json_file", side_effect=PermissionError("denied")):
            assert _http_error(get_file_content, _dataset(str(path)), PAGE_1) == (
                403, "Permission error: denied")

    def test_folder(self, tmp_path):
        for i in range(3):
            (tmp_path / f"f{i}.txt").write_text(str(i))

        response = get_file_content(_dataset(folder=str(tmp_path)), Pagination(page=2, perPage=2))

        assert isinstance(response, FileContentResponse)
        assert response.total_rows == 3
        assert response.current_page == 2
        assert len(response.data) == 1

    def test_folder_is_checked_before_the_file(self, tmp_path):
        path = _write(tmp_path / "data.csv")
        missing = str(tmp_path / "missing")

        assert _http_error(get_file_content, _dataset(str(path), folder=missing), PAGE_1) == (
            404, f"Folder not found: {missing}")
        assert _http_error(get_file_content, _dataset(folder=str(path)), PAGE_1) == (
            400, f"Path is not a directory: {path}")

    def test_forbidden_folder_is_a_403(self, tmp_path):
        with patch("app.utils.security.FileAccessController.can_read_file", return_value=False):
            assert _http_error(get_file_content, _dataset(folder=str(tmp_path)), PAGE_1) == (
                403, f"Permission error: Access denied to directory: {tmp_path}")


# ===========================
# csv_file
# ===========================

class TestCsvFile:

    def test_with_header_and_value_types(self, tmp_path):
        path = tmp_path / "data.csv"
        path.write_text("a,b,c\n1,2.5,true\n-3,1e3,FALSE\nx,,True\n")

        assert csv_file(str(path), "0", ",") == [
            {"a": 1, "b": 2.5, "c": True},
            {"a": -3, "b": 1000.0, "c": False},
            {"a": "x", "b": "", "c": True},
        ]

    def test_without_header(self, tmp_path):
        path = tmp_path / "data.csv"
        path.write_text("1,x\n2,y\n")

        assert csv_file(str(path), "false", ",") == [
            {"None1": 1, "None2": "x"},
            {"None1": 2, "None2": "y"},
        ]

    def test_short_rows_are_filled_with_zero(self, tmp_path):
        path = tmp_path / "data.csv"
        path.write_text("a,b\n1\n")

        assert csv_file(str(path), "0", ",") == [{"a": 1, "b": 0}]

    def test_tsv_uses_tab_unless_the_delimiter_is_empty(self, tmp_path):
        path = tmp_path / "data.tsv"
        path.write_text("a\tb\n1\t2\n")

        assert csv_file(str(path), "0", ";") == [{"a": 1, "b": 2}]
        assert csv_file(str(path), "0", "") == [{"a": 1, "b": 2}]

    def test_empty_delimiter_is_detected(self, tmp_path):
        path = tmp_path / "data.csv"
        path.write_text("a;b\n1;2\n")

        assert csv_file(str(path), "0", "") == [{"a": 1, "b": 2}]
        assert csv_file(str(path), "0", ",") == [{"a;b": "1;2"}]

    def test_limited_to_100_rows(self, tmp_path):
        path = tmp_path / "data.csv"
        path.write_text("n\n" + "\n".join(str(i) for i in range(150)) + "\n")

        rows = csv_file(str(path), "0", ",")

        assert len(rows) == 100
        assert rows[-1] == {"n": 99}


# ===========================
# DatasetService.getDfFileContentData
# ===========================

@pytest.fixture
def service():
    return DatasetService()


class TestGetDfFileContentData:

    @pytest.mark.parametrize("suffix", [".csv", ".json", ".xlsx", ".parquet", ".avro"])
    def test_formats(self, service, tmp_path, suffix):
        path = _write(tmp_path / f"data{suffix}")

        node_data = service.getDfFileContentData(_dataset(str(path), name="my data"))

        assert node_data.name == "my data"
        assert node_data.data.to_dict("records") == ROWS
        assert node_data.dataExample is None
        assert [col.name for col in node_data.nodeSchema.root] == ["name", "age"]

    def test_tsv(self, service, tmp_path):
        path = _write(tmp_path / "data.tsv")

        assert service.getDfFileContentData(_dataset(str(path))).data.to_dict("records") == ROWS

    def test_name_defaults_to_the_file_name(self, service, tmp_path):
        path = _write(tmp_path / "data.json")

        assert service.getDfFileContentData(_dataset(str(path), name=None)).name == "data.json"

    def test_csv_page_2(self, service, tmp_path):
        rows = [{"n": i} for i in range(5)]
        path = _write(tmp_path / "data.csv", rows)

        node_data = service.getDfFileContentData(_dataset(str(path)), Pagination(page=2, perPage=2))

        assert node_data.data is None
        assert node_data.dataExample.to_dict("records") == [{"n": 2}, {"n": 3}]

    def test_csv_with_incomplete_pagination_reads_everything(self, service, tmp_path):
        rows = [{"n": i} for i in range(5)]
        path = _write(tmp_path / "data.csv", rows)

        node_data = service.getDfFileContentData(_dataset(str(path), header=None), Pagination(page=None, perPage=2))

        assert node_data.dataExample.to_dict("records") == rows

    def test_csv_delimiter(self, service, tmp_path):
        path = tmp_path / "data.csv"
        path.write_text("a;b\n1;2\n")

        assert service.getDfFileContentData(_dataset(str(path), delimiter=";")).data.to_dict("records") == [
            {"a": 1, "b": 2}]
        assert service.getDfFileContentData(_dataset(str(path), delimiter="")).data.columns.tolist() == ["a;b"]

    @pytest.mark.parametrize("suffix", [".json", ".parquet", ".tsv"])
    def test_other_formats_page_2(self, service, tmp_path, suffix):
        rows = [{"n": i} for i in range(5)]
        path = _write(tmp_path / f"data{suffix}", rows)

        node_data = service.getDfFileContentData(_dataset(str(path)), Pagination(page=2, perPage=2))

        assert node_data.dataExample.to_dict("records") == [{"n": 2}, {"n": 3}]

    def test_folder(self, service, tmp_path):
        for i in range(3):
            (tmp_path / f"f{i}.txt").write_text(str(i))

        node_data = service.getDfFileContentData(_dataset(folder=str(tmp_path), name="dir"))
        paged = service.getDfFileContentData(_dataset(folder=str(tmp_path)), Pagination(page=2, perPage=2))

        assert sorted(node_data.data["file"]) == ["f0.txt", "f1.txt", "f2.txt"]
        assert len(paged.dataExample) == 1

    def test_folder_errors(self, service, tmp_path):
        missing = str(tmp_path / "missing")
        file_path = _write(tmp_path / "data.csv")

        assert _http_error(service.getDfFileContentData, _dataset(folder=missing)) == (
            404, f"Folder not found: {missing}")
        assert _http_error(service.getDfFileContentData, _dataset(folder=str(file_path))) == (
            400, f"Path is not a directory: {file_path}")

    def test_unsupported_format_is_a_400(self, service, tmp_path):
        path = tmp_path / "data.txt"
        path.write_text("x")

        assert _http_error(service.getDfFileContentData, _dataset(str(path))) == (400, "Unsupported file format")

    def test_missing_path_and_file(self, service, tmp_path):
        assert _http_error(service.getDfFileContentData, _dataset(None)) == (400, "File path is required")
        assert _http_error(service.getDfFileContentData, _dataset(str(tmp_path / "x.csv"))) == (
            404, "File not found")

    def test_forbidden_path_is_a_403(self, service, tmp_path):
        path = _write(tmp_path / "data.csv")
        with patch("app.services.dataset_service.FileAccessController.can_read_file", return_value=False):
            assert _http_error(service.getDfFileContentData, _dataset(str(path))) == (
                403, "Access denied: Invalid or dangerous file path")
        with patch("app.services.dataset_service.PathSecurityValidator.validate_file_path",
                   side_effect=HTTPException(status_code=400, detail="Dangerous")):
            assert _http_error(service.getDfFileContentData, _dataset(str(path))) == (
                403, "Access denied: Invalid or dangerous file path")

    def test_read_errors(self, service, tmp_path):
        path = _write(tmp_path / "data.json")
        with patch("app.services.dataset_service.pd.read_json", side_effect=PermissionError("denied")):
            assert _http_error(service.getDfFileContentData, _dataset(str(path))) == (
                403, "Permission error: denied")
        with patch("app.services.dataset_service.pd.read_json", side_effect=ValueError("bad")):
            assert _http_error(service.getDfFileContentData, _dataset(str(path))) == (
                500, "Internal server error")


# ===========================
# DatasetService._process_file_dataset
# ===========================

class TestProcessFileDataset:

    @pytest.mark.parametrize("suffix, file_type", [
        (".csv", "csv"), (".json", "json"), (".xlsx", "xlsx"), (".parquet", "parquet"),
    ])
    def test_counts_by_format(self, service, tmp_path, suffix, file_type):
        path = _write(tmp_path / f"data{suffix}")

        result = service._process_file_dataset(_dataset(str(path)))

        assert result.metadata.fileType == file_type
        assert (result.metadata.columnCount, result.metadata.rowCount) == ("2", "3")
        assert result.metadata.fileSize.endswith("B")
        assert len(result.metadata.modifTime) == 19 and len(result.metadata.accessTime) == 19

    def test_csv_options(self, service, tmp_path):
        path = tmp_path / "data.csv"
        path.write_text("title\na;b\n1;2\n")

        result = service._process_file_dataset(_dataset(str(path), header="1", delimiter=";"))

        assert (result.metadata.columnCount, result.metadata.rowCount) == ("2", "1")

    @pytest.mark.parametrize("suffix", [".avro", ".tsv", ".txt"])
    def test_other_formats_have_no_counts(self, service, tmp_path, suffix):
        path = tmp_path / f"data{suffix}"
        path.write_text("x")

        result = service._process_file_dataset(_dataset(str(path)))

        assert result.metadata.fileType == suffix[1:]
        assert (result.metadata.columnCount, result.metadata.rowCount) == ("0", "0")

    def test_unreadable_file_has_no_counts(self, service, tmp_path, caplog):
        path = tmp_path / "data.parquet"
        path.write_bytes(b"not parquet")

        result = service._process_file_dataset(_dataset(str(path)))

        assert (result.metadata.columnCount, result.metadata.rowCount) == ("0", "0")
        assert "Error processing file metadata" in caplog.text

    def test_missing_file(self, service, tmp_path, caplog):
        dataset = _dataset(str(tmp_path / "missing.csv"))

        assert service._process_file_dataset(dataset) is dataset
        assert dataset.metadata is None
        assert "File not found for dataset" in caplog.text

    def test_no_file_path(self, service, caplog):
        dataset = _dataset(None, folder="/some/folder")

        assert service._process_file_dataset(dataset).metadata is None
        assert "path not specified" in caplog.text

    def test_validated_path_is_kept(self, service, tmp_path):
        path = _write(tmp_path / "data.csv")
        with patch("app.services.dataset_service.PathSecurityValidator.validate_file_path",
                   return_value=str(path)) as validate:
            result = service._process_file_dataset(_dataset("relative/data.csv"))

        validate.assert_called_once_with("relative/data.csv")
        assert result.filePath == str(path)

    def test_refused_path_is_a_403(self, service, tmp_path):
        path = _write(tmp_path / "data.csv")
        with patch("app.services.dataset_service.FileAccessController.can_read_file", return_value=False):
            assert _http_error(service._process_file_dataset, _dataset(str(path))) == (
                403, "Invalid or dangerous file path")
        with patch("app.services.dataset_service.PathSecurityValidator.validate_file_path",
                   side_effect=HTTPException(status_code=400, detail="Dangerous")):
            assert _http_error(service._process_file_dataset, _dataset(str(path))) == (
                403, "Invalid or dangerous file path")

    def test_unexpected_error_is_logged(self, service, tmp_path, caplog):
        path = _write(tmp_path / "data.csv")
        with patch("app.services.dataset_service.convert_size", side_effect=RuntimeError("boom")):
            result = service._process_file_dataset(_dataset(str(path)))

        assert result.metadata is None
        assert "Error processing file dataset ds: boom" in caplog.text
