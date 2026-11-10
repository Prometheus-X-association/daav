import asyncio
import traceback
from typing import Optional, Any

from pydantic import ConfigDict
from app.enums.status_node import StatusNode
from app.models.interface.dataset_interface import DatasetParams, MongoDataset, Pagination
from app.models.interface.node_data import NodeDataPandasDf
from app.nodes.inputs.input_node import InputNode
from app.services.dataset_service import DatasetService
from app.utils.utils import generate_pandas_schema

class DataMongoBlock(InputNode):

    datasetService: Optional[DatasetService] = None

    def __init__(self, id: str, data: Any, revision: Optional[str] = None, status: Optional[StatusNode] = None):
        """Initialize a new DataMongoBlock instance.

        Args:
            data (Any): Data associated with the node
            id (str): Unique identifier for the node
            revision (Optional[str]): Revision identifier for the node
            status (Optional[StatusNode]): Current status of the node
        """
        super().__init__(id=id, data=data, revision=revision, status=status) 
        self.datasetService = DatasetService()   

    async def process(self, sample: bool = False) -> StatusNode:
        """Process the data from the Mongo database.

        Args:
            sample (bool): If True, retrieve a sample of the data (default is False).

        Returns:
            StatusNode: The status of the node after processing.
        """
        try:
            dataset, database, collection = await self._retreiveDatabase()
            dataset_param = DatasetParams(
                database=database,
                table=collection  # In MongoDB context, 'table' refers to 'collection'
            )
            
            try:
                if sample:
                    # For sample data, create pagination with 20 items per page
                    pagination = Pagination(
                        page=1,
                        perPage=20
                    )
                else:
                    # For full data processing, don't use pagination
                    pagination = None
                node_data : NodeDataPandasDf = self.datasetService.getDfMongoContent(dataset, dataset_param, pagination)
                

                for key, output in self.outputs.items():
                    if output.get_node_data():
                        # Update existing node data
                        output.get_node_data().nodeSchema = node_data.nodeSchema
                        if sample:
                            output.get_node_data().dataExample = node_data.dataExample
                        else:
                            output.get_node_data().data = node_data.data
                    else:
                        output.set_node_data(node_data, self)
                return StatusNode.Valid
            except Exception as e:
                traceback.print_exc()
                self.errorStackTrace = traceback.TracebackException.from_exception(e).format()
                self.statusMessage = e.__str__()
                return StatusNode.Error
        except ValueError as e:
            traceback.print_exc()
            self.errorStackTrace = traceback.TracebackException.from_exception(e).format()
            self.statusMessage = e.__str__()
            return StatusNode.Error

    async def _retreiveDatabase(self) -> tuple[MongoDataset, str, str]:
        """Retrieve the database configuration.

        Returns:
            tuple[MongoDataset, str, str]: A tuple containing the dataset, database name, and a collection name.

        Raises:
            ValueError: If no data source, database, or collection is selected.
        """
        dataset_id : str 
        if self.data.get('selectDataSource') and self.data['selectDataSource']['value']:
            dataset_id = self.data['selectDataSource']['value']
        else:
            raise ValueError("No data source selected")
        dataset : MongoDataset  = await self.datasetService.get_dataset(dataset_id)
        database = self.data['selectDatabaseDataSource']['value'] if self.data.get('selectDatabaseDataSource') and self.data['selectDatabaseDataSource'].get('value') else dataset.database
        collection = self.data['selectCollectionDataSource']['value'] if self.data.get('selectCollectionDataSource') and self.data['selectCollectionDataSource'].get('value') else dataset.collection
        if (collection is None or collection == ""):
            raise ValueError("No Collection selected")
        if (database is None or database == ""):
            raise ValueError("No database selected")
        return dataset, database, collection

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )