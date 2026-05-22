import traceback
from typing import Literal, Optional, Any

import pandas as pd
from pydantic import ConfigDict
from sqlalchemy import create_engine
from app.enums.status_node import StatusNode
from app.models.interface.dataset_interface import MysqlDataset, _validate_sql_identifier
from app.models.interface.node_data import NodeDataPandasDf, NodeDataParquet
from app.nodes.outputs.output_node import OutputNode
from mysql import connector
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
            dataset, database, table, ifExist ,createIndex,indexTable = await self._retreiveDatabase()

            try:
                # Connect to the MySQL database
                mydb = connector.connect(host=dataset.host, database=database, user=dataset.user, password=dataset.password, use_pure=True)
                engine = create_engine('sqlite://', echo=False)
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
                            df.to_sql(table, con=mydb, if_exists=ifExist, index=createIndex, index_label=indexTable)

                            '''# Export the SQL database to a file
                            # Create an in-memory SQLite database
                            df.to_sql(table, con=engine, if_exists=ifExist , index=createIndex, index_label=indexTable)
                            with open('output.sql', 'w') as f:
                                print('Exporting SQL database to output.sql')
                                for line in engine.raw_connection().driver_connection.iterdump():
                                    print('%s\n' % line)
                                    f.write('%s\n' % line)
                            break'''
                        elif isinstance(data, NodeDataParquet):
                            chunkSize = 1000 
                            isFistChunk = True
                            parquetFile = pq.ParquetFile(data.data)

                            for batch in parquetFile.iter_batches(batch_size=chunkSize):
                                chunkDf = batch.to_pandas()
                                if sample and isFistChunk:
                                    chunkDf = chunkDf.head(20)
                                    chunkDf.to_sql(table, con=engine, if_exists=ifExist, index=createIndex, index_label=indexTable)
                                    break
                                if_exists = ifExist if isFistChunk else 'append'
                                chunkDf.to_sql(table, con=engine, if_exists=if_exists, index=createIndex, index_label=indexTable)
                                isFistChunk = False
                            '''with open('output.sql', 'w') as f:
                                print('Exporting SQL database to output.sql')
                                for line in engine.raw_connection().driver_connection.iterdump():
                                    print('%s\n' % line)
                                    f.write('%s\n' % line)
                            break'''
                        else:
                            raise TypeError("Unsupported data type: {}".format(type(data)))
                mydb.close()
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
        return StatusNode.Valid
    
    async def _retreiveDatabase(self) -> tuple[MysqlDataset, str, str, Literal['fail', 'replace', 'append']]:
        """Retrieve the database configuration.

        Returns:
            tuple[MysqlDataset, str, str, Literal['fail', 'replace', 'append']]: A tuple containing the dataset, database name, table name, and ifExist option.

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
        table = self.data.get('tableAutoComplete').get('value') if self.data.get('tableAutoComplete') and self.data.get('tableAutoComplete').get('value')   else dataset.table
        ifExist = self.data.get('selectExist')['value'] if self.data.get('selectExist') and self.data.get('selectExist').get('value') else "fail"
        createIndex = self.data.get('createIndex')['value'] if self.data.get('createIndex') and self.data.get('createIndex').get('value') else False
        indexTable = self.data.get('indexTable')['value'] if self.data.get('indexTable') and self.data.get('indexTable').get('value') else 'id'
        #print("table",indexTable)
        if (table is None or table == ""):
            raise ValueError("No table selected")
        if (database is None or database == ""):
            raise ValueError("No database selected")
        # Validate identifiers regardless of source (Pydantic model or workflow JSON)
        _validate_sql_identifier(database, 'database')
        _validate_sql_identifier(table, 'table')
        return dataset, database, table, ifExist,createIndex,indexTable

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )