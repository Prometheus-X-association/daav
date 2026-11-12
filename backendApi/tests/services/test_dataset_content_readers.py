"""
Tests for the MySQL, MongoDB and API content readers: get_mysql_content, get_mongo_content,
serialize_id, get_api_content (routes/datasets.py), get_content_dataset, and
DatasetService.getDfMongoContent and getDfMysqlContent.
"""
import base64
import functools
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import httpx
import mongomock
import mysql.connector
import pandas as pd
import pytest
from bson import ObjectId
from fastapi import HTTPException
from pymongo.errors import ConnectionFailure

from app.models.interface.dataset_interface import (
    ApiDataset, ConnectionInfo, DatasetParams, ElasticDataset, FileDataset, MongoDataset, MysqlDataset,
    Pagination, PTXDataset,
)
from app.routes import datasets
from app.routes.datasets import (
    get_api_content, get_content_dataset, get_mongo_content, get_mysql_content, rem_object_id, serialize_id,
)
from app.services.dataset_service import DatasetService


def _http_error(func, *args):
    with pytest.raises(HTTPException) as exc_info:
        func(*args)
    return exc_info.value.status_code, exc_info.value.detail


async def _async_http_error(coro):
    with pytest.raises(HTTPException) as exc_info:
        await coro
    return exc_info.value.status_code, exc_info.value.detail


# ===========================
# get_mysql_content
# ===========================

class FakeCursor:
    """A dictionary cursor over a fake server: {database: {table: rows}}."""

    def __init__(self, server):
        self.server = server
        self.executed = []
        self.database = None
        self.closed = False
        self._result = []

    def execute(self, query):
        self.executed.append(query)
        if query == "SHOW DATABASES":
            self._result = [{"Database": name.encode() if name == "shop" else name} for name in self.server]
        elif query.startswith("USE "):
            self.database = query[4:]
        elif query == "SHOW TABLES":
            self._result = [{f"Tables_in_{self.database}": name} for name in self.server[self.database]]
        elif query.startswith("DESCRIBE "):
            rows = self.server[self.database][query[9:]]
            self._result = [{"Field": key} for key in rows[0]]
        elif query.startswith("SELECT COUNT(*) FROM "):
            self._result = [{"COUNT(*)": len(self.server[self.database][query[21:]])}]
        elif query.startswith("SELECT * FROM "):
            table, _, limit, _, offset = query[14:].split(" ")
            rows = self.server[self.database][table]
            self._result = rows[int(offset):int(offset) + int(limit)]

    def fetchall(self):
        return self._result

    def fetchone(self):
        return self._result[0]

    def close(self):
        self.closed = True


SERVER = {
    "shop": {"orders": [{"id": i} for i in range(5)], "clients": [{"id": 1, "name": "a"}]},
    "crm": {"contacts": [{"id": 1}]},
    "mysql": {"user": [{"id": 1}]},
    "information_schema": {"tables": [{"id": 1}]},
}


@pytest.fixture
def mysql_server():
    cursor = FakeCursor(SERVER)
    conn = MagicMock()
    conn.cursor.return_value = cursor
    with patch("app.routes.datasets.mysql.connector.connect", return_value=conn) as connect:
        yield connect, conn, cursor


def _mysql(database=None, table=None):
    return MysqlDataset.model_construct(id="m1", type="mysql", name="my", host="h", user="u", password="p",
                                        database=database, table=table)


class TestGetMysqlContent:

    def test_lists_databases_and_tables(self, mysql_server):
        connect, conn, cursor = mysql_server

        response = get_mysql_content(_mysql(), Pagination(page=1, perPage=10), DatasetParams())

        assert response.databases == ["shop", "crm"]
        assert response.tables == [["orders", "clients"], ["contacts"]]
        assert response.data == []
        connect.assert_called_once_with(host="h", user="u", password="p", auth_plugin="mysql_native_password")
        assert cursor.closed
        conn.close.assert_called_once()

    @pytest.mark.parametrize("dataset_db, param_db, expected", [
        ("shop", None, ["orders", "clients"]),
        (None, "crm", ["contacts"]),
        ("shop", "crm", ["contacts"]),
    ])
    def test_lists_tables_of_a_database(self, mysql_server, dataset_db, param_db, expected):
        response = get_mysql_content(_mysql(database=dataset_db), Pagination(page=1, perPage=10),
                                     DatasetParams(database=param_db))

        assert response.tables == expected
        assert response.databases is None
        assert response.data == []

    def test_reads_a_page_of_a_table(self, mysql_server):
        _, _, cursor = mysql_server

        response = get_mysql_content(_mysql(database="shop", table="orders"), Pagination(page=2, perPage=2),
                                     DatasetParams())

        assert response.data == [{"id": 2}, {"id": 3}]
        assert response.total_rows == 5
        assert response.current_page == 2
        assert response.limit == 2
        assert response.table_description == [{"Field": "id"}]
        assert cursor.executed == ["USE shop", "DESCRIBE orders", "SELECT COUNT(*) FROM orders",
                                   "SELECT * FROM orders LIMIT 2 OFFSET 2"]

    def test_parameters_and_dataset_precedence(self, mysql_server):
        _, _, cursor = mysql_server

        # The database of the parameters wins, the table of the dataset wins
        response = get_mysql_content(_mysql(database="crm", table="clients"), Pagination(page=1, perPage=10),
                                     DatasetParams(database="shop", table="orders"))

        assert response.data == [{"id": 1, "name": "a"}]
        assert cursor.executed[0] == "USE shop"

    def test_table_from_the_parameters(self, mysql_server):
        response = get_mysql_content(_mysql(database="shop"), Pagination(page=1, perPage=10),
                                     DatasetParams(table="clients"))

        assert response.total_rows == 1

    def test_connection_error_is_a_503(self):
        error = mysql.connector.Error("Can't connect")
        with patch("app.routes.datasets.mysql.connector.connect", side_effect=error):
            status, detail = _http_error(get_mysql_content, _mysql(), Pagination(page=1, perPage=10),
                                         DatasetParams())

        assert status == 503
        assert detail == f"Database error: {error}"

    def test_query_error_is_a_503_and_closes_the_connection(self, mysql_server):
        _, conn, cursor = mysql_server
        with patch.object(cursor, "execute", side_effect=mysql.connector.Error("Unknown table")):
            status, _ = _http_error(get_mysql_content, _mysql(database="shop", table="x"),
                                    Pagination(page=1, perPage=10), DatasetParams())

        assert status == 503
        assert cursor.closed
        conn.close.assert_called_once()

    def test_permission_error_is_a_403(self, mysql_server):
        _, _, cursor = mysql_server
        with patch.object(cursor, "execute", side_effect=PermissionError("denied")):
            assert _http_error(get_mysql_content, _mysql(), Pagination(page=1, perPage=10), DatasetParams()) == (
                403, "Permission error: denied")


# ===========================
# get_mongo_content and serialize_id
# ===========================

@pytest.fixture
def mongo_client():
    client = mongomock.MongoClient()
    client.shop.orders.insert_many([{"_id": ObjectId(), "n": i} for i in range(5)])
    client.shop.clients.insert_one({"name": "a"})
    client.crm.contacts.insert_one({"name": "b"})
    client.config.system.insert_one({"x": 1})
    with patch("pymongo.mongo_client.MongoClient", return_value=client) as factory:
        yield factory, client


def _mongo(database=None, collection=None):
    return MongoDataset.model_construct(id="g1", type="mongo", name="mg", uri="mongodb://db.example.com",
                                        database=database, collection=collection)


class TestGetMongoContent:

    def test_lists_databases_and_collections(self, mongo_client):
        response = get_mongo_content(_mongo(), Pagination(page=1, perPage=10), DatasetParams())

        assert response.databases == ["shop", "crm"]
        assert [sorted(names) for names in response.collections] == [["clients", "orders"], ["contacts"]]
        assert response.data == []

    def test_lists_databases_with_a_table_parameter(self, mongo_client):
        response = get_mongo_content(_mongo(), Pagination(page=1, perPage=10), DatasetParams(table="orders"))

        assert response.databases == ["shop", "crm"]

    @pytest.mark.parametrize("dataset_db, param_db, expected", [
        ("shop", None, ["clients", "orders"]),
        (None, "crm", ["contacts"]),
        ("shop", "crm", ["clients", "orders"]),
    ])
    def test_lists_collections_of_a_database(self, mongo_client, dataset_db, param_db, expected):
        response = get_mongo_content(_mongo(database=dataset_db), Pagination(page=1, perPage=10),
                                     DatasetParams(database=param_db))

        assert sorted(response.collections) == expected
        assert response.databases is None
        assert response.data == []

    def test_reads_a_page_of_a_collection(self, mongo_client):
        _, client = mongo_client
        ids = [str(doc["_id"]) for doc in client.shop.orders.find({})]

        response = get_mongo_content(_mongo(database="shop", collection="orders"), Pagination(page=2, perPage=2),
                                     DatasetParams())

        assert response.data == [{"_id": ids[2], "n": 2}, {"_id": ids[3], "n": 3}]
        assert response.total_rows == 5
        assert response.limit == 2
        assert response.current_page == 2

    @pytest.mark.parametrize("dataset_db, dataset_col, params, expected_total", [
        (None, None, DatasetParams(database="shop", table="clients"), 1),
        ("crm", None, DatasetParams(database="shop", table="contacts"), 1),
        ("shop", "orders", DatasetParams(database="crm", table="contacts"), 5),
    ])
    def test_dataset_takes_precedence(self, mongo_client, dataset_db, dataset_col, params, expected_total):
        response = get_mongo_content(_mongo(database=dataset_db, collection=dataset_col),
                                     Pagination(page=1, perPage=10), params)

        assert response.total_rows == expected_total

    def test_client_is_closed(self, mongo_client):
        _, client = mongo_client
        with patch.object(client, "close") as close:
            get_mongo_content(_mongo(database="shop"), Pagination(page=1, perPage=10), DatasetParams())

        close.assert_called_once()

    def test_permission_error_is_a_403(self):
        with patch("pymongo.mongo_client.MongoClient", side_effect=PermissionError("denied")):
            assert _http_error(get_mongo_content, _mongo(), Pagination(page=1, perPage=10), DatasetParams()) == (
                403, "Permission error: denied")

    def test_connection_failure_is_a_503(self, mongo_client):
        _, client = mongo_client
        with patch.object(client, "list_database_names", side_effect=ConnectionFailure("down")):
            assert _http_error(get_mongo_content, _mongo(), Pagination(page=1, perPage=10), DatasetParams()) == (
                503, "Database error: down")


class TestSerializeId:

    def test_object_ids_in_nested_dicts_and_lists(self):
        a, b, c, d = (ObjectId() for _ in range(4))
        document = {
            "_id": a,
            "owner": {"ref": b, "name": "x"},
            "items": [{"ref": c, "qty": 1}, {"sub": {"ref": d}}],
            "tags": ["t1", "t2"],
            "count": 3,
        }

        assert serialize_id(document) == {
            "_id": str(a),
            "owner": {"ref": str(b), "name": "x"},
            "items": [{"ref": str(c), "qty": 1}, {"sub": {"ref": str(d)}}],
            "tags": ["t1", "t2"],
            "count": 3,
        }

    def test_rem_object_id_yields_the_keys(self):
        a = ObjectId()
        document = {"_id": a, "x": {"ref": a, "_id": a}, "l": [{"k": a}, "s", [{"z": a}], {"n": 1}]}

        assert list(rem_object_id(document)) == ["_id", "ref", "_id", "k"]
        assert list(rem_object_id("not a dict")) == []
        assert list(rem_object_id([{"_id": a}])) == []


# ===========================
# get_api_content
# ===========================

def _api(**kwargs):
    values = dict(id="a1", type="api", name="api", url="https://api.example.com/items", apiAuth=None,
                  authUrl="https://auth.example.com/token", bearerToken=None, basicToken=None)
    values.update(kwargs)
    return ApiDataset.model_construct(**values)


@pytest.fixture
def http():
    """Route the httpx clients of the module to a handler; returns the list of received requests."""
    state = {"handler": None, "requests": []}

    def dispatch(request):
        state["requests"].append(request)
        return state["handler"](request)

    real_client = httpx.AsyncClient
    factory = functools.partial(real_client, transport=httpx.MockTransport(dispatch))
    with patch("app.routes.datasets.httpx.AsyncClient", side_effect=factory):
        yield state


JSON_API = {
    "data": [{"id": "1"}, {"id": "2"}],
    "links": {"self": "s", "next": "https://api.example.com/items?page=2", "prev": None},
    "meta": {"count": 10},
}


@pytest.mark.asyncio
class TestGetApiContent:

    async def test_no_auth_and_json_api_format(self, http):
        http["handler"] = lambda request: httpx.Response(200, json=JSON_API)

        response = await get_api_content(_api(), Pagination(page=1, perPage=2))

        assert response.data == JSON_API["data"]
        assert response.total_rows == 10
        assert response.limit == 2
        assert response.current_page == 1
        assert response.next_url == "https://api.example.com/items?page=2"
        assert response.prev_url is None
        assert "authorization" not in http["requests"][0].headers

    @pytest.mark.parametrize("data, meta, expected_total", [
        ({"id": "1"}, {"total": 7}, 7),
        ([{"id": "1"}, {"id": "2"}], {}, 2),
    ])
    async def test_json_api_single_resource_and_totals(self, http, data, meta, expected_total):
        http["handler"] = lambda request: httpx.Response(200, json={"data": data, "links": {"self": "s"}, "meta": meta})

        response = await get_api_content(_api(), Pagination(page=3, perPage=5))

        assert response.data == (data if isinstance(data, list) else [data])
        assert response.total_rows == expected_total
        assert response.current_page == 3

    async def test_next_url_from_the_pagination(self, http):
        http["handler"] = lambda request: httpx.Response(200, json=[{"a": 1}])

        await get_api_content(_api(), Pagination(page=2, perPage=5, nextUrl="https://api.example.com/next"))

        assert str(http["requests"][0].url) == "https://api.example.com/next"

    async def test_bearer_token(self, http):
        http["handler"] = lambda request: httpx.Response(200, json=[{"a": 1}])

        await get_api_content(_api(apiAuth="bearer", bearerToken="tok"), Pagination(page=1, perPage=5))

        assert http["requests"][0].headers["authorization"] == "token tok"

    async def test_oauth2_post_fails_then_get_succeeds(self, http):
        def handler(request):
            if request.url.host == "auth.example.com":
                if request.method == "POST":
                    return httpx.Response(405, text="no post")
                return httpx.Response(200, json={"access_token": "acc"})
            return httpx.Response(200, json=[{"a": 1}])
        http["handler"] = handler

        response = await get_api_content(_api(apiAuth="oauth2", basicToken="id:secret"), Pagination(page=1, perPage=5))

        post, get, data = http["requests"]
        basic = base64.b64encode(b"id:secret").decode()
        assert (post.method, get.method) == ("POST", "GET")
        assert post.content == b"grant_type=client_credentials"
        assert post.headers["authorization"] == f"Basic {basic}"
        assert get.headers["authorization"] == f"Basic {basic}"
        assert data.headers["authorization"] == "Bearer acc"
        assert data.headers["access_token"] == "acc"
        assert response.data == [{"a": 1}]

    async def test_oauth2_post_succeeds(self, http):
        def handler(request):
            if request.url.host == "auth.example.com":
                return httpx.Response(200, json={"access_token": "acc"})
            return httpx.Response(200, json=[{"a": 1}])
        http["handler"] = handler

        await get_api_content(_api(apiAuth="oauth2", basicToken="id:secret"), Pagination(page=1, perPage=5))

        assert [request.method for request in http["requests"]] == ["POST", "GET"]

    async def test_oauth2_failure(self, http):
        http["handler"] = lambda request: httpx.Response(401, text="bad credentials")

        assert await _async_http_error(get_api_content(_api(apiAuth="oauth2", basicToken="id:secret"),
                                                       Pagination(page=1, perPage=5))) == (
            401, "Authentication error: bad credentials")
        assert len(http["requests"]) == 2

    async def test_custom_format(self, http):
        payload = {
            "data": [{"a": 1}, {"a": 2}, {"a": 3}],
            "count": 30,
            "self": {"href": "https://api.example.com/items?page=2"},
            "next": {"href": "https://api.example.com/items?page=3"},
            "previous": {"href": "https://api.example.com/items?page=1"},
        }
        http["handler"] = lambda request: httpx.Response(200, json=payload)

        response = await get_api_content(_api(), Pagination(page=2, perPage=5))

        assert response.data == payload["data"]
        assert response.total_rows == 30
        assert response.limit == 3
        assert response.current_page == 2
        assert response.next_url == "https://api.example.com/items?page=3"
        assert response.prev_url == "https://api.example.com/items?page=1"

    async def test_custom_format_without_links(self, http):
        payload = {"data": [{"a": 1}], "count": 1, "self": {"href": "s"}, "next": None}
        http["handler"] = lambda request: httpx.Response(200, json=payload)

        response = await get_api_content(_api(), Pagination(page=1, perPage=5))

        assert (response.next_url, response.prev_url) == (None, None)

    async def test_dict_fallback(self, http):
        http["handler"] = lambda request: httpx.Response(200, json={"a": 1, "b": [2]})

        response = await get_api_content(_api(), Pagination(page=1, perPage=5))

        assert response.data == [("a", 1), ("b", [2])]
        assert response.total_rows == 2
        assert response.limit == 5
        assert response.current_page == 1

    async def test_list_fallback(self, http):
        http["handler"] = lambda request: httpx.Response(200, json=[{"a": 1}, {"a": 2}])

        response = await get_api_content(_api(), Pagination(page=1, perPage=5))

        assert response.data == [{"a": 1}, {"a": 2}]
        assert response.total_rows == 2

    async def test_xml_response(self, http):
        xml = b"<items><item><a>1</a><b>x</b></item><item><a>2</a></item></items>"
        http["handler"] = lambda request: httpx.Response(200, content=xml, headers={"Content-Type": "application/xml"})

        response = await get_api_content(_api(), Pagination(page=1, perPage=5))

        assert response.data == [{"a": "1", "b": "x"}, {"a": "2"}]
        assert response.total_rows == 2

    async def test_http_error_status(self, http):
        http["handler"] = lambda request: httpx.Response(418, text="teapot")

        status, detail = await _async_http_error(get_api_content(_api(), Pagination(page=1, perPage=5)))

        assert status == 418
        assert detail.startswith("HTTP error: Client error '418 I'm a teapot' for url 'https://api.example.com/items'")

    @pytest.mark.parametrize("error, status, prefix", [
        (httpx.ConnectError("refused"), 404, "Connection error: refused"),
        (httpx.ReadTimeout("slow"), 504, "Timeout error: slow"),
        (httpx.RemoteProtocolError("broken"), 400, "Request error: broken"),
        (PermissionError("denied"), 403, "Permission error: denied"),
    ])
    async def test_request_errors(self, http, error, status, prefix):
        def handler(request):
            raise error
        http["handler"] = handler

        assert await _async_http_error(get_api_content(_api(), Pagination(page=1, perPage=5))) == (status, prefix)


# ===========================
# get_content_dataset
# ===========================

@pytest.mark.asyncio
class TestGetContentDataset:

    @pytest.fixture
    def request_mock(self):
        request = Mock()
        request.client.host = "10.0.0.1"
        return request

    @pytest.mark.parametrize("dataset, reader", [
        (_mongo(database="shop"), "get_mongo_content"),
        (_mysql(database="shop"), "get_mysql_content"),
        (ElasticDataset.model_construct(id=None, type="elastic", name="es"), "get_elastic_content"),
    ])
    async def test_synchronous_readers(self, request_mock, dataset, reader):
        dataset.id = None
        info = ConnectionInfo.model_construct(dataset=dataset, pagination=Pagination(page=1, perPage=5),
                                              datasetParams=DatasetParams())
        with patch.object(datasets, reader, return_value="content") as read:
            assert await get_content_dataset(request_mock, info, Mock()) == "content"
        read.assert_called_once_with(dataset, info.pagination, info.datasetParams)

    async def test_api_reader(self, request_mock):
        dataset = _api(id=None)
        info = ConnectionInfo.model_construct(dataset=dataset, pagination=Pagination(page=1, perPage=5),
                                              datasetParams=DatasetParams())
        with patch.object(datasets, "get_api_content", AsyncMock(return_value="content")) as read:
            assert await get_content_dataset(request_mock, info, Mock()) == "content"
        read.assert_awaited_once_with(dataset, info.pagination)

    async def test_ptx_dataset_is_returned(self, request_mock):
        dataset = PTXDataset.model_construct(id=None, type="ptx", name="p")
        info = ConnectionInfo.model_construct(dataset=dataset, pagination=Pagination(), datasetParams=DatasetParams())

        assert await get_content_dataset(request_mock, info, Mock()) is dataset

    async def test_stored_dataset_is_reloaded(self, request_mock):
        stored = _mongo(database="shop")
        info = ConnectionInfo.model_construct(dataset=_mongo(), pagination=Pagination(page=1, perPage=5),
                                              datasetParams=DatasetParams())
        info.dataset.id = "g1"
        user = Mock()
        with patch.object(datasets.dataset_service, "get_dataset", AsyncMock(return_value=stored)) as get_dataset, \
                patch.object(datasets, "get_mongo_content", return_value="content") as read:
            await get_content_dataset(request_mock, info, user)
        get_dataset.assert_awaited_once_with("g1", user)
        assert read.call_args.args[0] is stored

    async def test_file_reader_logs_the_access(self, request_mock):
        dataset = FileDataset.model_construct(id=None, type="file", name="f", filePath="/data/a.csv", folder=None)
        info = ConnectionInfo.model_construct(dataset=dataset, pagination=Pagination(page=1, perPage=5),
                                              datasetParams=DatasetParams())
        with patch.object(datasets, "get_file_content", return_value="content") as read, \
                patch.object(datasets, "log_file_access") as log:
            assert await get_content_dataset(request_mock, info, Mock()) == "content"
        read.assert_called_once_with(dataset, info.pagination)
        log.assert_called_once_with("10.0.0.1", "/data/a.csv", "read")

    @pytest.mark.parametrize("status, logged", [(403, True), (404, False)])
    async def test_file_reader_logs_refused_reads(self, request_mock, status, logged):
        dataset = FileDataset.model_construct(id=None, type="file", name="f", filePath="/data/a.csv",
                                              folder="/data/dir")
        info = ConnectionInfo.model_construct(dataset=dataset, pagination=Pagination(page=1, perPage=5),
                                              datasetParams=DatasetParams())
        with patch.object(datasets, "get_file_content", side_effect=HTTPException(status_code=status)), \
                patch.object(datasets, "log_file_access") as log:
            current_user = Mock()
            with pytest.raises(HTTPException):
                await get_content_dataset(request_mock, info, current_user)
        calls = [call.args for call in log.call_args_list]
        assert calls[0] == ("10.0.0.1", "/data/dir", "read")
        assert (("10.0.0.1", "/data/dir", "read_failed") in calls) is logged

    async def test_unknown_type(self, request_mock):
        info = ConnectionInfo.model_construct(dataset=Mock(id=None), pagination=Pagination(),
                                              datasetParams=DatasetParams())
        current_user = Mock()
        with pytest.raises(ValueError, match="Type de connexion non reconnu"):
            await get_content_dataset(request_mock, info, current_user)


