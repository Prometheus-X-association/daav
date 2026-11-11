"""MySQL access for the MySQL dashboard: server information, databases, tables and columns.

Everything is read from information_schema with parameterized queries, so database and
table names never end up in the SQL text.
"""
import logging
from contextlib import contextmanager
from datetime import date, datetime
from typing import Any, Dict, Iterator, List, Optional, Tuple

import mysql.connector
from mysql.connector import errorcode

from app.models.interface.dataset_interface import MysqlDataset

logger = logging.getLogger(__name__)

CONNECT_TIMEOUT = 10
SYSTEM_DATABASES = ('information_schema', 'mysql', 'performance_schema', 'sys')


class MysqlServiceError(Exception):
    """Error raised by MysqlService, carrying the HTTP status to return to the client.

    MySQL authentication failures are reported as 502 (bad gateway): a 401/403 would be
    mistaken by the frontend for a DAAV session problem.
    """

    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.status_code = status_code


def _split_host(host: str) -> Tuple[str, int]:
    """Accept 'host' or 'host:port' (IPv6 addresses in brackets: '[::1]:3307')"""
    host = (host or '').strip()
    if host.startswith('['):
        address, _, rest = host[1:].partition(']')
        port = rest[1:] if rest.startswith(':') else ''
    elif host.count(':') == 1:
        address, port = host.split(':')
    else:
        address, port = host, ''
    return address, int(port) if port.isdigit() else 3306


def _single_table(dataset: MysqlDataset) -> bool:
    """The dataset points to one table, not to a whole database or server"""
    return bool(dataset.database and dataset.table)


def _to_json(value: Any) -> Any:
    if isinstance(value, (bytes, bytearray)):
        return value.decode(errors='replace')
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


