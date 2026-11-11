import asyncio
import pyarrow.parquet as pq
from typing import Optional, Any
import pandas as pd
import traceback
from pydantic import ConfigDict
from app.enums.status_node import StatusNode
from app.models.interface.dataset_interface import MysqlDataset, _validate_sql_identifier
from app.models.interface.node_data import NodeDataPandasDf, NodeDataParquet
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
                    if sample:
                        query += " LIMIT 20"
                        result_data_frame = pd.read_sql_query(query, mydb)
                    else:
                        result_data_frame = pd.read_sql_query(query, mydb)
                    schema = generate_pandas_schema(result_data_frame)
                
                else : 
                    print(f"Saving data to {parquet_path}")
                    chunksize = 50
                    parquet_writer = None
                    for chunk in pd.read_sql_query(query, engine, chunksize=chunksize):
                        table = pa.Table.from_pandas(chunk)

                        if parquet_writer is None:
                            parquet_writer = pq.ParquetWriter(parquet_path, table.schema)
                            if sample:
                                parquet_writer.write_table(table)
                                break
                        parquet_writer.write_table(table)

                    if parquet_writer:
                        parquet_writer.close()

                    parquet_file = pq.ParquetFile(parquet_path)
                    schema = parquet_file.schema 
                
                for key, output in self.outputs.items():
                    if output.get_node_data():
                        # Update existing node data
                        # should resolve when output.get_node_data() is not the same type as the new node data
                        if parquet_save:
                            if isinstance(output.get_node_data(), NodeDataParquet):
                                output.get_node_data().parquetPath = parquet_path
                                output.get_node_data().nodeSchema = schema
                            else:
                                raise ValueError("Output node data is not of type NodeDataParquet")

                        else:
                            if isinstance(output.get_node_data(), NodeDataPandasDf):
                                output.get_node_data().nodeSchema = schema
                                if sample:
                                    output.get_node_data().dataExample = result_data_frame
                                else:
                                    output.get_node_data().data = result_data_frame
                            else:
                                raise ValueError("Output node data is not of type NodeDataPandasDf")
                    else:
                        # Create new node data
                        if parquet_save:
                            if isinstance(schema, ParquetSchema):
                                node_data = NodeDataParquet(
                                    data = parquet_path,
                                    nodeSchema=schema,
                                    name=key,
                                )
                            else: 
                                raise ValueError("Schema is not a ParquetSchema")
                        else:
                            node_data = NodeDataPandasDf(
                                nodeSchema=schema,
                                name=key
                            )
                            if sample:
                                node_data.dataExample = result_data_frame
                            else :
                                node_data.data = result_data_frame    
                        output.set_node_data(node_data, self)
                return StatusNode.Valid
            except Exception as e:
                traceback.print_exc()
                self.errorStackTrace = traceback.TracebackException.from_exception(e).format()
                self.statusMessage = e.__str__()
                return StatusNode.Error
            finally:
                if mydb is not None:
                    mydb.close()
                if engine is not None:
                    engine.dispose()
        except ValueError as e:
            traceback.print_exc()
            self.errorStackTrace = traceback.TracebackException.from_exception(e).format()
            self.statusMessage = e.__str__()
            return StatusNode.Error

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


