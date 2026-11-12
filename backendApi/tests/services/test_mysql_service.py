"""
Tests of MysqlService (mysql.connector mocked).
"""
from datetime import datetime
from unittest.mock import MagicMock, patch

import mysql.connector
import pytest
from mysql.connector import errorcode

from app.models.interface.dataset_interface import MysqlDataset
from app.services import mysql_service
from app.services.mysql_service import MysqlService, MysqlServiceError, _split_host


def _dataset(**kwargs):
    return MysqlDataset.model_construct(id="ds1", type="mysql", name="db", host="db.local",
                                        user="u", password="p", **kwargs)


@pytest.fixture
def cursor():
    cursor = MagicMock()
    conn = MagicMock()
    conn.cursor.return_value = cursor
    with patch.object(mysql_service.mysql.connector, "connect", return_value=conn) as connect:
        cursor.connect = connect
        cursor.conn = conn
        yield cursor


@pytest.mark.parametrize("host,expected", [
    ("db.local", ("db.local", 3306)),
    ("db.local:3307", ("db.local", 3307)),
    ("[::1]:3308", ("::1", 3308)),
    ("::1", ("::1", 3306)),
])
def test_split_host(host, expected):
    assert _split_host(host) == expected


def test_info(cursor):
    cursor.fetchall.side_effect = [
        [{"version": "8.4.0", "versionComment": "MySQL Community Server", "currentUser": "u@%",
          "charset": "utf8mb4", "collation": "utf8mb4_0900_ai_ci", "timeZone": "SYSTEM"}],
        [{"Variable_name": "Uptime", "Value": "3600"}, {"Variable_name": "Threads_connected", "Value": "2"}],
        [{"name": "shop", "charset": "utf8mb4", "collation": "c", "tables": 3,
          "approxRows": 120, "sizeBytes": 49152}],
    ]
    info = MysqlService().info(_dataset())
    assert info["version"] == "8.4.0"
    assert info["uptimeSeconds"] == 3600
    assert info["threadsConnected"] == 2
    assert info["databases"][0]["tables"] == 3
    # system databases are hidden
    assert cursor.execute.call_args_list[2].args[1] == list(mysql_service.SYSTEM_DATABASES)
    cursor.conn.close.assert_called_once()


def test_info_limited_to_the_dataset_database(cursor):
    cursor.fetchall.side_effect = [[{"version": "8"}], [], []]
    MysqlService().info(_dataset(database="shop"))
    assert cursor.execute.call_args_list[2].args[1] == ["shop"]


def test_list_tables(cursor):
    cursor.fetchall.return_value = [
        {"name": "orders", "type": "BASE TABLE", "engine": "InnoDB", "approxRows": 10,
         "sizeBytes": 16384, "collation": "c", "createdAt": datetime(2026, 1, 2),
         "updatedAt": None, "comment": "", "columns": 4},
        {"name": "v_orders", "type": "VIEW", "engine": None, "approxRows": None,
         "sizeBytes": None, "collation": None, "createdAt": None, "updatedAt": None,
         "comment": "VIEW", "columns": 2},
    ]
    tables = MysqlService().list_tables(_dataset(), "shop")
    assert tables[0]["type"] == "table"
    assert tables[0]["createdAt"] == "2026-01-02T00:00:00"
    assert tables[1]["type"] == "view"
    assert tables[1]["sizeBytes"] is None
    assert cursor.execute.call_args.args[1] == ["shop"]


def test_list_columns_unknown_table(cursor):
    cursor.fetchall.return_value = []
    service, dataset = MysqlService(), _dataset()
    with pytest.raises(MysqlServiceError) as err:
        service.list_columns(dataset, "shop", "missing")
    assert err.value.status_code == 404


def test_list_columns(cursor):
    cursor.fetchall.return_value = [{"name": "id", "type": "int", "nullable": 0, "key": "PRI",
                                     "default": None, "extra": "auto_increment", "comment": ""}]
    columns = MysqlService().list_columns(_dataset(), "shop", "orders")
    assert columns[0]["nullable"] is False
    assert cursor.execute.call_args.args[1] == ("shop", "orders")


def test_bad_credentials_are_a_bad_gateway():
    err = mysql.connector.Error(msg="Access denied", errno=errorcode.ER_ACCESS_DENIED_ERROR)
    service, dataset = MysqlService(), _dataset()
    with patch.object(mysql_service.mysql.connector, "connect", side_effect=err):
        with pytest.raises(MysqlServiceError) as raised:
            service.info(dataset)
    assert raised.value.status_code == 502
    assert "credentials" in str(raised.value)


def test_query_error_closes_the_connection(cursor):
    cursor.execute.side_effect = mysql.connector.Error(msg="boom")
    service, dataset = MysqlService(), _dataset()
    with pytest.raises(MysqlServiceError):
        service.info(dataset)
    cursor.conn.close.assert_called_once()


def test_missing_host():
    service, dataset = MysqlService(), _dataset().model_copy(update={"host": None})
    with pytest.raises(MysqlServiceError) as err:
        service.info(dataset)
    assert err.value.status_code == 400


def test_info_limited_to_the_dataset_table(cursor):
    cursor.fetchall.side_effect = [[{"version": "8"}], [], []]
    MysqlService().info(_dataset(database="shop", table="orders"))
    sql, params = cursor.execute.call_args_list[2].args
    assert "t.TABLE_NAME = %s" in sql
    assert params == ["orders", "shop"]


def test_list_tables_limited_to_the_dataset_table(cursor):
    cursor.fetchall.return_value = []
    MysqlService().list_tables(_dataset(database="shop", table="orders"), "shop")
    assert cursor.execute.call_args.args[1] == ["shop", "orders"]
