"""
Unit tests for the Elasticsearch input and output nodes (Elasticsearch mocked).
"""
from unittest.mock import AsyncMock, MagicMock, Mock

import pandas as pd
import pytest

from app.enums.status_node import StatusNode
from app.models.interface.dataset_interface import ElasticDataset
from app.models.interface.node_data import NodeDataPandasDf
from app.nodes.inputs.data_elastic_block import DataElasticBlock
from app.nodes.outputs.elastic_output import ElasticOutput

pytestmark = pytest.mark.asyncio


def make_dataset(**kwargs):
    defaults = dict(id="ds1", type="elastic", name="es", url="https://es.example.com", verifyCerts=True)
    defaults.update(kwargs)
    return ElasticDataset.model_construct(**defaults)


def control(value):
    return {"value": value}


# ===========================
# INPUT NODE
# ===========================

@pytest.fixture
def input_node():
    def build(data, dataset=None):
        node = DataElasticBlock(id="in", data=data)
        node.datasetService = Mock(get_dataset=AsyncMock(return_value=dataset or make_dataset()))
        node.elasticService = Mock()
        node.elasticService.sample_dataframe.return_value = pd.DataFrame([{"_id": "1", "a": 1}])
        node.elasticService.read_dataframe.return_value = pd.DataFrame([{"_id": "1", "a": 1}, {"_id": "2", "a": 2}])
        output = Mock()
        output.get_node_data.return_value = None
        node.outputs = {"out": output}
        return node
    return build


class TestDataElasticBlock:

    async def test_full_read(self, input_node):
        node = input_node({
            "selectDataSource": control("ds1"),
            "selectIndexDataSource": control("products"),
            "query": control("category:books"),
            "fields": control("name, price ,"),
            "maxDocs": control("100"),
            "includeId": control(False),
        })
        assert await node.process() == StatusNode.Valid
        args = node.elasticService.read_dataframe.call_args.args
        assert args[1:] == ("products", "category:books", ["name", "price"], 100, False)
        node_data = node.outputs["out"].set_node_data.call_args.args[0]
        assert isinstance(node_data, NodeDataPandasDf)
        assert len(node_data.data) == 2 and node_data.name == "products"

    async def test_sample_is_limited(self, input_node):
        node = input_node({"selectDataSource": control("ds1"), "selectIndexDataSource": control("products"),
                           "maxDocs": control(5)})
        assert await node.process(sample=True) == StatusNode.Valid
        args = node.elasticService.sample_dataframe.call_args.args
        assert args[1:] == ("products", 5, None, None, True)
        node.elasticService.read_dataframe.assert_not_called()
        node_data = node.outputs["out"].set_node_data.call_args.args[0]
        assert len(node_data.dataExample) == 1

    async def test_dataset_index_takes_precedence(self, input_node):
        node = input_node({"selectDataSource": control("ds1"), "selectIndexDataSource": control("other")},
                          dataset=make_dataset(index="fixed"))
        await node.process()
        assert node.elasticService.read_dataframe.call_args.args[1] == "fixed"

    async def test_existing_output_data_updated(self, input_node):
        node = input_node({"selectDataSource": control("ds1"), "selectIndexDataSource": control("products")})
        existing = NodeDataPandasDf(nodeSchema=[], name="products")
        node.outputs["out"].get_node_data.return_value = existing
        await node.process()
        assert len(existing.data) == 2
        node.outputs["out"].set_node_data.assert_not_called()

    @pytest.mark.parametrize("data, message", [
        ({}, "No data source"),
        ({"selectDataSource": control("ds1")}, "No index"),
        ({"selectDataSource": control("ds1"), "selectIndexDataSource": control("*")}, "wildcard"),
        ({"selectDataSource": control("ds1"), "selectIndexDataSource": control("p"), "maxDocs": control("x")}, "must be a number"),
        ({"selectDataSource": control("ds1"), "selectIndexDataSource": control("p"), "maxDocs": control(0)}, "positive"),
    ])
    async def test_invalid_configuration(self, input_node, data, message):
        node = input_node(data)
        assert await node.process() == StatusNode.Error
        assert message in node.statusMessage

    async def test_not_an_elastic_dataset(self, input_node):
        node = input_node({"selectDataSource": control("ds1"), "selectIndexDataSource": control("p")},
                          dataset=Mock(spec=[]))
        assert await node.process() == StatusNode.Error
        assert "not an Elasticsearch dataset" in node.statusMessage


# ===========================
# OUTPUT NODE
# ===========================

@pytest.fixture
def output_node():
    def build(data, df, exists=False, bulk_result=None):
        node = ElasticOutput(id="out", data=data)
        node.datasetService = Mock(get_dataset=AsyncMock(return_value=make_dataset()))
        client = MagicMock()
        client.indices.exists.return_value = exists
        node.elasticService = Mock()
        node.elasticService.connect.return_value.__enter__ = Mock(return_value=client)
        node.elasticService.connect.return_value.__exit__ = Mock(return_value=False)
        node.elasticService.bulk_index.side_effect = (
            bulk_result or (lambda client, index, records, id_field=None: (len(records), 0, []))
        )
        source = Mock()
        source.get_connected_node.return_value = Mock()
        source.get_node_data.return_value = NodeDataPandasDf(nodeSchema=[], name="in", data=df, dataExample=df.head(1))
        node.inputs = {"datasource": source}
        return node
    return build


def es_client(node):
    return node.elasticService.connect.return_value.__enter__.return_value


OUTPUT_DATA = {"selectDataSource": control("ds1"), "indexAutoComplete": control("target")}


class TestElasticOutput:

    async def test_creates_index_with_mapping_and_indexes(self, output_node):
        df = pd.DataFrame({"sku": ["a", "b"], "price": [1.5, 2.0]})
        node = output_node(OUTPUT_DATA, df)
        assert await node.process() == StatusNode.Valid
        es_client(node).indices.create.assert_called_once_with(
            index="target", mappings={"properties": {"price": {"type": "double"}}})
        records = node.elasticService.bulk_index.call_args.args[2]
        assert records == [{"sku": "a", "price": 1.5}, {"sku": "b", "price": 2.0}]
        es_client(node).indices.refresh.assert_called_once_with(index="target")
        assert "2 documents indexed" in node.statusMessage

    async def test_sample_writes_sample_only(self, output_node):
        node = output_node(OUTPUT_DATA, pd.DataFrame({"a": [1, 2, 3]}))
        assert await node.process(sample=True) == StatusNode.Valid
        assert len(node.elasticService.bulk_index.call_args.args[2]) == 1

    async def test_fail_if_exists(self, output_node):
        node = output_node(OUTPUT_DATA, pd.DataFrame({"a": [1]}), exists=True)
        assert await node.process() == StatusNode.Error
        assert "already exists" in node.statusMessage
        node.elasticService.bulk_index.assert_not_called()

    async def test_replace_recreates_index(self, output_node):
        node = output_node({**OUTPUT_DATA, "selectExist": control("replace")}, pd.DataFrame({"a": [1]}), exists=True)
        assert await node.process() == StatusNode.Valid
        es_client(node).indices.delete.assert_called_once_with(index="target")
        es_client(node).indices.create.assert_called_once()

    async def test_append_keeps_index(self, output_node):
        node = output_node({**OUTPUT_DATA, "selectExist": control("append")}, pd.DataFrame({"a": [1]}), exists=True)
        assert await node.process() == StatusNode.Valid
        es_client(node).indices.delete.assert_not_called()
        es_client(node).indices.create.assert_not_called()

    async def test_id_field(self, output_node):
        node = output_node({**OUTPUT_DATA, "idField": control("sku")}, pd.DataFrame({"sku": ["a"]}))
        assert await node.process() == StatusNode.Valid
        assert node.elasticService.bulk_index.call_args.kwargs["id_field"] == "sku"

    async def test_unknown_id_field(self, output_node):
        node = output_node({**OUTPUT_DATA, "idField": control("nope")}, pd.DataFrame({"sku": ["a"]}))
        assert await node.process() == StatusNode.Error
        assert "'nope'" in node.statusMessage

    async def test_rejected_documents_reported(self, output_node):
        node = output_node(OUTPUT_DATA, pd.DataFrame({"a": [1, 2]}),
                           bulk_result=lambda client, index, records, id_field=None: (1, 1, ["mapper_parsing_exception"]))
        assert await node.process() == StatusNode.Error
        assert "1 documents were rejected" in node.statusMessage
        assert "mapper_parsing_exception" in node.statusMessage

    @pytest.mark.parametrize("data, message", [
        ({"indexAutoComplete": control("t")}, "No data source"),
        ({"selectDataSource": control("ds1")}, "No index"),
        ({**OUTPUT_DATA, "indexAutoComplete": control("UPPER")}, "invalid characters"),
        ({**OUTPUT_DATA, "selectExist": control("drop")}, "Invalid ifExist"),
    ])
    async def test_invalid_configuration(self, output_node, data, message):
        node = output_node(data, pd.DataFrame({"a": [1]}))
        assert await node.process() == StatusNode.Error
        assert message in node.statusMessage
