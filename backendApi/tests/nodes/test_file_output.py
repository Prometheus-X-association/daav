"""
Unit tests of the file output node helpers
"""
import pandas as pd
import pyarrow.parquet as pq

from app.nodes.outputs.file_output import FileOutput


def write_parquet(path, df):
    df.to_parquet(path)
    return pq.ParquetFile(path)


def test_parquet_data_is_written_as_csv_in_chunks(tmp_path):
    """The CSV writer (run in a worker thread by process) writes the header once and every chunk"""
    parquet_file = write_parquet(tmp_path / "in.parquet", pd.DataFrame({"a": range(5), "b": list("vwxyz")}))
    output_file = tmp_path / "out.csv"
    node = FileOutput("output", {})

    node._write_csv_parquet_data(parquet_file, str(output_file), ";", "utf-8", False, 2, "replace")

    assert output_file.read_text().splitlines() == ["a;b", "0;v", "1;w", "2;x", "3;y", "4;z"]


def test_parquet_sample_is_limited_to_the_first_chunk(tmp_path):
    parquet_file = write_parquet(tmp_path / "in.parquet", pd.DataFrame({"a": range(5)}))
    output_file = tmp_path / "out.csv"
    node = FileOutput("output", {})

    node._write_csv_parquet_data(parquet_file, str(output_file), ",", "utf-8", True, 2, "replace")

    assert output_file.read_text().splitlines() == ["a", "0", "1"]
