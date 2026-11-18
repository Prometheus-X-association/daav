"""
Unit tests for the process method of the MongoDB, MySQL, PDC, service chain and Elasticsearch output nodes
(databases and HTTP calls mocked).
"""
import json
import os
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import mongomock
import pandas as pd
import pyarrow.parquet as pq
import pytest
from sqlalchemy import create_engine

from app.enums.status_node import StatusNode
from app.models.interface.dataset_interface import ElasticDataset, MongoDataset, MysqlDataset
from app.models.interface.node_data import NodeDataPandasDf, NodeDataParquet
from app.nodes.outputs.elastic_output import ElasticOutput
from app.nodes.outputs.mongo_output import MongoOutput
from app.nodes.outputs.mysql_output import MysqlOutput
from app.nodes.outputs.pdc_output import PdcOutput
from app.nodes.outputs.service_chain_output import ServiceChainOutput

pytestmark = pytest.mark.asyncio

ROWS = [{"a": 1, "b": "x"}, {"a": 2, "b": "y"}, {"a": 3, "b": "z"}]
MANY_ROWS = [{"a": i, "b": f"row{i}"} for i in range(2500)]  # three batches of 1000


def control(value):
    return {"value": value}


def connected_input(node_data):
    node_input = Mock()
    node_input.get_connected_node.return_value = Mock()
    node_input.get_node_data.return_value = node_data
    return node_input


def unconnected_input():
    node_input = Mock()
    node_input.get_connected_node.return_value = None
    return node_input


def pandas_data(rows=ROWS, sample_rows=1):
    df = pd.DataFrame(rows)
    return NodeDataPandasDf(nodeSchema=[], data=df, dataExample=df.head(sample_rows), name="in")


def parquet_data(tmp_path, rows=ROWS, name="in.parquet"):
    path = str(tmp_path / name)
    pd.DataFrame(rows).to_parquet(path)
    return NodeDataParquet(data=path, nodeSchema=pq.ParquetFile(path).schema, name="in")


# ===========================
# MONGO OUTPUT
# ===========================

class FakeMongo:
    """Stands in for the MongoDB server: records the requested URIs and serves one mongomock client."""

    def __init__(self):
        self.uris = []
        self.client = mongomock.MongoClient()
        self.client.close = Mock()

    def connect(self, uri):
        self.uris.append(uri)
        return self.client

    def docs(self, collection="orders", database="shop"):
        return list(self.client[database][collection].find({}, {"_id": 0}))


def mongo_output(node_data, if_exist="append", **data):
    node = MongoOutput(id="out", data={"selectDataSource": control("ds1"), "selectExist": control(if_exist), **data})
    dataset = MongoDataset.model_construct(id="ds1", type="mongo", name="mg", uri="mongodb://db.example.com",
                                           database="shop", collection="orders", table="orders")
    node.datasetService = Mock(get_dataset=AsyncMock(return_value=dataset))
    node.inputs = {"in": connected_input(node_data)}
    return node


@pytest.fixture
def mongo():
    fake = FakeMongo()
    with patch("app.nodes.outputs.mongo_output.MongoClient", fake.connect):
        yield fake


