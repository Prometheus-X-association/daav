import traceback
from typing import Optional, Any

import pandas as pd
from pydantic import ConfigDict

from app.enums.status_node import StatusNode
from app.models.interface.dataset_interface import FileDataset, Pagination
from app.models.interface.node_data import NodeDataPandasDf
from app.nodes.inputs.input_node import InputNode
from app.services.dataset_service import DatasetService
import asyncio

class DataFileBlock(InputNode):

    datasetService: Optional[DatasetService] = None

    def __init__(self, id: str, data: Any, revision: Optional[str] = None, status: Optional[StatusNode] = None):
        """Initialize a new ExampleInput instance.

        Args:
            data (Any): Data associated with the node
            id (str): Unique identifier for the node
            revision (Optional[str]): Revision identifier for the node
            status (Optional[StatusNode]): Current status of the node
        """
        super().__init__(id=id, data=data, revision=revision, status=status)
        self.datasetService = DatasetService()    

    async def process(self, sample: bool = False):
        dataset = await self._retreiveDatabase()
        if sample:
            # For sample data, create pagination with 20 items per page
            pagination = Pagination(
                page=1,
                perPage=20
            )
        else:
            # For full data processing, don't use pagination
            pagination = None

        try:
            node_data = self.datasetService.getDfFileContentData(dataset, pagination)
            
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
            
        except ValueError as e:
            traceback.print_exc()
            self.errorStackTrace = traceback.TracebackException.from_exception(e).format()
            self.statusMessage = e.__str__()
            return StatusNode.Error

    async def _retreiveDatabase(self) -> FileDataset:
        """Retrieve the database configuration.

        Returns:
            tuple[MysqlDataset, str, str]: A tuple containing the dataset, database name, and table name.

        Raises:
            ValueError: If no data source, database, or table is selected.
        """
        dataset_id: str 
        if self.data.get('selectDataSource') and self.data['selectDataSource']['value']:
            dataset_id = self.data['selectDataSource']['value']
        else:
            raise ValueError("No data source selected")
        
        dataset: FileDataset = await self.datasetService.get_dataset(dataset_id)
        return dataset

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )