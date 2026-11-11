import asyncio
import pyarrow.parquet as pq
from typing import Optional, Any
import pandas as pd
from pydantic import ConfigDict
from app.enums.status_node import StatusNode
from app.models.interface.dataset_interface import MysqlDataset, _validate_sql_identifier
from app.nodes.inputs.input_node import InputNode
from app.services.dataset_service import DatasetService
from app.utils.utils import generate_pandas_schema
from sqlalchemy import create_engine
import pyarrow as pa
from pyarrow.parquet import ParquetSchema


class DataMysqlBlock(InputNode):
    """
    DataMysqlBlock is responsible for retrieving data from a MySQL database and processing it into a pandas DataFrame.
    """
    datasetService: Optional[DatasetService] = None

    def __init__(self, id: str, data: Any, revision: Optional[str] = None, status: Optional[StatusNode] = None):
        """Initialize a new DataMysqlBlock instance.

        Args:
            id (str): Unique identifier for the node
            data (Any): Data associated with the node
            revision (Optional[str]): Revision identifier for the node
            status (Optional[StatusNode]): Current status of the node
        """
        super().__init__(id=id, data=data, revision=revision, status=status)    
        self.datasetService = DatasetService()

    async def process(self, sample: bool = False) -> StatusNode:
        """Process the data from the MySQL database.

        Args:
            sample (bool): If True, retrieve a sample of the data (default is False).

        Returns:
            StatusNode: The status of the node after processing.
        """
        try:
            dataset, database, table, parquet_save = await self._retreiveDatabase()
            return self._read(dataset, database, table, parquet_save, sample)
        except ValueError as e:
            return self._fail(e)

    def _read(self, dataset: MysqlDataset, database: str, table: str, parquet_save: bool, sample: bool) -> StatusNode:
        """Read the table and publish it on the outputs; the connection is always closed."""
        parquet_path = f"{dataset.id}_{table}.parquet"

        engine = None
        mydb = None
        try:
            # Connect to the MySQL database
            engine = create_engine(f"mysql+mysqlconnector://{dataset.user}:{dataset.password}@{dataset.host}/{database}")
            mydb = engine.connect()
            query = f"SELECT * FROM {table}"
            print(f"Connected to MySQL database {database} on {table}")
            if not parquet_save:
                result_data_frame = self._read_dataframe(mydb, query, sample)
                schema = generate_pandas_schema(result_data_frame)
                parquet_path = None
            else:
                result_data_frame = None
                schema = self._dump_to_parquet(engine, query, parquet_path, sample)

            for key, output in self.outputs.items():
                self._publish(output, key, schema, result_data_frame, parquet_path, sample)
            return StatusNode.Valid
        except Exception as e:
            return self._fail(e)
        finally:
            if mydb is not None:
                mydb.close()
            if engine is not None:
                engine.dispose()

    @staticmethod
    def _read_dataframe(connection, query: str, sample: bool) -> pd.DataFrame:
        """Read the result of the query in memory; a sample is its first 20 rows."""
        if sample:
            query += " LIMIT 20"
        return pd.read_sql_query(query, connection)

    @staticmethod
    def _dump_to_parquet(engine, query: str, parquet_path: str, sample: bool) -> ParquetSchema:
        """Write the result of the query to a parquet file by chunks, and return the schema of the file.

        A sample only writes the first chunk.
        """
        print(f"Saving data to {parquet_path}")
        chunksize = 50
        parquet_writer = None
        try:
            # Nullable dtypes: an integer column keeps its type in a chunk that holds a NULL
            # (it would become a float there, and no longer match the schema of the file)
            for chunk in pd.read_sql_query(query, engine, chunksize=chunksize, dtype_backend="numpy_nullable"):
                table = pa.Table.from_pandas(chunk)

                if parquet_writer is None:
                    parquet_writer = pq.ParquetWriter(parquet_path, table.schema)
                elif not table.schema.equals(parquet_writer.schema):
                    table = table.cast(parquet_writer.schema)
                parquet_writer.write_table(table)
                if sample:
                    break
        finally:
            if parquet_writer:
                parquet_writer.close()

        parquet_file = pq.ParquetFile(parquet_path)
        return parquet_file.schema

    async def _retreiveDatabase(self) -> tuple[MysqlDataset, str, str]:
        """Retrieve the database configuration.

        Returns:
            tuple[MysqlDataset, str, str]: A tuple containing the dataset, database name, and table name.

        Raises:
            ValueError: If no data source, database, or table is selected.
        """
        dataset_id : str 
        if self.data.get('selectDataSource') and self.data['selectDataSource']['value']:
            dataset_id = self.data['selectDataSource']['value']
        else:
            raise ValueError("No data source selected")
        dataset : MysqlDataset  = await self.datasetService.get_dataset(dataset_id)
        database = self._param('selectDatabaseDataSource') or dataset.database
        table = self._param('selectTableDataSource') or dataset.table
        parquet_save = self.data['parquetSave']['value'] if self.data.get('parquetSave') else False
        if (table is None or table == ""):
            raise ValueError("No table selected")
        if (database is None or database == ""):
            raise ValueError("No database selected")
        # Validate identifiers regardless of source (Pydantic model or workflow JSON)
        _validate_sql_identifier(database, 'database')
        _validate_sql_identifier(table, 'table')
        return dataset, database, table, parquet_save


    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )


