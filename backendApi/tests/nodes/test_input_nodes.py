"""
Unit tests for the process method of the MySQL and service chain input nodes (database mocked by SQLite).
"""
import importlib
from unittest.mock import AsyncMock, Mock, patch

import pandas as pd
import pyarrow.parquet as pq
import pytest
from pyarrow.parquet import ParquetSchema
from sqlalchemy import create_engine

from app.enums.status_node import StatusNode
from app.models.interface.dataset_interface import MysqlDataset
from app.models.interface.node_data import NodeDataPandasDf, NodeDataParquet
from app.models.interface.pdc_chain_interface import AdditionalDataItem, Participant, PdcChainRequestData
from app.nodes.inputs.data_mysql_block import DataMysqlBlock
from app.utils.utils import generate_pandas_schema

ServiceChainInput = importlib.import_module("app.nodes.inputs.service-chain-input").ServiceChainInput

pytestmark = pytest.mark.asyncio

TABLE_ROWS = [{"a": i, "b": f"row{i}"} for i in range(130)]  # three chunks of 50


def control(value):
    return {"value": value}


def empty_output():
    output = Mock()
    output.get_node_data.return_value = None
    return output


def output_with(node_data):
    output = Mock()
    output.get_node_data.return_value = node_data
    return output


def published(output):
    return output.set_node_data.call_args.args[0]


def existing_dataframe():
    df = pd.DataFrame([{"old": 0}])
    return NodeDataPandasDf(nodeSchema=generate_pandas_schema(df), data=df, dataExample=df, name="previous")


def existing_parquet(tmp_path):
    path = str(tmp_path / "previous.parquet")
    pd.DataFrame([{"old": 0}]).to_parquet(path)
    return NodeDataParquet(data=path, nodeSchema=pq.ParquetFile(path).schema, name="previous")


def records(df):
    return df.to_dict(orient="records")


# ===========================
# MYSQL INPUT
# ===========================

class FakeMysql:
    """Stands in for the MySQL server: records the requested URLs and queries, and serves a SQLite file engine."""

    def __init__(self, tmp_path):
        self.urls = []
        self.queries = []
        # A file, not memory: the node disposes of its engine, which would drop an in-memory database
        self.engine = create_engine(f"sqlite:///{tmp_path / 'mysql.db'}")
        pd.DataFrame(TABLE_ROWS).to_sql("orders", self.engine, index=False)
        pd.DataFrame({"a": pd.Series([], dtype="int64")}).to_sql("empty_orders", self.engine, index=False)
        self._read_sql_query = pd.read_sql_query

    def create_engine(self, url, *args, **kwargs):
        self.urls.append(str(url))
        return self.engine

    def read_sql_query(self, query, con, **kwargs):
        self.queries.append((query, kwargs))
        return self._read_sql_query(query, con, **kwargs)


@pytest.fixture
def mysql(tmp_path, monkeypatch):
    # The parquet file of the node is written in the working directory
    monkeypatch.chdir(tmp_path)
    fake = FakeMysql(tmp_path)
    with patch("app.nodes.inputs.data_mysql_block.create_engine", fake.create_engine), \
            patch("app.nodes.inputs.data_mysql_block.pd.read_sql_query", fake.read_sql_query):
        yield fake


def mysql_input(parquet_save=None, table=None, **outputs):
    data = {"selectDataSource": control("ds1")}
    if parquet_save is not None:
        data["parquetSave"] = control(parquet_save)
    if table:
        data["selectTableDataSource"] = control(table)
    node = DataMysqlBlock(id="in", data=data)
    dataset = MysqlDataset.model_construct(id="ds1", type="mysql", name="my", host="db.example.com",
                                           user="bob", password="secret", database="shop", table="orders")
    node.datasetService = Mock(get_dataset=AsyncMock(return_value=dataset))
    node.outputs = outputs or {"out": empty_output()}
    return node


class TestDataMysqlBlock:

    async def test_table_is_read_in_memory(self, mysql):
        node = mysql_input()
        assert await node.process() == StatusNode.Valid
        assert mysql.urls == ["mysql+mysqlconnector://bob:secret@db.example.com/shop"]
        assert mysql.queries == [("SELECT * FROM orders", {})]
        node_data = published(node.outputs["out"])
        assert isinstance(node_data, NodeDataPandasDf)
        assert records(node_data.data) == TABLE_ROWS
        assert node_data.dataExample is None
        assert node_data.name == "out"
        assert node_data.nodeSchema == generate_pandas_schema(pd.DataFrame(TABLE_ROWS))
        node.outputs["out"].set_node_data.assert_called_once_with(node_data, node)

    async def test_sample_reads_twenty_rows(self, mysql):
        node = mysql_input(parquet_save=False)
        assert await node.process(sample=True) == StatusNode.Valid
        assert mysql.queries == [("SELECT * FROM orders LIMIT 20", {})]
        node_data = published(node.outputs["out"])
        assert records(node_data.dataExample) == TABLE_ROWS[:20]
        assert node_data.data is None

    async def test_parquet_save_writes_the_table_by_chunks(self, mysql, tmp_path):
        node = mysql_input(parquet_save=True)
        assert await node.process() == StatusNode.Valid
        assert mysql.queries == [("SELECT * FROM orders", {"chunksize": 50, "dtype_backend": "numpy_nullable"})]
        node_data = published(node.outputs["out"])
        assert isinstance(node_data, NodeDataParquet)
        assert node_data.data == "ds1_orders.parquet"
        assert node_data.name == "out"
        assert isinstance(node_data.nodeSchema, ParquetSchema)
        assert node_data.nodeSchema.names == ["a", "b"]
        parquet_file = pq.ParquetFile(tmp_path / "ds1_orders.parquet")
        assert parquet_file.num_row_groups == 3
        assert records(parquet_file.read().to_pandas()) == TABLE_ROWS

    async def test_parquet_save_sample_writes_the_first_chunk_only(self, mysql, tmp_path):
        node = mysql_input(parquet_save=True)
        assert await node.process(sample=True) == StatusNode.Valid
        assert mysql.queries == [("SELECT * FROM orders", {"chunksize": 50, "dtype_backend": "numpy_nullable"})]
        assert isinstance(published(node.outputs["out"]), NodeDataParquet)
        rows = records(pd.read_parquet(tmp_path / "ds1_orders.parquet"))
        # Known: the sample is the first chunk, it is not cut to 20 rows
        assert 0 < len(rows) <= 50
        assert rows == TABLE_ROWS[:len(rows)]

    async def test_parquet_save_of_an_empty_table(self, mysql, tmp_path):
        node = mysql_input(parquet_save=True, table="empty_orders")
        assert await node.process() == StatusNode.Valid
        assert published(node.outputs["out"]).data == "ds1_empty_orders.parquet"
        assert len(pd.read_parquet(tmp_path / "ds1_empty_orders.parquet")) == 0

    async def test_every_output_gets_its_node_data(self, mysql):
        node = mysql_input(first=empty_output(), second=empty_output())
        assert await node.process() == StatusNode.Valid
        assert published(node.outputs["first"]).name == "first"
        assert published(node.outputs["second"]).name == "second"
        assert records(published(node.outputs["second"]).data) == TABLE_ROWS

    async def test_existing_dataframe_is_updated(self, mysql):
        existing = existing_dataframe()
        node = mysql_input(out=output_with(existing))
        assert await node.process() == StatusNode.Valid
        assert records(existing.data) == TABLE_ROWS
        assert records(existing.dataExample) == [{"old": 0}]
        assert existing.nodeSchema == generate_pandas_schema(pd.DataFrame(TABLE_ROWS))
        assert existing.name == "previous"
        node.outputs["out"].set_node_data.assert_not_called()

    async def test_existing_dataframe_sample_is_updated(self, mysql):
        existing = existing_dataframe()
        node = mysql_input(out=output_with(existing))
        assert await node.process(sample=True) == StatusNode.Valid
        assert records(existing.dataExample) == TABLE_ROWS[:20]
        assert records(existing.data) == [{"old": 0}]

    async def test_existing_dataframe_with_parquet_save(self, mysql):
        node = mysql_input(parquet_save=True, out=output_with(existing_dataframe()))
        assert await node.process() == StatusNode.Error
        assert node.statusMessage == "Output node data is not of type NodeDataParquet"
        assert "ValueError" in "".join(node.errorStackTrace)

    async def test_existing_parquet_without_parquet_save(self, mysql, tmp_path):
        node = mysql_input(out=output_with(existing_parquet(tmp_path)))
        assert await node.process() == StatusNode.Error
        assert node.statusMessage == "Output node data is not of type NodeDataPandasDf"

    async def test_unknown_table(self, mysql):
        node = mysql_input(table="missing")
        assert await node.process() == StatusNode.Error
        assert "no such table: missing" in node.statusMessage
        node.outputs["out"].set_node_data.assert_not_called()

    async def test_connection_is_closed_and_engine_disposed(self):
        engine = Mock()
        node = mysql_input()
        with patch("app.nodes.inputs.data_mysql_block.create_engine", return_value=engine), \
                patch("app.nodes.inputs.data_mysql_block.pd.read_sql_query", return_value=pd.DataFrame(TABLE_ROWS)) as read:
            assert await node.process() == StatusNode.Valid
        assert read.call_args.args == ("SELECT * FROM orders", engine.connect.return_value)
        engine.connect.return_value.close.assert_called_once_with()
        engine.dispose.assert_called_once_with()

    async def test_connection_is_closed_after_an_error(self):
        engine = Mock()
        node = mysql_input()
        with patch("app.nodes.inputs.data_mysql_block.create_engine", return_value=engine), \
                patch("app.nodes.inputs.data_mysql_block.pd.read_sql_query", side_effect=RuntimeError("read refused")):
            assert await node.process() == StatusNode.Error
        assert node.statusMessage == "read refused"
        assert "RuntimeError" in "".join(node.errorStackTrace)
        engine.connect.return_value.close.assert_called_once_with()
        engine.dispose.assert_called_once_with()

    async def test_missing_data_source(self, mysql):
        node = mysql_input()
        node.data = {}
        assert await node.process() == StatusNode.Error
        assert node.statusMessage == "No data source selected"
        assert "ValueError" in "".join(node.errorStackTrace)
        assert mysql.urls == []

    async def test_dataset_service_failure_is_raised(self, mysql):
        node = mysql_input()
        node.datasetService.get_dataset.side_effect = RuntimeError("database is down")
        with pytest.raises(RuntimeError, match="database is down"):
            await node.process()