# ===========================
# DatasetService.getDfMongoContent and getDfMysqlContent
# ===========================

@pytest.fixture
def service():
    return DatasetService()


class TestGetDfMongoContent:

    def test_whole_collection(self, service, mongo_client):
        node_data = service.getDfMongoContent(_mongo(database="shop", collection="orders"), DatasetParams())

        assert node_data.name == "orders"
        assert node_data.data["n"].tolist() == [0, 1, 2, 3, 4]
        assert node_data.dataExample is None
        assert [col.name for col in node_data.nodeSchema.root] == ["_id", "n"]

    def test_page(self, service, mongo_client):
        node_data = service.getDfMongoContent(_mongo(database="shop", collection="orders"), DatasetParams(),
                                              Pagination(page=2, perPage=2))

        assert node_data.data is None
        assert node_data.dataExample["n"].tolist() == [2, 3]

    def test_incomplete_pagination_keeps_a_sample(self, service, mongo_client):
        node_data = service.getDfMongoContent(_mongo(database="shop", collection="orders"), DatasetParams(),
                                              Pagination(page=None, perPage=3))
        no_size = service.getDfMongoContent(_mongo(database="shop", collection="orders"), DatasetParams(),
                                            Pagination(page=1, perPage=None))

        assert node_data.dataExample["n"].tolist() == [0, 1, 2]
        assert len(node_data.nodeSchema.root) == 2
        assert no_size.dataExample["n"].tolist() == [0, 1, 2, 3, 4]

    def test_parameters(self, service, mongo_client):
        node_data = service.getDfMongoContent(_mongo(), DatasetParams(database="crm", table="contacts"))

        assert node_data.name == "contacts"
        assert node_data.data["name"].tolist() == ["b"]

    @pytest.mark.parametrize("database, collection, params", [
        (None, "orders", DatasetParams()),
        ("shop", None, DatasetParams()),
        (None, None, DatasetParams(database="shop")),
    ])
    def test_missing_database_or_collection(self, service, database, collection, params):
        assert _http_error(service.getDfMongoContent, _mongo(database, collection), params) == (
            422, "Database and collection must be specified")

    def test_errors(self, service, mongo_client):
        _, client = mongo_client
        dataset = _mongo(database="shop", collection="orders")
        with patch.object(mongomock.Collection, "find", side_effect=ConnectionFailure("down")):
            assert _http_error(service.getDfMongoContent, dataset, DatasetParams()) == (503, "Database error: down")
        with patch.object(mongomock.Collection, "find", side_effect=PermissionError("denied")):
            assert _http_error(service.getDfMongoContent, dataset, DatasetParams()) == (
                403, "Permission error: denied")
        with patch.object(mongomock.Collection, "find", side_effect=RuntimeError("boom")):
            assert _http_error(service.getDfMongoContent, dataset, DatasetParams()) == (500, "Internal server error")

    def test_client_is_closed(self, service, mongo_client):
        _, client = mongo_client
        with patch.object(client, "close") as close:
            service.getDfMongoContent(_mongo(database="shop", collection="orders"), DatasetParams())

        close.assert_called_once()