class TestMongoOutput:

    async def test_missing_collection_is_created_and_filled(self, mongo):
        node = mongo_output(pandas_data(), if_exist="fail")
        assert await node.process() == StatusNode.Valid
        assert mongo.uris == ["mongodb://db.example.com"]
        assert mongo.docs() == ROWS
        mongo.client.close.assert_called_once_with()

    async def test_fail_on_an_existing_collection(self, mongo):
        mongo.client["shop"]["orders"].insert_one({"a": 0, "b": "old"})
        node = mongo_output(pandas_data(), if_exist="fail")
        assert await node.process() == StatusNode.Error
        assert node.statusMessage == "Collection 'orders' already exists and ifExist is set to 'fail'"
        assert "ValueError" in "".join(node.errorStackTrace)
        assert mongo.docs() == [{"a": 0, "b": "old"}]
        mongo.client.close.assert_called_once_with()

    async def test_replace_drops_the_existing_documents(self, mongo):
        mongo.client["shop"]["orders"].insert_one({"a": 0, "b": "old"})
        node = mongo_output(pandas_data(), if_exist="replace")
        assert await node.process() == StatusNode.Valid
        assert mongo.docs() == ROWS

    async def test_append_keeps_the_existing_documents(self, mongo):
        mongo.client["shop"]["orders"].insert_one({"a": 0, "b": "old"})
        node = mongo_output(pandas_data(), if_exist="append")
        assert await node.process() == StatusNode.Valid
        assert mongo.docs() == [{"a": 0, "b": "old"}] + ROWS

    async def test_node_parameters_select_the_database_and_collection(self, mongo):
        node = mongo_output(pandas_data(), selectDatabaseDataSource=control("crm"),
                            collectionAutoComplete=control("contacts"))
        assert await node.process() == StatusNode.Valid
        assert mongo.docs("contacts", "crm") == ROWS
        assert mongo.docs() == []

    async def test_dataframe_larger_than_a_chunk(self, mongo):
        node = mongo_output(pandas_data(MANY_ROWS))
        assert await node.process() == StatusNode.Valid
        assert mongo.docs() == MANY_ROWS

    async def test_dataframe_sample(self, mongo):
        node = mongo_output(pandas_data(sample_rows=2))
        assert await node.process(sample=True) == StatusNode.Valid
        assert mongo.docs() == ROWS[:2]

    async def test_parquet_is_inserted_by_batches(self, mongo, tmp_path):
        node = mongo_output(parquet_data(tmp_path, MANY_ROWS))
        assert await node.process() == StatusNode.Valid
        assert mongo.docs() == MANY_ROWS

    async def test_parquet_sample_reads_the_first_batch_only(self, mongo, tmp_path):
        node = mongo_output(parquet_data(tmp_path, MANY_ROWS))
        assert await node.process(sample=True) == StatusNode.Valid
        docs = mongo.docs()
        # Known: the sample is the first batch, it is not cut to 20 rows
        assert 0 < len(docs) <= 1000
        assert docs == MANY_ROWS[:len(docs)]

    async def test_several_inputs_are_written_in_order(self, mongo, tmp_path):
        node = mongo_output(pandas_data())
        node.inputs = {"in": connected_input(pandas_data()), "free": unconnected_input(),
                       "in2": connected_input(parquet_data(tmp_path, [{"a": 9, "b": "p"}]))}
        assert await node.process() == StatusNode.Valid
        assert mongo.docs() == ROWS + [{"a": 9, "b": "p"}]
        node.inputs["free"].get_node_data.assert_not_called()

    async def test_no_connected_input_only_creates_the_collection(self, mongo):
        node = mongo_output(pandas_data())
        node.inputs = {"free": unconnected_input()}
        assert await node.process() == StatusNode.Valid
        assert mongo.client["shop"].list_collection_names() == ["orders"]
        assert mongo.docs() == []

    async def test_unsupported_data_type(self, mongo):
        node = mongo_output(object())
        assert await node.process() == StatusNode.Error
        assert node.statusMessage == "Unsupported data type: <class 'object'>"
        assert "TypeError" in "".join(node.errorStackTrace)
        mongo.client.close.assert_called_once_with()

    async def test_missing_dataframe(self, mongo):
        node = mongo_output(NodeDataPandasDf(nodeSchema=[], dataExample=pd.DataFrame(ROWS), name="in"))
        assert await node.process() == StatusNode.Error
        assert node.statusMessage == "Input data is not a pandas DataFrame"

    async def test_missing_data_source(self, mongo):
        node = mongo_output(pandas_data())
        node.data = {}
        assert await node.process() == StatusNode.Error
        assert node.statusMessage == "No data source selected"
        assert "ValueError" in "".join(node.errorStackTrace)
        assert mongo.uris == []

    async def test_dataset_service_failure_is_raised(self, mongo):
        node = mongo_output(pandas_data())
        node.datasetService.get_dataset.side_effect = RuntimeError("database is down")
        with pytest.raises(RuntimeError, match="database is down"):
            await node.process()


# ===========================
# MYSQL OUTPUT
# ===========================

class FakeMysql:
    """Stands in for the MySQL server: serves a SQLite file engine and records the calls of DataFrame.to_sql."""

    def __init__(self, tmp_path):
        # A file, not memory: the node disposes of its engine, which would drop an in-memory database
        self.engine = create_engine(f"sqlite:///{tmp_path / 'mysql.db'}")
        self.writes = []
        self._to_sql = pd.DataFrame.to_sql

    def create_engine(self, url, *args, **kwargs):
        return self.engine

    def to_sql(self, df, name, con=None, **kwargs):
        self.writes.append((name, len(df), kwargs.get("if_exists"), kwargs.get("index"), kwargs.get("index_label")))
        return self._to_sql(df, name, con, **kwargs)

    def rows(self, table="orders"):
        return pd.read_sql(f"SELECT * FROM {table}", self.engine)


def mysql_output(node_data, if_exist="replace", **data):
    node = MysqlOutput(id="out", data={"selectDataSource": control("ds1"), "selectExist": control(if_exist), **data})
    dataset = MysqlDataset.model_construct(id="ds1", type="mysql", name="my", host="db.example.com",
                                           user="bob", password="secret", database="shop", table="orders")
    node.datasetService = Mock(get_dataset=AsyncMock(return_value=dataset))
    node.inputs = {"in": connected_input(node_data)}
    return node


@pytest.fixture
def mysql(tmp_path):
    fake = FakeMysql(tmp_path)
    with patch("app.nodes.outputs.mysql_output.create_engine", fake.create_engine), \
            patch.object(pd.DataFrame, "to_sql", lambda df, name, con=None, **kwargs: fake.to_sql(df, name, con, **kwargs)):
        yield fake


class TestMysqlOutput:

    async def test_dataframe_is_written_with_the_node_parameters(self, mysql):
        node = mysql_output(pandas_data(), if_exist="append", tableAutoComplete=control("contacts"),
                            createIndex=control(True), indexTable=control("code"))
        assert await node.process() == StatusNode.Valid
        assert mysql.writes == [("contacts", 3, "append", True, "code")]
        assert mysql.rows("contacts").to_dict(orient="records") == [
            {"code": 0, "a": 1, "b": "x"}, {"code": 1, "a": 2, "b": "y"}, {"code": 2, "a": 3, "b": "z"}]

    async def test_dataframe_sample(self, mysql):
        node = mysql_output(pandas_data(sample_rows=2))
        assert await node.process(sample=True) == StatusNode.Valid
        assert mysql.writes == [("orders", 2, "replace", False, "id")]
        assert mysql.rows().to_dict(orient="records") == ROWS[:2]

    async def test_parquet_replaces_with_the_first_batch_then_appends(self, mysql, tmp_path):
        pd.DataFrame([{"a": -1, "b": "old"}]).to_sql("orders", mysql.engine, index=False)
        mysql.writes.clear()
        node = mysql_output(parquet_data(tmp_path, MANY_ROWS), if_exist="replace")
        assert await node.process() == StatusNode.Valid
        assert mysql.writes == [("orders", 1000, "replace", False, "id"), ("orders", 1000, "append", False, "id"),
                                ("orders", 500, "append", False, "id")]
        assert mysql.rows().to_dict(orient="records") == MANY_ROWS

    async def test_parquet_append_keeps_the_existing_rows(self, mysql, tmp_path):
        pd.DataFrame([{"a": -1, "b": "old"}]).to_sql("orders", mysql.engine, index=False)
        node = mysql_output(parquet_data(tmp_path), if_exist="append")
        assert await node.process() == StatusNode.Valid
        assert mysql.rows().to_dict(orient="records") == [{"a": -1, "b": "old"}] + ROWS

    async def test_parquet_fail_on_an_existing_table(self, mysql, tmp_path):
        pd.DataFrame([{"a": -1, "b": "old"}]).to_sql("orders", mysql.engine, index=False)
        node = mysql_output(parquet_data(tmp_path, MANY_ROWS), if_exist="fail")
        assert await node.process() == StatusNode.Error
        assert node.statusMessage == "Table 'orders' already exists."
        assert mysql.rows().to_dict(orient="records") == [{"a": -1, "b": "old"}]

    async def test_parquet_sample_writes_twenty_rows(self, mysql, tmp_path):
        node = mysql_output(parquet_data(tmp_path, MANY_ROWS), if_exist="fail")
        assert await node.process(sample=True) == StatusNode.Valid
        assert mysql.writes == [("orders", 20, "fail", False, "id")]
        assert mysql.rows().to_dict(orient="records") == MANY_ROWS[:20]

    async def test_several_inputs_are_written_in_order(self, mysql, tmp_path):
        node = mysql_output(pandas_data(), if_exist="append")
        node.inputs = {"in": connected_input(pandas_data()), "free": unconnected_input(),
                       "in2": connected_input(parquet_data(tmp_path, [{"a": 9, "b": "p"}]))}
        assert await node.process() == StatusNode.Valid
        assert mysql.rows().to_dict(orient="records") == ROWS + [{"a": 9, "b": "p"}]
        node.inputs["free"].get_node_data.assert_not_called()

    async def test_no_connected_input_writes_nothing(self, mysql):
        node = mysql_output(pandas_data())
        node.inputs = {"free": unconnected_input()}
        assert await node.process() == StatusNode.Valid
        assert mysql.writes == []

    async def test_engine_is_disposed(self):
        engine = Mock()
        node = mysql_output(pandas_data())
        with patch("app.nodes.outputs.mysql_output.create_engine", return_value=engine), \
                patch.object(pd.DataFrame, "to_sql") as to_sql:
            assert await node.process() == StatusNode.Valid
        assert to_sql.call_args.kwargs["con"] is engine
        engine.dispose.assert_called_once_with()

    async def test_engine_is_disposed_after_an_error(self):
        engine = Mock()
        node = mysql_output(pandas_data())
        with patch("app.nodes.outputs.mysql_output.create_engine", return_value=engine), \
                patch.object(pd.DataFrame, "to_sql", side_effect=RuntimeError("write refused")):
            assert await node.process() == StatusNode.Error
        assert node.statusMessage == "write refused"
        assert "RuntimeError" in "".join(node.errorStackTrace)
        engine.dispose.assert_called_once_with()

    async def test_unsupported_data_type(self, mysql):
        node = mysql_output(object())
        assert await node.process() == StatusNode.Error
        assert node.statusMessage == "Unsupported data type: <class 'object'>"
        assert "TypeError" in "".join(node.errorStackTrace)

    async def test_missing_dataframe(self, mysql):
        node = mysql_output(NodeDataPandasDf(nodeSchema=[], dataExample=pd.DataFrame(ROWS), name="in"))
        assert await node.process() == StatusNode.Error
        assert node.statusMessage == "Input data is not a pandas DataFrame"

    async def test_missing_data_source(self, mysql):
        node = mysql_output(pandas_data())
        node.data = {}
        assert await node.process() == StatusNode.Error
        assert node.statusMessage == "No data source selected"
        assert "ValueError" in "".join(node.errorStackTrace)

    async def test_dataset_service_failure_is_raised(self, mysql):
        node = mysql_output(pandas_data())
        node.datasetService.get_dataset.side_effect = RuntimeError("database is down")
        with pytest.raises(RuntimeError, match="database is down"):
            await node.process()


