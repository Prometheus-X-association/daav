"""
Integration tests against a real Elasticsearch node.

Skipped unless ES_TEST_URL is set, e.g.:
    ES_TEST_URL=http://samX1:9200 ES_TEST_USER=elastic ES_TEST_PASSWORD=... pytest tests/integration
Each test index (daav-it-*) is removed at the end of its test.
"""
import os
import uuid
from unittest.mock import AsyncMock, Mock
from urllib.parse import urlparse

import pandas as pd
import pytest

from app.config.settings import settings
from app.enums.status_node import StatusNode
from app.models.interface.dataset_interface import ElasticDataset
from app.models.interface.node_data import NodeDataPandasDf
from app.nodes.inputs.data_elastic_block import DataElasticBlock
from app.nodes.outputs.elastic_output import ElasticOutput
from app.services.elastic_service import ElasticService, ElasticServiceError

ES_URL = os.environ.get("ES_TEST_URL")

pytestmark = pytest.mark.skipif(not ES_URL, reason="ES_TEST_URL is not set")


@pytest.fixture
def dataset(monkeypatch):
    monkeypatch.setattr(settings, "allowed_private_hosts", [urlparse(ES_URL).hostname])
    return ElasticDataset.model_construct(
        id="it", type="elastic", name="it", url=ES_URL, verifyCerts=False,
        user=os.environ.get("ES_TEST_USER"), password=os.environ.get("ES_TEST_PASSWORD"),
        key=os.environ.get("ES_TEST_API_KEY"),
    )


@pytest.fixture
def index_name(dataset):
    name = f"daav-it-{uuid.uuid4().hex[:8]}"
    yield name
    with ElasticService().connect(dataset) as client:
        client.indices.delete(index=name, ignore_unavailable=True)


def control(value):
    return {"value": value}


def output_node(dataset, df, data):
    node = ElasticOutput(id="out", data={"selectDataSource": control("it"), **data})
    node.datasetService = Mock(get_dataset=AsyncMock(return_value=dataset))
    source = Mock()
    source.get_connected_node.return_value = Mock()
    source.get_node_data.return_value = NodeDataPandasDf(nodeSchema=[], name="in", data=df, dataExample=df.head(2))
    node.inputs = {"datasource": source}
    return node


def input_node(dataset, data):
    node = DataElasticBlock(id="in", data={"selectDataSource": control("it"), **data})
    node.datasetService = Mock(get_dataset=AsyncMock(return_value=dataset))
    output = Mock()
    output.get_node_data.return_value = None
    node.outputs = {"out": output}
    return node


@pytest.mark.asyncio
async def test_write_then_read_round_trip(dataset, index_name):
    df = pd.DataFrame({
        "sku": [f"S{i}" for i in range(2500)],
        "price": [i * 1.5 for i in range(2500)],
        "in_stock": [i % 2 == 0 for i in range(2500)],
        "created": pd.date_range("2025-01-01", periods=2500, freq="h"),
        "supplier": [{"name": f"F{i % 3}", "country": "FR"} for i in range(2500)],
        "note": [None if i % 10 else "x" for i in range(2500)],
    })
    out = output_node(dataset, df, {"indexAutoComplete": control(index_name), "idField": control("sku")})
    assert await out.process() == StatusNode.Valid, out.statusMessage

    service = ElasticService()
    mapping = service.get_mapping(dataset, index_name)["properties"]
    assert mapping["price"]["type"] == "double"
    assert mapping["created"]["type"] == "date"
    assert mapping["supplier"]["properties"]["name"]["type"] == "text"

    # Full read goes beyond one scan batch
    node = input_node(dataset, {"selectIndexDataSource": control(index_name)})
    assert await node.process() == StatusNode.Valid, node.statusMessage
    result = node.outputs["out"].set_node_data.call_args.args[0].data
    assert len(result) == 2500
    assert set(result["_id"]) == set(df["sku"])

    # Query, fields and max documents
    node = input_node(dataset, {
        "selectIndexDataSource": control(index_name),
        "query": control('{"term": {"in_stock": true}}'),
        "fields": control("sku,price"),
        "maxDocs": control(1500),
        "includeId": control(False),
    })
    assert await node.process() == StatusNode.Valid, node.statusMessage
    result = node.outputs["out"].set_node_data.call_args.args[0].data
    assert len(result) == 1250
    assert set(result.columns) == {"sku", "price"}

    # Upsert on the id field: appending the same rows does not duplicate them
    out = output_node(dataset, df.head(10), {"indexAutoComplete": control(index_name), "idField": control("sku"),
                                             "selectExist": control("append")})
    assert await out.process() == StatusNode.Valid, out.statusMessage
    assert service.count(dataset, index_name) == 2500


@pytest.mark.asyncio
async def test_if_exist_options(dataset, index_name):
    df = pd.DataFrame({"a": [1, 2, 3]})
    params = {"indexAutoComplete": control(index_name)}
    assert await output_node(dataset, df, params).process() == StatusNode.Valid

    out = output_node(dataset, df, params)
    assert await out.process() == StatusNode.Error
    assert "already exists" in out.statusMessage

    out = output_node(dataset, df, {**params, "selectExist": control("append")})
    assert await out.process() == StatusNode.Valid
    assert ElasticService().count(dataset, index_name) == 6

    out = output_node(dataset, df, {**params, "selectExist": control("replace")})
    assert await out.process(sample=True) == StatusNode.Valid
    assert ElasticService().count(dataset, index_name) == 2


@pytest.mark.asyncio
async def test_rejected_documents(dataset, index_name):
    ElasticService().create_index(dataset, index_name, mappings={"properties": {"n": {"type": "integer"}}})
    out = output_node(dataset, pd.DataFrame({"n": ["1", "not a number"]}),
                      {"indexAutoComplete": control(index_name), "selectExist": control("append")})
    assert await out.process() == StatusNode.Error
    assert "1 documents were rejected" in out.statusMessage


def test_dashboard_operations(dataset, index_name):
    service = ElasticService()
    assert service.info(dataset)["version"]
    service.create_index(dataset, index_name, mappings={"properties": {"title": {"type": "keyword"}}})
    with pytest.raises(ElasticServiceError) as exc:
        service.create_index(dataset, index_name)
    assert exc.value.status_code == 409
    names = [i["index"] for i in service.list_indices(dataset)]
    assert index_name in names
    assert service.get_mapping(dataset, index_name) == {"properties": {"title": {"type": "keyword"}}}
    data, total = service.search_page(dataset, index_name, query="title:x")
    assert (data, total) == ([], 0)