# ===========================
# SERVICE CHAIN INPUT
# ===========================

EXAMPLES = [[{"a": 1}, {"a": 2}], [{"b": "x"}]]
ORIGIN = {"a": [1, 2, 3]}
CHAIN_HEADERS = Mock(x_ptx_service_chain_id="chain-1")


def additional(data):
    participant = Participant(name="p", connectorUrl="http://p.example.com", id="p1")
    return AdditionalDataItem(participant=participant, params={}, data=data)


def service_chain_input(chain_data=None, parquet_save=None, outputs=None):
    data = {"selectDataSource": control("ds1"), "inputsDatasource": EXAMPLES}
    if parquet_save is not None:
        data["parquetSave"] = control(parquet_save)
    node = ServiceChainInput(id="in", data=data)
    node.datasetService = Mock(get_dataset=AsyncMock(return_value=Mock(id="ds1")),
                               pdcChainData=chain_data, pdcChainHeaders=CHAIN_HEADERS)
    node.outputs = outputs or {"pdc-0": empty_output(), "pdc-1": empty_output(), "pdc-2": empty_output()}
    return node


class TestServiceChainInput:

    async def test_sample_publishes_each_example(self):
        node = service_chain_input(chain_data=[{"ignored": 1}])
        assert await node.process(sample=True) == StatusNode.Valid
        first, second = published(node.outputs["pdc-0"]), published(node.outputs["pdc-1"])
        assert isinstance(first, NodeDataPandasDf)
        assert (first.name, second.name) == ("Example 0", "Example 1")
        assert records(first.dataExample) == EXAMPLES[0]
        assert records(second.dataExample) == EXAMPLES[1]
        assert first.data is None
        assert first.nodeSchema == generate_pandas_schema(pd.DataFrame(EXAMPLES[0]))
        node.outputs["pdc-0"].set_node_data.assert_called_once_with(first, node)
        node.outputs["pdc-2"].set_node_data.assert_not_called()

    async def test_raw_chain_data_goes_to_the_first_output(self):
        node = service_chain_input(chain_data=[{"a": 1}, {"a": 2}])
        assert await node.process() == StatusNode.Valid
        node_data = published(node.outputs["pdc-0"])
        assert node_data.name == "chain-1 0"
        assert records(node_data.data) == [{"a": 1}, {"a": 2}]
        assert node_data.dataExample is None
        node.outputs["pdc-1"].set_node_data.assert_not_called()

    async def test_chain_request_publishes_the_origin_then_the_additional_data(self):
        chain_data = PdcChainRequestData(origin=ORIGIN, additionalData=[additional({"b": ["x"]}),
                                                                        additional({"c": [1.5, 2.5]})])
        node = service_chain_input(chain_data=chain_data)
        assert await node.process() == StatusNode.Valid
        outputs = [published(node.outputs[f"pdc-{index}"]) for index in range(3)]
        assert [node_data.name for node_data in outputs] == ["chain-1 0", "chain-1 1", "chain-1 2"]
        assert [records(node_data.data) for node_data in outputs] == [
            [{"a": 1}, {"a": 2}, {"a": 3}], [{"b": "x"}], [{"c": 1.5}, {"c": 2.5}]]

    async def test_parquet_save_writes_one_file_per_dataset(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        chain_data = PdcChainRequestData(origin=ORIGIN, additionalData=[additional({"b": ["x"]})])
        node = service_chain_input(chain_data=chain_data, parquet_save=True)
        assert await node.process() == StatusNode.Valid
        first, second = published(node.outputs["pdc-0"]), published(node.outputs["pdc-1"])
        assert isinstance(second, NodeDataParquet)
        assert (first.data, second.data) == ("ds1_0.parquet", "ds1_1.parquet")
        assert (first.name, second.name) == ("chain-1 0", "chain-1 1")
        assert first.nodeSchema.names == ["a"]
        assert records(pd.read_parquet(tmp_path / "ds1_1.parquet")) == [{"b": "x"}]

    async def test_existing_dataframe_is_updated(self):
        existing = existing_dataframe()
        node = service_chain_input(chain_data=[{"a": 1}], outputs={"pdc-0": output_with(existing)})
        assert await node.process() == StatusNode.Valid
        assert records(existing.data) == [{"a": 1}]
        assert records(existing.dataExample) == [{"old": 0}]
        assert existing.nodeSchema == generate_pandas_schema(pd.DataFrame([{"a": 1}]))
        assert existing.name == "previous"
        node.outputs["pdc-0"].set_node_data.assert_not_called()

    async def test_existing_dataframe_with_parquet_save(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        node = service_chain_input(chain_data=[{"a": 1}], parquet_save=True,
                                   outputs={"pdc-0": output_with(existing_dataframe())})
        assert await node.process() == StatusNode.Error
        assert node.statusMessage == "Output node data is not of type NodeDataParquet"
        assert "ValueError" in "".join(node.errorStackTrace)

    async def test_existing_parquet_without_parquet_save(self, tmp_path):
        node = service_chain_input(chain_data=[{"a": 1}], outputs={"pdc-0": output_with(existing_parquet(tmp_path))})
        assert await node.process() == StatusNode.Error
        assert node.statusMessage == "Output node data is not of type NodeDataPandasDf"

    async def test_missing_data_source(self):
        node = service_chain_input()
        node.data = {"inputsDatasource": EXAMPLES}
        assert await node.process() == StatusNode.Error
        assert node.statusMessage == "No data source selected"
        assert "ValueError" in "".join(node.errorStackTrace)

    async def test_missing_examples(self):
        node = service_chain_input()
        node.data = {"selectDataSource": control("ds1")}
        assert await node.process(sample=True) == StatusNode.Error
        assert node.statusMessage == "No datasource example"

    async def test_dataset_service_failure_is_raised(self):
        node = service_chain_input()
        node.datasetService.get_dataset.side_effect = RuntimeError("database is down")
        with pytest.raises(RuntimeError, match="database is down"):
            await node.process()
