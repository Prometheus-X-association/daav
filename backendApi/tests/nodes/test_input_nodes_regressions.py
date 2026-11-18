"""
Regression tests for the MySQL and service chain input nodes with the parquet option (SQLite stands in for MySQL).
"""
import importlib
from unittest.mock import AsyncMock, Mock, patch

import pandas as pd
import pyarrow.parquet as pq
import pytest
from sqlalchemy import create_engine

from app.enums.status_node import StatusNode
from app.models.interface.dataset_interface import MysqlDataset
from app.models.interface.node_data import NodeDataParquet
from app.models.interface.pdc_chain_interface import PdcChainRequestData
from app.nodes.inputs.data_mysql_block import DataMysqlBlock

ServiceChainInput = importlib.import_module("app.nodes.inputs.service-chain-input").ServiceChainInput

pytestmark = pytest.mark.asyncio


def control(value):
    return {"value": value}


def existing_parquet(tmp_path):
    path = str(tmp_path / "old.parquet")
    pd.DataFrame({"old": [0]}).to_parquet(path)
    return NodeDataParquet(data=path, nodeSchema=pq.ParquetFile(path).schema, name="old")


@pytest.fixture
def mysql_table(tmp_path, monkeypatch):
    """A table of 120 rows whose integer column n is NULL at row 70 only, served by a SQLite file."""
    monkeypatch.chdir(tmp_path)  # the node writes its parquet file in the current directory
    engine = create_engine(f"sqlite:///{tmp_path / 'mysql.db'}")
    pd.DataFrame({"id": range(120), "n": [None if i == 70 else i * 2 for i in range(120)]}) \
        .astype({"n": "Int64"}).to_sql("orders", engine, index=False)
    with patch("app.nodes.inputs.data_mysql_block.create_engine", return_value=engine):
        yield


def mysql_input(existing=None):
    node = DataMysqlBlock(id="in", data={"selectDataSource": control("ds1"), "parquetSave": control(True)})
    dataset = MysqlDataset.model_construct(id="ds1", type="mysql", name="my", host="h", user="u", password="p",
                                           database="shop", table="orders")
    node.datasetService = Mock(get_dataset=AsyncMock(return_value=dataset))
    output = Mock()
    output.get_node_data.return_value = existing
    node.outputs = {"out": output}
    return node, output


class TestDataMysqlBlockParquet:

    async def test_null_in_a_later_chunk_keeps_the_integer_column(self, mysql_table, tmp_path):
        node, output = mysql_input()

        assert await node.process() == StatusNode.Valid
        written = pd.read_parquet(tmp_path / "ds1_orders.parquet")
        assert len(written) == 120
        assert str(pq.ParquetFile(tmp_path / "ds1_orders.parquet").schema_arrow.field("n").type) == "int64"
        assert pd.isna(written["n"][70])
        assert written["n"][71] == 142

    async def test_existing_parquet_output_is_updated(self, mysql_table, tmp_path):
        existing = existing_parquet(tmp_path)
        node, output = mysql_input(existing)

        assert await node.process() == StatusNode.Valid
        assert existing.data == "ds1_orders.parquet"
        output.set_node_data.assert_not_called()


def service_chain_input(chain_data, existing=None):
    node = ServiceChainInput(id="in", data={
        "selectDataSource": control("ds1"), "inputsDatasource": [[{"a": 0}]], "parquetSave": control(existing is not None),
    })
    node.datasetService = Mock(get_dataset=AsyncMock(return_value=Mock(id="ds1")),
                               pdcChainData=chain_data, pdcChainHeaders=Mock(x_ptx_service_chain_id="chain"))
    output = Mock()
    output.get_node_data.return_value = existing
    node.outputs = {"pdc-0": output}
    return node, output


class TestServiceChainInputParquet:

    async def test_chain_request_without_additional_data(self):
        node, output = service_chain_input(PdcChainRequestData(origin={"a": [1, 2, 3]}))

        assert await node.process() == StatusNode.Valid
        assert output.set_node_data.call_args.args[0].data["a"].tolist() == [1, 2, 3]

    async def test_existing_parquet_output_is_updated(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        existing = existing_parquet(tmp_path)
        node, output = service_chain_input([{"a": 1}, {"a": 2}], existing)

        assert await node.process() == StatusNode.Valid
        assert existing.data == "ds1_0.parquet"
        assert pd.read_parquet(tmp_path / "ds1_0.parquet")["a"].tolist() == [1, 2]
