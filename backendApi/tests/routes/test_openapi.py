"""
The OpenAPI schema (/openapi.json, used by /docs) can be generated for every route
"""
from http import HTTPStatus

import pandas as pd
from fastapi.testclient import TestClient

from app.main import app
from app.models.interface.dataset_schema import PandasColumn, PandasSchema
from app.models.interface.node_data import NodeDataPandasDf


def test_openapi_schema_is_generated():
    """Models holding a pandas DataFrame or a Parquet schema used to make /openapi.json fail"""
    # Without the context manager, the lifespan (database connection) does not run
    response = TestClient(app).get("/openapi.json")

    assert response.status_code == 200
    schemas = response.json()["components"]["schemas"]
    assert "NodeDataPandasDf" in schemas
    assert "NodeDataParquet" in schemas


def test_dataframe_serialization_unchanged():
    """The JSON schema annotation does not change how the data sample is serialized"""
    node = NodeDataPandasDf(
        nodeSchema=PandasSchema([PandasColumn(name="a", dtype="int64", nullable=False, count=2)]),
        name="n",
        dataExample=pd.DataFrame({"a": [1, 2]}),
    )

    dumped = node.model_dump()

    assert dumped["dataExample"] == {"a": {0: 1, 1: 2}}
    assert dumped["type"] == "pandasdf"


def test_error_responses_are_documented():
    """The HTTP error status codes raised by the routes appear in the OpenAPI schema"""
    paths = TestClient(app).get("/openapi.json").json()["paths"]

    upload = paths["/datasets/uploadFile"]["post"]["responses"]
    assert {"400", "413", "500"} <= upload.keys()
    assert upload["413"]["description"] == HTTPStatus(413).phrase  # "Content Too Large" since Python 3.13
    delete_workflow = paths["/workflows/{id}"]["delete"]["responses"]
    assert {"404", "500"} <= delete_workflow.keys()
    assert {"400", "401"} <= paths["/ptx/executeChainService"]["post"]["responses"].keys()


def test_error_responses_helper():
    from app.routes.responses import error_responses

    assert error_responses(404, 500) == {404: {"description": "Not Found"}, 500: {"description": "Internal Server Error"}}
