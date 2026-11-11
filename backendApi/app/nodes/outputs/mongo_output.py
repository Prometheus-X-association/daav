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
            dataset, database, collection, if_exist ,create_index,index_table = await self._retreiveDatabase()

            client = None
            try:
                # Connect to the MongoDB database
                client = MongoClient(dataset.uri)
                db = client[database]

                # Handle collection existence based on ifExist parameter
                collection_exists = collection in db.list_collection_names()
                if collection_exists:
                    if if_exist == 'fail':
                        raise ValueError(f"Collection '{collection}' already exists and ifExist is set to 'fail'")
                    elif if_exist == 'replace':
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
                            chunk_size = 1000 
                            is_first_chunk = True
                            parquet_file = pq.ParquetFile(data.data)

                            for batch in parquet_file.iter_batches(batch_size=chunk_size):
                                df_chunk = batch.to_pandas()
                                if sample and is_first_chunk:
                                    records = df_chunk.to_dict(orient='records')
                                    col.insert_many(records)
                                    break
                                if_exists = if_exist if is_first_chunk else 'append'
                                records = df_chunk.to_dict(orient='records')
                                col.insert_many(records)
                                is_first_chunk = False
                        else:
                            raise TypeError("Unsupported data type: {}".format(type(data)))
            except Exception as e:
                traceback.print_exc()
                self.errorStackTrace = traceback.TracebackException.from_exception(e).format()
                self.statusMessage = e.__str__()
                return StatusNode.Error
            finally:
                if client is not None:
                    client.close()
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
        dataset_id : str 
        if self.data.get('selectDataSource') and self.data['selectDataSource']['value']:
            dataset_id = self.data['selectDataSource']['value']
        else:
            raise ValueError("No data source selected")
        dataset : MongoDataset  = await self.datasetService.get_dataset(dataset_id)
        database = self._param('selectDatabaseDataSource') or dataset.database
        collection = self._param('collectionAutoComplete') or dataset.table
        if_exist = self._param('selectExist', "fail")
        create_index = self._param('createIndex', False)
        index_table = self._param('indexTable', 'id')
        if (collection is None or collection == ""):
            raise ValueError("No collection selected")
        if (database is None or database == ""):
            raise ValueError("No database selected")
        return dataset, database, collection, if_exist,create_index,index_table

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )