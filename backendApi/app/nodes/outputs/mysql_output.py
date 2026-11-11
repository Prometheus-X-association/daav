from typing import Literal, Optional, Any

from pydantic import ConfigDict
from sqlalchemy import create_engine
from app.enums.status_node import StatusNode
from app.models.interface.dataset_interface import MysqlDataset, _validate_sql_identifier
from app.models.interface.node_data import NodeDataPandasDf, NodeDataParquet
from app.nodes.outputs.output_node import OutputNode
import pyarrow.parquet as pq

from app.services.dataset_service import DatasetService


class MysqlOutput(OutputNode):
    
    datasetService: Optional[DatasetService] = None

    def __init__(self, id: str, data: Any, revision: Optional[str] = None, status: Optional[StatusNode] = None):
        """Initialize a new MysqlOutput instance.

        Args:
            id (str): Unique identifier for the node
            data (Any): Data associated with the node
            revision (Optional[str]): Revision identifier for the node
            status (Optional[StatusNode]): Current status of the node
        """
        super().__init__(id=id, data=data, revision=revision, status=status)
        self.datasetService = DatasetService()    

    async def process(self, sample=False) -> StatusNode:
        """Process the data and export it to a SQL file.

        Args:
            sample (bool): Flag to indicate if process on sample should be done. Defaults to False.

        Returns:
            StatusNode: The status of the node after processing.
        """
        try:
            dataset, database, table, if_exist ,create_index,index_table = await self._retreiveDatabase()
            index_options = {'index': create_index, 'index_label': index_table}
            return self._write(dataset, database, table, if_exist, index_options, sample)
        except ValueError as e:
            return self._fail(e)

    def _write(self, dataset: MysqlDataset, database: str, table: str, if_exist: str, index_options: dict,
               sample: bool) -> StatusNode:
        """Write the connected input data into the table; the engine is always disposed of."""
        engine = None
        try:
            # pandas only writes through SQLAlchemy: a raw mysql.connector connection is handled as SQLite
            engine = create_engine(f"mysql+mysqlconnector://{dataset.user}:{dataset.password}@{dataset.host}/{database}")
            for data in self._connected_data():
                if isinstance(data, NodeDataPandasDf):
                    df = self._input_dataframe(data, sample)
                    # Write the DataFrame to the SQL database
                    df.to_sql(table, con=engine, if_exists=if_exist, **index_options)
                elif isinstance(data, NodeDataParquet):
                    self._write_parquet(data.data, engine, table, if_exist, index_options, sample)
                else:
                    raise TypeError("Unsupported data type: {}".format(type(data)))
        except Exception as e:
            return self._fail(e)
        finally:
            if engine is not None:
                engine.dispose()
        return StatusNode.Valid

    @staticmethod
    def _write_parquet(path: str, engine, table: str, if_exist: str, index_options: dict, sample: bool) -> None:
        """Write a parquet file by batches: ifExist applies to the first batch, the next ones are appended.

        A sample only writes the first 20 rows.
        """
        chunk_size = 1000
        parquet_file = pq.ParquetFile(path)
        if_exists = if_exist
        for batch in parquet_file.iter_batches(batch_size=chunk_size):
            chunk_df = batch.to_pandas()
            if sample:
                chunk_df.head(20).to_sql(table, con=engine, if_exists=if_exists, **index_options)
                break
            chunk_df.to_sql(table, con=engine, if_exists=if_exists, **index_options)
            if_exists = 'append'

    async def _retreiveDatabase(self) -> tuple[MysqlDataset, str, str, Literal['fail', 'replace', 'append']]:
        """Retrieve the database configuration.

        Returns:
            tuple[MysqlDataset, str, str, Literal['fail', 'replace', 'append']]: A tuple containing the dataset, database name, table name, and ifExist option.

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
        table = self._param('tableAutoComplete') or dataset.table
        if_exist = self._param('selectExist', "fail")
        create_index = self._param('createIndex', False)
        index_table = self._param('indexTable', 'id')
        #print("table",indexTable)
        if (table is None or table == ""):
            raise ValueError("No table selected")
        if (database is None or database == ""):
            raise ValueError("No database selected")
        # Validate identifiers regardless of source (Pydantic model or workflow JSON)
        _validate_sql_identifier(database, 'database')
        _validate_sql_identifier(table, 'table')
        return dataset, database, table, if_exist,create_index,index_table

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )