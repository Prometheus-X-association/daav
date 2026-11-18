import asyncio
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
            dataset, database, collection, if_exist, _, _ = await self._retreiveDatabase()
            return self._write(dataset, database, collection, if_exist, sample)
        except ValueError as e:
            return self._fail(e)

    def _write(self, dataset: MongoDataset, database: str, collection: str, if_exist: str, sample: bool) -> StatusNode:
        """Insert the connected input data into the collection; the client is always closed."""
        client = None
        try:
            # Connect to the MongoDB database
            client = MongoClient(dataset.uri)
            col = self._prepare_collection(client[database], collection, if_exist)
            for data in self._connected_data():
                if isinstance(data, NodeDataPandasDf):
                    self._insert_dataframe(col, self._input_dataframe(data, sample))
                elif isinstance(data, NodeDataParquet):
                    self._insert_parquet(col, data.data, sample)
                else:
                    raise TypeError("Unsupported data type: {}".format(type(data)))
        except Exception as e:
            return self._fail(e)
        finally:
            if client is not None:
                client.close()
        return StatusNode.Valid

    @staticmethod
    def _prepare_collection(db, collection: str, if_exist: str):
        """Create, keep or recreate the collection according to the ifExist parameter, and return it."""
        if collection not in db.list_collection_names():
            # Collection doesn't exist, create it
            print(f"Collection '{collection}' does not exist. Creating it now.")
            db.create_collection(collection)
            print(f"Collection '{collection}' created successfully.")
        elif if_exist == 'fail':
            raise ValueError(f"Collection '{collection}' already exists and ifExist is set to 'fail'")
        elif if_exist == 'replace':
            print(f"Dropping existing collection '{collection}' because ifExist is set to 'replace'")
            db.drop_collection(collection)
            print(f"Creating new collection '{collection}'")
            db.create_collection(collection)
        # For 'append', we don't need to do anything special
        return db[collection]

    @staticmethod
    def _insert_dataframe(col, df: pd.DataFrame) -> None:
        for df_chunk in utils.slice_generator(df):
            col.insert_many(df_chunk.to_dict(orient='records'))

    @staticmethod
    def _insert_parquet(col, path: str, sample: bool) -> None:
        """Insert a parquet file by batches; a sample only inserts the first batch."""
        chunk_size = 1000
        parquet_file = pq.ParquetFile(path)
        for batch in parquet_file.iter_batches(batch_size=chunk_size):
            col.insert_many(batch.to_pandas().to_dict(orient='records'))
            if sample:
                break

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