class TestGetDfMysqlContent:

    @pytest.fixture
    def engine(self):
        with patch("app.services.dataset_service.create_engine") as create_engine, \
                patch("app.services.dataset_service.pd.read_sql",
                      return_value=pd.DataFrame([{"id": 1}, {"id": 2}])) as read_sql:
            yield create_engine, read_sql

    def test_whole_table(self, service, engine):
        create_engine, read_sql = engine

        node_data = service.getDfMysqlContent(_mysql(database="shop", table="orders"), DatasetParams())

        create_engine.assert_called_once_with("mysql+mysqlconnector://u:p@h/shop")
        assert read_sql.call_args.args[0] == "SELECT * FROM orders"
        assert node_data.name == "my"
        assert node_data.data["id"].tolist() == [1, 2]
        assert node_data.dataExample is None
        create_engine.return_value.dispose.assert_called_once()

    def test_page(self, service, engine):
        _, read_sql = engine

        node_data = service.getDfMysqlContent(_mysql(database="shop", table="orders"), DatasetParams(),
                                              Pagination(page=3, perPage=10))

        assert read_sql.call_args.args[0] == "SELECT * FROM orders LIMIT 10 OFFSET 20"
        assert node_data.data is None
        assert node_data.dataExample["id"].tolist() == [1, 2]

    def test_incomplete_pagination_reads_everything(self, service, engine):
        _, read_sql = engine

        node_data = service.getDfMysqlContent(_mysql(database="shop", table="orders"), DatasetParams(),
                                              Pagination(page=1))

        assert read_sql.call_args.args[0] == "SELECT * FROM orders"
        assert node_data.dataExample is not None

    def test_parameters_take_precedence(self, service, engine):
        create_engine, read_sql = engine

        service.getDfMysqlContent(_mysql(database="shop", table="orders"), DatasetParams(database="crm", table="contacts"))

        create_engine.assert_called_once_with("mysql+mysqlconnector://u:p@h/crm")
        assert read_sql.call_args.args[0] == "SELECT * FROM contacts"

    @pytest.mark.parametrize("database, table", [(None, "orders"), ("shop", None)])
    def test_missing_database_or_table(self, service, engine, database, table):
        create_engine, _ = engine

        assert _http_error(service.getDfMysqlContent, _mysql(database, table), DatasetParams()) == (
            422, "Database and table must be specified")
        create_engine.assert_not_called()

    def test_errors(self, service, engine):
        create_engine, read_sql = engine
        dataset = _mysql(database="shop", table="orders")
        error = mysql.connector.Error("refused")
        read_sql.side_effect = error
        assert _http_error(service.getDfMysqlContent, dataset, DatasetParams()) == (503, f"Database error: {error}")
        read_sql.side_effect = PermissionError("denied")
        assert _http_error(service.getDfMysqlContent, dataset, DatasetParams()) == (403, "Permission error: denied")
        read_sql.side_effect = RuntimeError("boom")
        assert _http_error(service.getDfMysqlContent, dataset, DatasetParams()) == (500, "Internal server error")
        assert create_engine.return_value.dispose.call_count == 3