# ===========================
# PDC OUTPUT AND SERVICE CHAIN OUTPUT
# ===========================

CHAIN_HEADERS = Mock(x_ptx_service_chain_id="chain-1", x_ptx_target_id="target-1")
RESUME_URL = "http://pdc.example.com/service-chain/resume"


def response_body(data, chained=True, params=None):
    return {"chainId": "chain-1" if chained else "", "targetId": "target-1" if chained else "",
            "data": data, "params": params}


def assert_resumed(post, body):
    post.assert_called_once_with(RESUME_URL, headers={"Content-Type": "application/json"}, json=body)


@pytest.fixture
def post():
    with patch("requests.post") as post:
        yield post


@pytest.fixture
def cache_file(tmp_path):
    path = str(tmp_path / "pdc1-output.json")
    with patch.object(PdcOutput, "get_output_file_path", return_value=path):
        yield path


def read_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def pdc_output(node_data, chain_headers=None, workflows=()):
    node = PdcOutput(id="pdc1", data={"selectDataSource": control("ds1"), "urlInput": control("my-data")})
    node.datasetService = Mock(get_dataset=AsyncMock(return_value=Mock(url="http://pdc.example.com")),
                               pdcChainHeaders=chain_headers)
    node.workflowService = Mock(get_workflows=AsyncMock(return_value=list(workflows)))
    node.inputs = {"in": connected_input(node_data)}
    return node


def workflow_with_pdc_output(node_id, url):
    other = Mock(type="PdcOutput", id=node_id, data={"urlInput": control(url)})
    return Mock(pschema=Mock(nodes=[other]))


class TestPdcOutput:

    async def test_without_chain_headers_only_the_cache_file_is_written(self, cache_file, post):
        node = pdc_output(pandas_data())
        assert await node.process() == StatusNode.Valid
        assert read_json(cache_file) == response_body(ROWS, chained=False)
        post.assert_not_called()

    async def test_chain_is_resumed_with_the_response(self, cache_file, post):
        node = pdc_output(pandas_data(), CHAIN_HEADERS)
        assert await node.process() == StatusNode.Valid
        assert read_json(cache_file) == response_body(ROWS)
        assert_resumed(post, response_body(ROWS))

    async def test_dataframe_sample(self, cache_file, post):
        node = pdc_output(pandas_data(sample_rows=2), CHAIN_HEADERS)
        assert await node.process(sample=True) == StatusNode.Valid
        assert read_json(cache_file) == response_body(ROWS[:2])
        assert_resumed(post, response_body(ROWS[:2]))

    async def test_parquet_is_converted_to_json(self, cache_file, post, tmp_path):
        node = pdc_output(parquet_data(tmp_path), CHAIN_HEADERS)
        assert await node.process() == StatusNode.Valid
        assert read_json(cache_file) == response_body(ROWS)
        assert_resumed(post, response_body(ROWS))

    async def test_url_used_by_another_node(self, cache_file, post):
        node = pdc_output(pandas_data(), CHAIN_HEADERS, [workflow_with_pdc_output("other", "my-data")])
        assert await node.process() == StatusNode.Error
        assert node.statusMessage == "URL 'my-data' is already in use"
        assert node.errorStackTrace is None
        assert not os.path.exists(cache_file)
        post.assert_not_called()

    async def test_url_of_the_node_itself_is_accepted(self, cache_file, post):
        node = pdc_output(pandas_data(), None, [workflow_with_pdc_output("pdc1", "my-data"),
                                                workflow_with_pdc_output("other", "another-url")])
        assert await node.process() == StatusNode.Valid

    async def test_unsupported_data_type(self, cache_file, post):
        node = pdc_output(object(), CHAIN_HEADERS)
        assert await node.process() == StatusNode.Error
        assert node.statusMessage == "Unsopported datatype: <class 'object'>"
        assert "TypeError" in "".join(node.errorStackTrace)
        post.assert_not_called()

    async def test_no_connected_input(self, cache_file, post):
        node = pdc_output(pandas_data(), CHAIN_HEADERS)
        node.inputs = {"free": unconnected_input()}
        assert await node.process() == StatusNode.Error
        assert node.statusMessage == "No data was generated"
        assert node.errorStackTrace is None
        post.assert_not_called()

    async def test_several_inputs_resume_the_chain_once_each(self, cache_file, post):
        node = pdc_output(pandas_data(), CHAIN_HEADERS)
        node.inputs = {"in": connected_input(pandas_data()), "free": unconnected_input(),
                       "in2": connected_input(pandas_data([{"a": 9, "b": "p"}]))}
        assert await node.process() == StatusNode.Valid
        assert [call.kwargs["json"]["data"] for call in post.call_args_list] == [ROWS, [{"a": 9, "b": "p"}]]
        assert read_json(cache_file) == response_body([{"a": 9, "b": "p"}])

    async def test_http_failure_is_a_node_error(self, cache_file, post):
        post.side_effect = RuntimeError("connector is down")
        node = pdc_output(pandas_data(), CHAIN_HEADERS)
        assert await node.process() == StatusNode.Error
        assert node.statusMessage == "connector is down"
        assert "RuntimeError" in "".join(node.errorStackTrace)

    async def test_missing_data_source_is_raised(self, cache_file, post):
        node = pdc_output(pandas_data())
        node.data = {}
        with pytest.raises(ValueError, match="No data source selected"):
            await node.process()


def service_chain_output(node_data, chain_headers=None):
    node = ServiceChainOutput(id="chain-out", data={"selectDataSource": control("ds1")})
    node.datasetService = Mock(get_dataset=AsyncMock(return_value=Mock(url="http://pdc.example.com")),
                               pdcChainHeaders=chain_headers)
    node.inputs = {"in": connected_input(node_data)}
    return node


FOO = {"foo": "bar"}


class TestServiceChainOutput:

    async def test_without_chain_headers_nothing_is_sent(self, post):
        node = service_chain_output(pandas_data())
        assert await node.process() == StatusNode.Valid
        post.assert_not_called()

    async def test_chain_is_resumed_with_the_response(self, post):
        node = service_chain_output(pandas_data(), CHAIN_HEADERS)
        assert await node.process() == StatusNode.Valid
        assert_resumed(post, response_body(ROWS, params=FOO))

    async def test_dataframe_sample(self, post):
        node = service_chain_output(pandas_data(sample_rows=2), CHAIN_HEADERS)
        assert await node.process(sample=True) == StatusNode.Valid
        assert_resumed(post, response_body(ROWS[:2], params=FOO))

    async def test_unsupported_data_type(self, post):
        node = service_chain_output(object(), CHAIN_HEADERS)
        assert await node.process() == StatusNode.Error
        assert node.statusMessage == "Unsupported datatype: <class 'object'>"
        assert "TypeError" in "".join(node.errorStackTrace)
        post.assert_not_called()

    async def test_no_connected_input(self, post):
        node = service_chain_output(pandas_data(), CHAIN_HEADERS)
        node.inputs = {"free": unconnected_input()}
        assert await node.process() == StatusNode.Valid
        post.assert_not_called()

    async def test_several_inputs_resume_the_chain_once_each(self, post):
        node = service_chain_output(pandas_data(), CHAIN_HEADERS)
        node.inputs = {"in": connected_input(pandas_data()), "free": unconnected_input(),
                       "in2": connected_input(pandas_data([{"a": 9, "b": "p"}]))}
        assert await node.process() == StatusNode.Valid
        assert [call.kwargs["json"]["data"] for call in post.call_args_list] == [ROWS, [{"a": 9, "b": "p"}]]

    async def test_http_failure_is_a_node_error(self, post):
        post.side_effect = RuntimeError("connector is down")
        node = service_chain_output(pandas_data(), CHAIN_HEADERS)
        assert await node.process() == StatusNode.Error
        assert node.statusMessage == "connector is down"

    async def test_missing_data_source_is_raised(self, post):
        node = service_chain_output(pandas_data())
        node.data = {}
        with pytest.raises(ValueError, match="No data source selected"):
            await node.process()


# ===========================
# ELASTIC OUTPUT
# ===========================

def elastic_output(*node_inputs):
    node = ElasticOutput(id="out", data={"selectDataSource": control("ds1"), "indexAutoComplete": control("target")})
    dataset = ElasticDataset.model_construct(id="ds1", type="elastic", name="es", url="https://es.example.com",
                                             verifyCerts=True)
    node.datasetService = Mock(get_dataset=AsyncMock(return_value=dataset))
    client = MagicMock()
    client.indices.exists.return_value = False
    node.elasticService = Mock()
    node.elasticService.connect.return_value.__enter__ = Mock(return_value=client)
    node.elasticService.connect.return_value.__exit__ = Mock(return_value=False)
    node.elasticService.bulk_index.side_effect = lambda client, index, records, id_field=None: (len(records), 0, [])
    node.inputs = {f"in{position}": node_input for position, node_input in enumerate(node_inputs)}
    return node


def indexed_records(node):
    return [call.args[2] for call in node.elasticService.bulk_index.call_args_list]


class TestElasticOutputChunks:

    async def test_dataframe_is_indexed_by_chunks(self):
        node = elastic_output(connected_input(pandas_data(MANY_ROWS)))
        assert await node.process() == StatusNode.Valid
        assert indexed_records(node) == [MANY_ROWS[:1000], MANY_ROWS[1000:2000], MANY_ROWS[2000:]]

    async def test_parquet_is_indexed_by_batches(self, tmp_path):
        node = elastic_output(connected_input(parquet_data(tmp_path, MANY_ROWS)))
        assert await node.process() == StatusNode.Valid
        assert indexed_records(node) == [MANY_ROWS[:1000], MANY_ROWS[1000:2000], MANY_ROWS[2000:]]
        assert node.statusMessage == "2500 documents indexed into 'target'"

    async def test_parquet_sample_reads_the_first_batch_only(self, tmp_path):
        node = elastic_output(connected_input(parquet_data(tmp_path, MANY_ROWS)))
        assert await node.process(sample=True) == StatusNode.Valid
        assert indexed_records(node) == [MANY_ROWS[:1000]]

    async def test_several_inputs_are_indexed_in_order(self, tmp_path):
        free = unconnected_input()
        node = elastic_output(connected_input(pandas_data()), free,
                              connected_input(parquet_data(tmp_path, [{"a": 9, "b": "p"}])))
        assert await node.process() == StatusNode.Valid
        assert indexed_records(node) == [ROWS, [{"a": 9, "b": "p"}]]
        free.get_node_data.assert_not_called()

    async def test_no_connected_input(self):
        node = elastic_output(unconnected_input())
        assert await node.process() == StatusNode.Error
        assert node.statusMessage == "No input data connected"

    async def test_unsupported_data_type(self):
        node = elastic_output(connected_input(object()))
        assert await node.process() == StatusNode.Error
        assert node.statusMessage == "Unsupported data type: <class 'object'>"

    async def test_missing_dataframe(self):
        node = elastic_output(connected_input(NodeDataPandasDf(nodeSchema=[], dataExample=pd.DataFrame(ROWS),
                                                               name="in")))
        assert await node.process() == StatusNode.Error
        assert node.statusMessage == "Input data is not a pandas DataFrame"
