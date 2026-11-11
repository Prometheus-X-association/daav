"""MySQL-specific routes used by the MySQL dashboard: server information, tables and columns.

The routes are read-only and only query information_schema.
"""
import asyncio
from typing import Annotated, Any, Dict, List

from fastapi import APIRouter, HTTPException, Path, status

from app.middleware.auth import CurrentUser
from app.models.interface.dataset_interface import MysqlDataset
from app.services.dataset_service import DatasetService
from app.services.mysql_service import MysqlService

router = APIRouter(prefix="/datasets", tags=["mysql"],
                   responses={404: {"description": "Not found"}})
dataset_service = DatasetService()
mysql_service = MysqlService()

# Names are passed as query parameters, never in the SQL text: only their length is checked
SqlName = Annotated[str, Path(min_length=1, max_length=64)]


async def _get_mysql_dataset(dataset_id: str, user, database: str = None, table: str = None) -> MysqlDataset:
    dataset = await dataset_service.get_dataset(dataset_id, user)
    if not isinstance(dataset, MysqlDataset):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="The dataset is not a MySQL dataset")
    if database and dataset.database and database != dataset.database:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail=f"The dataset is limited to the database {dataset.database}")
    if table and dataset.database and dataset.table and table != dataset.table:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail=f"The dataset is limited to the table {dataset.database}.{dataset.table}")
    return dataset


@router.get("/{dataset_id}/mysql/info")
async def server_info(dataset_id: str, current_user: CurrentUser) -> Dict[str, Any]:
    """Server version and uptime, connected user and a summary of the visible databases"""
    dataset = await _get_mysql_dataset(dataset_id, current_user)
    return await asyncio.to_thread(mysql_service.info, dataset)


@router.get("/{dataset_id}/mysql/databases/{database}/tables")
async def list_tables(dataset_id: str, database: SqlName, current_user: CurrentUser) -> List[Dict[str, Any]]:
    """Tables and views of a database with engine, approximate row count and size"""
    dataset = await _get_mysql_dataset(dataset_id, current_user, database)
    return await asyncio.to_thread(mysql_service.list_tables, dataset, database)


@router.get("/{dataset_id}/mysql/databases/{database}/tables/{table}/columns")
async def list_columns(dataset_id: str, database: SqlName, table: SqlName,
                       current_user: CurrentUser) -> List[Dict[str, Any]]:
    """Columns of a table"""
    dataset = await _get_mysql_dataset(dataset_id, current_user, database, table)
    return await asyncio.to_thread(mysql_service.list_columns, dataset, database, table)
