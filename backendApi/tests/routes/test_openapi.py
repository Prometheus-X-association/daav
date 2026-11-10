"""
The OpenAPI schema (/openapi.json, used by /docs) can be generated for every route
"""
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
