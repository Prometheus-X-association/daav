"""
Reading of the node parameters: MongoOutput and MysqlOutput._retreiveDatabase,
FileOutput._retrieveFileConfig, DataMysqlBlock and DataMongoBlock._retreiveDatabase.
"""
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import HTTPException

from app.nodes.inputs.data_mongo_block import DataMongoBlock
from app.nodes.inputs.data_mysql_block import DataMysqlBlock
from app.nodes.outputs.file_output import FileOutput
from app.nodes.outputs.mongo_output import MongoOutput
from app.nodes.outputs.mysql_output import MysqlOutput
from app.utils.security import PathSecurityValidator


def _node(cls, data, dataset=None, get_dataset=None):
    node = cls(id="n1", data=data)
    service = Mock()
    service.get_dataset = get_dataset or AsyncMock(return_value=dataset)
    object.__setattr__(node, "datasetService", service)
    return node


def _dataset(**kwargs):
    values = dict(database=None, table=None, collection=None)
    values.update(kwargs)
    return Mock(**values)


SOURCE = {"selectDataSource": {"value": "ds1"}}


# ===========================
# MongoOutput and MysqlOutput
# ===========================

DATABASE_OUTPUTS = [
    (MongoOutput, "collectionAutoComplete", "No collection selected"),
    (MysqlOutput, "tableAutoComplete", "No table selected"),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("cls, table_key, missing_table", DATABASE_OUTPUTS)
async def test_output_defaults_come_from_the_dataset(cls, table_key, missing_table):
    dataset = _dataset(database="shop", table="orders")
    node = _node(cls, dict(SOURCE), dataset)

    assert await node._retreiveDatabase() == (dataset, "shop", "orders", "fail", False, "id")
    node.datasetService.get_dataset.assert_awaited_once_with("ds1")


@pytest.mark.asyncio
@pytest.mark.parametrize("cls, table_key, missing_table", DATABASE_OUTPUTS)
async def test_output_parameters(cls, table_key, missing_table):
    dataset = _dataset(database="shop", table="orders")
    data = dict(SOURCE, selectDatabaseDataSource={"value": "crm"}, selectExist={"value": "append"},
                createIndex={"value": True}, indexTable={"value": "code"})
    data[table_key] = {"value": "contacts"}
    node = _node(cls, data, dataset)

    assert await node._retreiveDatabase() == (dataset, "crm", "contacts", "append", True, "code")


@pytest.mark.asyncio
@pytest.mark.parametrize("cls, table_key, missing_table", DATABASE_OUTPUTS)
async def test_output_empty_parameters_fall_back(cls, table_key, missing_table):
    dataset = _dataset(database="shop", table="orders")
    data = dict(SOURCE, selectDatabaseDataSource={"value": ""}, selectExist={}, createIndex={"value": False},
                indexTable={"value": None})
    data[table_key] = {"value": ""}
    node = _node(cls, data, dataset)

    assert await node._retreiveDatabase() == (dataset, "shop", "orders", "fail", False, "id")


@pytest.mark.asyncio
@pytest.mark.parametrize("cls, table_key, missing_table", DATABASE_OUTPUTS)
@pytest.mark.parametrize("data", [{}, {"selectDataSource": None}, {"selectDataSource": {"value": ""}}])
async def test_output_without_source(cls, table_key, missing_table, data):
    node = _node(cls, data, _dataset())

    with pytest.raises(ValueError, match="No data source selected"):
        await node._retreiveDatabase()
    node.datasetService.get_dataset.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize("cls, table_key, missing_table", DATABASE_OUTPUTS)
async def test_output_without_value_key(cls, table_key, missing_table):
    node = _node(cls, {"selectDataSource": {"label": "x"}}, _dataset())

    with pytest.raises(KeyError):
        await node._retreiveDatabase()


@pytest.mark.asyncio
@pytest.mark.parametrize("cls, table_key, missing_table", DATABASE_OUTPUTS)
@pytest.mark.parametrize("table", [None, ""])
async def test_output_without_table(cls, table_key, missing_table, table):
    node = _node(cls, dict(SOURCE), _dataset(database=None, table=table))

    # The table is checked before the database
    with pytest.raises(ValueError, match=missing_table):
        await node._retreiveDatabase()


@pytest.mark.asyncio
@pytest.mark.parametrize("cls, table_key, missing_table", DATABASE_OUTPUTS)
@pytest.mark.parametrize("database", [None, ""])
async def test_output_without_database(cls, table_key, missing_table, database):
    node = _node(cls, dict(SOURCE), _dataset(database=database, table="orders"))

    with pytest.raises(ValueError, match="No database selected"):
        await node._retreiveDatabase()


@pytest.mark.asyncio
@pytest.mark.parametrize("database, table", [("bad-name", "orders"), ("shop", "orders; DROP")])
async def test_mysql_output_identifiers_are_validated(database, table):
    node = _node(MysqlOutput, dict(SOURCE), _dataset(database=database, table=table))

    with pytest.raises(ValueError, match="invalid characters"):
        await node._retreiveDatabase()


@pytest.mark.asyncio
async def test_mongo_output_does_not_validate_identifiers():
    dataset = _dataset(database="shop-2", table="orders.archive")
    node = _node(MongoOutput, dict(SOURCE), dataset)

    assert (await node._retreiveDatabase())[1:3] == ("shop-2", "orders.archive")


@pytest.mark.asyncio
@pytest.mark.parametrize("cls", [MongoOutput, MysqlOutput])
async def test_output_dataset_error_propagates(cls):
    node = _node(cls, dict(SOURCE), get_dataset=AsyncMock(side_effect=HTTPException(status_code=404)))

    with pytest.raises(HTTPException):
        await node._retreiveDatabase()


# ===========================
# FileOutput
# ===========================

@pytest.mark.asyncio
async def test_file_output_defaults():
    dataset = _dataset()
    node = _node(FileOutput, dict(SOURCE), dataset)

    assert await node._retrieveFileConfig() == (dataset, ",", "utf-8", None, None, None)


@pytest.mark.asyncio
async def test_file_output_parameters():
    dataset = _dataset()
    data = dict(SOURCE, delimiter={"value": ";"}, encoding={"value": "latin-1"}, fileType={"value": "csv"},
                fileName={"value": "out.csv"}, fileExist={"value": "append"})
    node = _node(FileOutput, data, dataset)

    assert await node._retrieveFileConfig() == (dataset, ";", "latin-1", "csv", "out.csv", "append")


@pytest.mark.asyncio
async def test_file_output_file_name_without_source():
    node = _node(FileOutput, {"fileName": {"value": "out.json"}, "delimiter": {"value": ""}})

    assert await node._retrieveFileConfig() == (None, ",", "utf-8", None, "out.json", None)
    node.datasetService.get_dataset.assert_not_called()


@pytest.mark.asyncio
async def test_file_output_unknown_dataset_with_file_name():
    node = _node(FileOutput, dict(SOURCE, fileName={"value": "out.json"}),
                 get_dataset=AsyncMock(side_effect=HTTPException(status_code=404)))

    assert (await node._retrieveFileConfig())[0] is None


@pytest.mark.asyncio
@pytest.mark.parametrize("data", [{}, {"selectDataSource": {"value": ""}, "fileName": {"value": ""}}])
async def test_file_output_without_source_nor_file_name(data):
    node = _node(FileOutput, data)

    with pytest.raises(ValueError, match="Either a data source must be selected or a filename must be provided"):
        await node._retrieveFileConfig()


@pytest.mark.asyncio
async def test_file_output_unknown_dataset_without_file_name():
    node = _node(FileOutput, dict(SOURCE), get_dataset=AsyncMock(side_effect=RuntimeError("down")))

    with pytest.raises(ValueError, match="Either a data source"):
        await node._retrieveFileConfig()


@pytest.mark.asyncio
async def test_file_output_file_name_refused():
    PathSecurityValidator.set_security_enabled(True)
    try:
        node = _node(FileOutput, {"fileName": {"value": "../evil.csv"}})
        with pytest.raises(HTTPException):
            await node._retrieveFileConfig()
    finally:
        PathSecurityValidator.reset_security_state()


# ===========================
# DataMysqlBlock and DataMongoBlock
# ===========================

@pytest.mark.asyncio
async def test_mysql_input_parameters():
    dataset = _dataset(database="shop", table="orders")
    node = _node(DataMysqlBlock, dict(SOURCE), dataset)
    assert await node._retreiveDatabase() == (dataset, "shop", "orders", False)

    data = dict(SOURCE, selectDatabaseDataSource={"value": "crm"}, selectTableDataSource={"value": "contacts"},
                parquetSave={"value": True})
    node = _node(DataMysqlBlock, data, dataset)
    assert await node._retreiveDatabase() == (dataset, "crm", "contacts", True)

    node = _node(DataMysqlBlock, dict(SOURCE, parquetSave={"value": False}), dataset)
    assert (await node._retreiveDatabase())[3] is False


@pytest.mark.asyncio
async def test_mysql_input_errors():
    node = _node(DataMysqlBlock, {}, _dataset())
    with pytest.raises(ValueError, match="No data source selected"):
        await node._retreiveDatabase()
    node = _node(DataMysqlBlock, dict(SOURCE), _dataset(database="shop"))
    with pytest.raises(ValueError, match="No table selected"):
        await node._retreiveDatabase()
    node = _node(DataMysqlBlock, dict(SOURCE), _dataset(table="orders"))
    with pytest.raises(ValueError, match="No database selected"):
        await node._retreiveDatabase()
    node = _node(DataMysqlBlock, dict(SOURCE), _dataset(database="shop", table="a b"))
    with pytest.raises(ValueError, match="invalid characters"):
        await node._retreiveDatabase()


@pytest.mark.asyncio
async def test_mongo_input_parameters():
    dataset = _dataset(database="shop", collection="orders")
    node = _node(DataMongoBlock, dict(SOURCE), dataset)
    assert await node._retreiveDatabase() == (dataset, "shop", "orders")

    data = dict(SOURCE, selectDatabaseDataSource={"value": "crm"}, selectCollectionDataSource={"value": "contacts"})
    assert await _node(DataMongoBlock, data, dataset)._retreiveDatabase() == (dataset, "crm", "contacts")


@pytest.mark.asyncio
async def test_mongo_input_errors():
    node = _node(DataMongoBlock, {"selectDataSource": {"value": None}}, _dataset())
    with pytest.raises(ValueError, match="No data source selected"):
        await node._retreiveDatabase()
    node = _node(DataMongoBlock, dict(SOURCE), _dataset(database="shop"))
    with pytest.raises(ValueError, match="No Collection selected"):
        await node._retreiveDatabase()
    node = _node(DataMongoBlock, dict(SOURCE), _dataset(collection="orders"))
    with pytest.raises(ValueError, match="No database selected"):
        await node._retreiveDatabase()