class MysqlService:

    @contextmanager
    def _cursor(self, dataset: MysqlDataset) -> Iterator[Any]:
        if not dataset.host:
            raise MysqlServiceError("The dataset has no host", 400)
        host, port = _split_host(dataset.host)
        try:
            conn = mysql.connector.connect(
                host=host,
                port=port,
                user=dataset.user,
                password=dataset.password,
                connection_timeout=CONNECT_TIMEOUT,
            )
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                raise MysqlServiceError(f"MySQL refused the credentials: {err.msg}")
            raise MysqlServiceError(f"Cannot connect to MySQL: {err.msg or err}")
        try:
            cursor = conn.cursor(dictionary=True)
            try:
                yield cursor
            finally:
                cursor.close()
        except mysql.connector.Error as err:
            logger.warning(f"MySQL error on dataset {dataset.id}: {err}")
            raise MysqlServiceError(f"MySQL error: {err.msg or err}")
        finally:
            conn.close()

    @staticmethod
    def _rows(cursor) -> List[Dict[str, Any]]:
        return [{k: _to_json(v) for k, v in row.items()} for row in cursor.fetchall()]

    def info(self, dataset: MysqlDataset) -> Dict[str, Any]:
        """Server version and uptime, connected user, and a summary of each visible database"""
        with self._cursor(dataset) as cursor:
            cursor.execute(
                "SELECT VERSION() AS version, @@version_comment AS versionComment, "
                "CURRENT_USER() AS currentUser, @@character_set_server AS charset, "
                "@@collation_server AS collation, @@time_zone AS timeZone"
            )
            server = self._rows(cursor)[0]
            cursor.execute("SHOW GLOBAL STATUS WHERE Variable_name IN ('Uptime', 'Threads_connected')")
            status = {row['Variable_name']: row['Value'] for row in self._rows(cursor)}

            # A dataset limited to one table only reports that table in its database summary
            join = "t.TABLE_SCHEMA = s.SCHEMA_NAME"
            params: List[Any] = []
            if _single_table(dataset):
                join += " AND t.TABLE_NAME = %s"
                params.append(dataset.table)
            if dataset.database:
                where = "s.SCHEMA_NAME = %s"
                params.append(dataset.database)
            else:
                where = "s.SCHEMA_NAME NOT IN (%s, %s, %s, %s)"
                params.extend(SYSTEM_DATABASES)
            cursor.execute(
                "SELECT s.SCHEMA_NAME AS name, s.DEFAULT_CHARACTER_SET_NAME AS charset, "
                "s.DEFAULT_COLLATION_NAME AS collation, COUNT(t.TABLE_NAME) AS tables, "
                "COALESCE(SUM(t.TABLE_ROWS), 0) AS approxRows, "
                "COALESCE(SUM(t.DATA_LENGTH + t.INDEX_LENGTH), 0) AS sizeBytes "
                "FROM information_schema.SCHEMATA s "
                f"LEFT JOIN information_schema.TABLES t ON {join} "
                f"WHERE {where} GROUP BY s.SCHEMA_NAME, s.DEFAULT_CHARACTER_SET_NAME, "
                "s.DEFAULT_COLLATION_NAME ORDER BY s.SCHEMA_NAME",
                params,
            )
            databases = [
                {**db, 'tables': int(db['tables']), 'approxRows': int(db['approxRows']),
                 'sizeBytes': int(db['sizeBytes'])}
                for db in self._rows(cursor)
            ]

        def as_int(value: Optional[str]) -> Optional[int]:
            return int(value) if value is not None and str(value).isdigit() else None

        return {
            **server,
            'host': dataset.host,
            'uptimeSeconds': as_int(status.get('Uptime')),
            'threadsConnected': as_int(status.get('Threads_connected')),
            'databases': databases,
        }

    def list_tables(self, dataset: MysqlDataset, database: str) -> List[Dict[str, Any]]:
        """Tables and views of a database, with engine, approximate row count and size.

        A dataset limited to one table only lists that table.
        """
        where = "t.TABLE_SCHEMA = %s"
        params: List[Any] = [database]
        if _single_table(dataset):
            where += " AND t.TABLE_NAME = %s"
            params.append(dataset.table)
        with self._cursor(dataset) as cursor:
            cursor.execute(
                "SELECT t.TABLE_NAME AS name, t.TABLE_TYPE AS type, t.ENGINE AS engine, "
                "t.TABLE_ROWS AS approxRows, t.DATA_LENGTH + t.INDEX_LENGTH AS sizeBytes, "
                "t.TABLE_COLLATION AS collation, t.CREATE_TIME AS createdAt, "
                "t.UPDATE_TIME AS updatedAt, t.TABLE_COMMENT AS comment, "
                "(SELECT COUNT(*) FROM information_schema.COLUMNS c "
                " WHERE c.TABLE_SCHEMA = t.TABLE_SCHEMA AND c.TABLE_NAME = t.TABLE_NAME) AS columns "
                f"FROM information_schema.TABLES t WHERE {where} ORDER BY t.TABLE_NAME",
                params,
            )
            tables = self._rows(cursor)
        for table in tables:
            table['type'] = 'view' if table['type'] == 'VIEW' else 'table'
            for key in ('approxRows', 'sizeBytes', 'columns'):
                table[key] = int(table[key]) if table[key] is not None else None
        return tables

    def list_columns(self, dataset: MysqlDataset, database: str, table: str) -> List[Dict[str, Any]]:
        """Columns of a table, in their definition order"""
        with self._cursor(dataset) as cursor:
            cursor.execute(
                "SELECT COLUMN_NAME AS name, COLUMN_TYPE AS type, IS_NULLABLE = 'YES' AS nullable, "
                "COLUMN_KEY AS `key`, COLUMN_DEFAULT AS `default`, EXTRA AS extra, "
                "COLUMN_COMMENT AS comment FROM information_schema.COLUMNS "
                "WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s ORDER BY ORDINAL_POSITION",
                (database, table),
            )
            columns = self._rows(cursor)
        if not columns:
            raise MysqlServiceError(f"Table {database}.{table} not found", 404)
        for column in columns:
            column['nullable'] = bool(column['nullable'])
        return columns
