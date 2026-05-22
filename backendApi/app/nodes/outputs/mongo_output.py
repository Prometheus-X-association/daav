import asyncio
import traceback
from typing import Literal, Optional, Any

import pandas as pd
from pydantic import ConfigDict
from pymongo import MongoClient
from sqlalchemy import create_engine
from app.enums.status_node import StatusNode
from app.models.interface.dataset_interface import MongoDataset
from app.models.interface.node_data import NodeDataPandasDf, NodeDataParquet
from app.nodes.outputs.output_node import OutputNode
from mysql import connector
import pyarrow.parquet as pq

from app.services.dataset_service import DatasetService
from app.utils import utils


class MongoOutput(OutputNode):
    
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
            dataset, database, collection, ifExist ,createIndex,indexTable = await self._retreiveDatabase()

            try:
                # Connect to the MongoDB database
                client = MongoClient(dataset.uri)
                db = client[database]

                # Handle collection existence based on ifExist parameter
                collection_exists = collection in db.list_collection_names()
                if collection_exists:
                    if ifExist == 'fail':
                        raise ValueError(f"Collection '{collection}' already exists and ifExist is set to 'fail'")
                    elif ifExist == 'replace':
                        print(f"Dropping existing collection '{collection}' because ifExist is set to 'replace'")
                        db.drop_collection(collection)
                        print(f"Creating new collection '{collection}'")
                        db.create_collection(collection)
                    # For 'append', we don't need to do anything special
                else:
                    # Collection doesn't exist, create it
                    print(f"Collection '{collection}' does not exist. Creating it now.")
                    db.create_collection(collection)
                    print(f"Collection '{collection}' created successfully.")
                
                col = db[collection]
                
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
                            for df_chunk in utils.slice_generator(df):
                                records = df_chunk.to_dict(orient='records')
                                col.insert_many(records)
                        elif isinstance(data, NodeDataParquet):
                            chunkSize = 1000 
                            isFistChunk = True
                            parquetFile = pq.ParquetFile(data.data)

                            for batch in parquetFile.iter_batches(batch_size=chunkSize):
                                df_chunk = batch.to_pandas()
                                if sample and isFistChunk:
                                    records = df_chunk.to_dict(orient='records')
                                    col.insert_many(records)
                                    break
                                if_exists = ifExist if isFistChunk else 'append'
                                records = df_chunk.to_dict(orient='records')
                                col.insert_many(records)
                                isFistChunk = False
                        else:
                            raise TypeError("Unsupported data type: {}".format(type(data)))
                client.close() 
            except Exception as e:
                client.close()  # Ensure the connection is closed in case of an error
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
    
    async def _retreiveDatabase(self) -> tuple[MongoDataset, str, str, Literal['fail', 'replace', 'append']]:
        """Retrieve the database configuration.

        Returns:
            tuple[MongoDataset, str, str, Literal['fail', 'replace', 'append']]: A tuple containing the dataset, database name, table name, and ifExist option.

        Raises:
            ValueError: If no data source, database, or table is selected.
        """
        datasetId : str 
        if self.data.get('selectDataSource') and self.data['selectDataSource']['value']:
            datasetId = self.data['selectDataSource']['value']
        else:
            raise ValueError("No data source selected")
        dataset : MongoDataset  = await self.datasetService.get_dataset(datasetId)
        database = self.data['selectDatabaseDataSource']['value'] if self.data.get('selectDatabaseDataSource') and self.data['selectDatabaseDataSource'].get('value') else dataset.database
        collection = self.data.get('collectionAutoComplete').get('value') if self.data.get('collectionAutoComplete') and self.data.get('collectionAutoComplete').get('value')   else dataset.table
        ifExist = self.data.get('selectExist')['value'] if self.data.get('selectExist') and self.data.get('selectExist').get('value') else "fail"
        createIndex = self.data.get('createIndex')['value'] if self.data.get('createIndex') and self.data.get('createIndex').get('value') else False
        indexTable = self.data.get('indexTable')['value'] if self.data.get('indexTable') and self.data.get('indexTable').get('value') else 'id'
        if (collection is None or collection == ""):
            raise ValueError("No collection selected")
        if (database is None or database == ""):
            raise ValueError("No database selected")
        return dataset, database, collection, ifExist,createIndex,indexTable

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )