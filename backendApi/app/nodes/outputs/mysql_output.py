import traceback
from typing import Literal, Optional, Any

import pandas as pd
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

            engine = None
            try:
                # pandas only writes through SQLAlchemy: a raw mysql.connector connection is handled as SQLite
                engine = create_engine(f"mysql+mysqlconnector://{dataset.user}:{dataset.password}@{dataset.host}/{database}")
                for input in self.inputs.values():
                    if (input.get_connected_node()):
                        data = input.get_node_data()
                        if isinstance(data, NodeDataPandasDf):
                            if (sample) :
                                df = data.dataExample
                            else:
                                df = data.data
                            if not isinstance(df, pd.DataFrame):
                                raise ValueError("Input data is not a pandas DataFrame")

                            # Write the DataFrame to the SQL database
                            df.to_sql(table, con=engine, if_exists=if_exist, index=create_index, index_label=index_table)
                        elif isinstance(data, NodeDataParquet):
                            chunk_size = 1000 
                            is_first_chunk = True
                            parquet_file = pq.ParquetFile(data.data)

                            for batch in parquet_file.iter_batches(batch_size=chunk_size):
                                chunk_df = batch.to_pandas()
                                if sample and is_first_chunk:
                                    chunk_df = chunk_df.head(20)
                                    chunk_df.to_sql(table, con=engine, if_exists=if_exist, index=create_index, index_label=index_table)
                                    break
                                if_exists = if_exist if is_first_chunk else 'append'
                                chunk_df.to_sql(table, con=engine, if_exists=if_exists, index=create_index, index_label=index_table)
                                is_first_chunk = False
                        else:
                            raise TypeError("Unsupported data type: {}".format(type(data)))
            except Exception as e:
                traceback.print_exc()
                self.errorStackTrace = traceback.TracebackException.from_exception(e).format()
                self.statusMessage = e.__str__()
                return StatusNode.Error
            finally:
                if engine is not None:
                    engine.dispose()
        except ValueError as e:
            traceback.print_exc()
            self.errorStackTrace = traceback.TracebackException.from_exception(e).format()
            self.statusMessage = e.__str__()
            return StatusNode.Error
        return StatusNode.Valid
    
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
        database = self.data['selectDatabaseDataSource']['value'] if self.data.get('selectDatabaseDataSource') and self.data['selectDatabaseDataSource'].get('value') else dataset.database
        table = self.data.get('tableAutoComplete').get('value') if self.data.get('tableAutoComplete') and self.data.get('tableAutoComplete').get('value')   else dataset.table
        if_exist = self.data.get('selectExist')['value'] if self.data.get('selectExist') and self.data.get('selectExist').get('value') else "fail"
        create_index = self.data.get('createIndex')['value'] if self.data.get('createIndex') and self.data.get('createIndex').get('value') else False
        index_table = self.data.get('indexTable')['value'] if self.data.get('indexTable') and self.data.get('indexTable').get('value') else 'id'
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