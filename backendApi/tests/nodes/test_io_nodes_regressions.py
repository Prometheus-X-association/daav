"""
Regression tests for the MySQL, MongoDB and service chain nodes (databases mocked).
"""
import importlib
from unittest.mock import AsyncMock, Mock, patch

import pandas as pd
import pyarrow.parquet as pq
import pytest
from sqlalchemy import create_engine

from app.enums.status_node import StatusNode
from app.models.interface.dataset_interface import MongoDataset, MysqlDataset
from app.models.interface.node_data import NodeDataPandasDf, NodeDataParquet
from app.nodes.inputs.data_mysql_block import DataMysqlBlock
from app.nodes.outputs.mongo_output import MongoOutput
from app.nodes.outputs.mysql_output import MysqlOutput
from app.utils.utils import generate_pandas_schema

ServiceChainInput = importlib.import_module("app.nodes.inputs.service-chain-input").ServiceChainInput

pytestmark = pytest.mark.asyncio

ROWS = [{"a": 1, "b": "x"}, {"a": 2, "b": "y"}, {"a": 3, "b": "z"}]


def control(value):
    return {"value": value}


def mysql_dataset():
    return MysqlDataset.model_construct(id="ds1", type="mysql", name="my", host="db.example.com",
                                        user="bob", password="secret", database="shop", table="orders")


def connected_input(node_data):
    node_input = Mock()
    node_input.get_connected_node.return_value = Mock()
    node_input.get_node_data.return_value = node_data
    return node_input


def pandas_data(rows=ROWS):
    df = pd.DataFrame(rows)
    return NodeDataPandasDf(nodeSchema=generate_pandas_schema(df), data=df, dataExample=df.head(1), name="in")


def parquet_data(tmp_path, rows=ROWS):
    path = str(tmp_path / "in.parquet")
    pd.DataFrame(rows).to_parquet(path)
    return NodeDataParquet(data=path, nodeSchema=pq.ParquetFile(path).schema, name="in")


def mysql_output(node_data):
    node = MysqlOutput(id="out", data={"selectDataSource": control("ds1"), "selectExist": control("replace")})
    node.datasetService = Mock(get_dataset=AsyncMock(return_value=mysql_dataset()))
    node.inputs = {"in": connected_input(node_data)}
    return node


class FakeMysql:
    """Stands in for the MySQL server: records the requested URLs and serves a SQLite file engine."""

    def __init__(self, tmp_path):
        self.urls = []
        # A file, not memory: the node disposes of its engine, which would drop an in-memory database
        self.engine = create_engine(f"sqlite:///{tmp_path / 'mysql.db'}")

    def create_engine(self, url, *args, **kwargs):
        self.urls.append(str(url))
        return self.engine

    def rows(self, table):
        return pd.read_sql(f"SELECT * FROM {table}", self.engine)


# ===========================
# MYSQL OUTPUT
# ===========================

class TestMysqlOutput:

    async def test_dataframe_is_written_to_mysql(self, tmp_path):
        fake = FakeMysql(tmp_path)
        node = mysql_output(pandas_data())
        with patch("app.nodes.outputs.mysql_output.create_engine", fake.create_engine):
            assert await node.process() == StatusNode.Valid
        assert fake.urls == ["mysql+mysqlconnector://bob:secret@db.example.com/shop"]
        assert fake.rows("orders")["a"].tolist() == [1, 2, 3]

    async def test_parquet_is_written_to_mysql(self, tmp_path):
        fake = FakeMysql(tmp_path)
        node = mysql_output(parquet_data(tmp_path))
        with patch("app.nodes.outputs.mysql_output.create_engine", fake.create_engine):
            assert await node.process() == StatusNode.Valid
        assert fake.urls == ["mysql+mysqlconnector://bob:secret@db.example.com/shop"]
        assert fake.rows("orders")["a"].tolist() == [1, 2, 3]

    async def test_connection_failure_reports_the_original_error(self):
        node = mysql_output(pandas_data())
        with patch("app.nodes.outputs.mysql_output.create_engine", side_effect=RuntimeError("mysql is down")):
            assert await node.process() == StatusNode.Error
        assert node.statusMessage == "mysql is down"


# ===========================
# MONGO OUTPUT
# ===========================

class TestMongoOutput:

    async def test_connection_failure_reports_the_original_error(self):
        node = MongoOutput(id="out", data={"selectDataSource": control("ds1"), "selectExist": control("append")})
        dataset = MongoDataset.model_construct(id="ds1", type="mongo", name="mg", uri="mongodb://db.example.com",
                                               database="shop", collection="orders", table="orders")
        node.datasetService = Mock(get_dataset=AsyncMock(return_value=dataset))
        node.inputs = {"in": connected_input(pandas_data())}
        with patch("app.nodes.outputs.mongo_output.MongoClient", side_effect=RuntimeError("mongo is down")):
            assert await node.process() == StatusNode.Error
        assert node.statusMessage == "mongo is down"


# ===========================
# MYSQL INPUT
# ===========================

class TestDataMysqlBlock:

    async def test_connection_failure_reports_the_original_error(self):
        node = DataMysqlBlock(id="in", data={"selectDataSource": control("ds1")})
        node.datasetService = Mock(get_dataset=AsyncMock(return_value=mysql_dataset()))
        node.outputs = {"out": Mock()}
        with patch("app.nodes.inputs.data_mysql_block.create_engine", side_effect=RuntimeError("mysql is down")):
            assert await node.process() == StatusNode.Error
        assert node.statusMessage == "mysql is down"


# ===========================
# SERVICE CHAIN INPUT
# ===========================

def service_chain_input(existing=None, parquet_save=False):
    node = ServiceChainInput(id="in", data={
        "selectDataSource": control("ds1"),
        "inputsDatasource": [ROWS],
        "parquetSave": control(parquet_save),
    })
    node.datasetService = Mock(get_dataset=AsyncMock(return_value=Mock(id="ds1")),
                               pdcChainData=ROWS, pdcChainHeaders=Mock(x_ptx_service_chain_id="chain"))
    output = Mock()
    output.get_node_data.return_value = existing
    node.outputs = {"pdc-0": output}
    return node, output


class TestServiceChainInput:

    async def test_existing_output_data_is_updated(self):
        existing = pandas_data([{"a": 0, "b": "old"}])
        node, _ = service_chain_input(existing)
        assert await node.process(sample=True) == StatusNode.Valid
        assert existing.dataExample["a"].tolist() == [1, 2, 3]

    async def test_sample_with_parquet_save_creates_a_dataframe(self):
        node, output = service_chain_input(parquet_save=True)
        assert await node.process(sample=True) == StatusNode.Valid
        node_data = output.set_node_data.call_args.args[0]
        assert isinstance(node_data, NodeDataPandasDf)
        assert node_data.dataExample["a"].tolist() == [1, 2, 3]

    async def test_parquet_save_writes_a_file_named_after_the_dataset(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        node, output = service_chain_input(parquet_save=True)
        assert await node.process() == StatusNode.Valid
        node_data = output.set_node_data.call_args.args[0]
        assert isinstance(node_data, NodeDataParquet)
        assert node_data.data == "ds1_0.parquet"
        assert pd.read_parquet(tmp_path / "ds1_0.parquet")["a"].tolist() == [1, 2, 3]
