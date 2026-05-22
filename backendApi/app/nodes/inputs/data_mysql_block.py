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
            dataset, database, table, parquetSave = await self._retreiveDatabase()
            parquetPath = f"{dataset.id}_{table}.parquet"

            try:
                # Connect to the MySQL database
                engine = create_engine(f"mysql+mysqlconnector://{dataset.user}:{dataset.password}@{dataset.host}/{database}")
                mydb = engine.connect()
                query = f"SELECT * FROM {table}"
                print(f"Connected to MySQL database {database} on {table}")
                if not parquetSave:
                    if sample:
                        query += f" LIMIT 20"
                        result_dataFrame = pd.read_sql_query(query, mydb)
                    else:
                        result_dataFrame = pd.read_sql_query(query, mydb)
                    schema = generate_pandas_schema(result_dataFrame)
                
                else : 
                    print(f"Saving data to {parquetPath}")
                    chunksize = 50
                    parquet_writer = None
                    for chunk in pd.read_sql_query(query, engine, chunksize=chunksize):
                        table = pa.Table.from_pandas(chunk)

                        if parquet_writer is None:
                            parquet_writer = pq.ParquetWriter(parquetPath, table.schema)
                            if sample:
                                parquet_writer.write_table(table)
                                break
                        parquet_writer.write_table(table)

                    if parquet_writer:
                        parquet_writer.close()

                    parquet_file = pq.ParquetFile(parquetPath)
                    schema = parquet_file.schema 
                
                mydb.close()  # Close the connection

                for key, output in self.outputs.items():
                    if output.get_node_data():
                        # Update existing node data
                        # should resolve when output.get_node_data() is not the same type as the new node data
                        if parquetSave:
                            if isinstance(output.get_node_data(), NodeDataParquet):
                                output.get_node_data().parquetPath = parquetPath
                                output.get_node_data().nodeSchema = schema
                            else:
                                raise ValueError("Output node data is not of type NodeDataParquet")

                        else:
                            if isinstance(output.get_node_data(), NodeDataPandasDf):
                                output.get_node_data().nodeSchema = schema
                                if sample:
                                    output.get_node_data().dataExample = result_dataFrame
                                else:
                                    output.get_node_data().data = result_dataFrame
                            else:
                                raise ValueError("Output node data is not of type NodeDataPandasDf")
                    else:
                        # Create new node data
                        if parquetSave:
                            if isinstance(schema, ParquetSchema):
                                node_data = NodeDataParquet(
                                    data = parquetPath,
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
                                node_data.dataExample = result_dataFrame
                            else :
                                node_data.data = result_dataFrame    
                        output.set_node_data(node_data, self)
                return StatusNode.Valid
            except Exception as e:
                mydb.close()  # Ensure the connection is closed in case of an error
                traceback.print_exc()
                self.errorStackTrace = traceback.TracebackException.from_exception(e).format()
                self.statusMessage = e.__str__()
                return StatusNode.Error
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
        datasetId : str 
        if self.data.get('selectDataSource') and self.data['selectDataSource']['value']:
            datasetId = self.data['selectDataSource']['value']
        else:
            raise ValueError("No data source selected")
        dataset : MysqlDataset  = await self.datasetService.get_dataset(datasetId)
        database = self.data['selectDatabaseDataSource']['value'] if self.data.get('selectDatabaseDataSource') and self.data['selectDatabaseDataSource'].get('value') else dataset.database
        table = self.data['selectTableDataSource']['value'] if self.data.get('selectTableDataSource') and self.data['selectTableDataSource'].get('value') else dataset.table
        parquetSave = self.data['parquetSave']['value'] if self.data.get('parquetSave') else False
        if (table is None or table == ""):
            raise ValueError("No table selected")
        if (database is None or database == ""):
            raise ValueError("No database selected")
        # Validate identifiers regardless of source (Pydantic model or workflow JSON)
        _validate_sql_identifier(database, 'database')
        _validate_sql_identifier(table, 'table')
        return dataset, database, table, parquetSave


    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )


