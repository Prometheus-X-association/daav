"""
Regression tests for the dataset readers: HTTP errors must keep their status code.
"""
from unittest.mock import patch

import numpy
import pandas as pd
import pytest
from fastapi import HTTPException
from pymongo.errors import ConnectionFailure

from app.models.interface.dataset_interface import (
    DatasetParams, FileDataset, MongoDataset, MysqlDataset, Pagination,
)
from app.models.interface.node_data import NodeDataPandasDf
from app.routes.datasets import get_mongo_content
from app.services.dataset_service import DatasetService
from app.utils.utils import generate_pandas_schema


@pytest.fixture
def service():
    return DatasetService()


def test_mysql_dataframe_without_table_is_a_422(service):
    dataset = MysqlDataset.model_construct(id="ds1", type="mysql", name="my", host="h", user="u", password="p",
                                           database=None, table=None)
    params = DatasetParams()
    with pytest.raises(HTTPException) as error:
        service.getDfMysqlContent(dataset, params)
    assert error.value.status_code == 422


def test_mongo_dataframe_without_collection_is_a_422(service):
    dataset = MongoDataset.model_construct(id="ds1", type="mongo", name="mg", uri="mongodb://db.example.com",
                                           database=None, collection=None)
    params = DatasetParams()
    with pytest.raises(HTTPException) as error:
        service.getDfMongoContent(dataset, params)
    assert error.value.status_code == 422


def test_mongo_content_connection_failure_is_a_503():
    dataset = MongoDataset.model_construct(id="ds1", type="mongo", name="mg", uri="mongodb://db.example.com",
                                           database="shop", collection="orders")
    pagination, params = Pagination(page=1, perPage=10), DatasetParams()
    with patch("pymongo.mongo_client.MongoClient", side_effect=ConnectionFailure("mongo is down")):
        with pytest.raises(HTTPException) as error:
            get_mongo_content(dataset, pagination, params)
    assert error.value.status_code == 503


def test_file_dataset_with_a_forbidden_path_is_refused(service, tmp_path):
    path = tmp_path / "data.csv"
    path.write_text("a,b\n1,2\n")
    dataset = FileDataset.model_construct(id="ds1", type="file", name="f", filePath=str(path),
                                          csvHeader="0", csvDelimiter=",")
    with patch("app.services.dataset_service.FileAccessController.can_read_file", return_value=False):
        with pytest.raises(HTTPException) as error:
            service._process_file_dataset(dataset)
    assert error.value.status_code == 403


def test_file_dataset_with_a_missing_file_keeps_no_metadata(service, tmp_path, caplog):
    dataset = FileDataset.model_construct(id="ds1", type="file", name="f", filePath=str(tmp_path / "missing.csv"),
                                          csvHeader="0", csvDelimiter=",", metadata=None)
    with patch("app.services.dataset_service.FileAccessController.can_read_file", return_value=True):
        result = service._process_file_dataset(dataset)
    assert result.metadata is None
    assert "File not found" in caplog.text
    assert "Error processing file dataset" not in caplog.text


def test_numpy_scalars_are_converted_for_json():
    df = pd.DataFrame([{"a": 1}])
    node_data = NodeDataPandasDf(nodeSchema=generate_pandas_schema(df), name="n")
    day = numpy.datetime64("2024-01-02")
    assert node_data._convert_objectid(day) == day.item()
    assert node_data._convert_objectid(numpy.str_("x")) == "x"
    assert node_data._convert_objectid({"n": [numpy.int64(3), numpy.float32(0.5), numpy.bool_(True)]}) == {"n": [3, 0.5, True]}
