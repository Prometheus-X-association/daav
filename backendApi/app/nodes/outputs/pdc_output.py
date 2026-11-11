import asyncio
import json

from fastapi import logger
from app.core.execution_context import ExecutionContext
from app.models.interface.dataset_interface import PTXDataset
from app.nodes.outputs.output_node import OutputNode
from app.models.interface.pdc_chain_interface import PdcChainResponse, PdcChainRequest
from pydantic import ConfigDict
from typing import Optional, Any, Dict, List
import duckdb
import traceback
import os
import requests

from app.enums.status_node import StatusNode
from app.models.interface.node_data import NodeDataPandasDf, NodeDataParquet
from app.services.dataset_service import DatasetService
from app import main
from app.services.workflow_service import WorkflowService
from app.utils.security import PathSecurityValidator
from app.config.settings import settings


def _read_json_file(path: str) -> Any:
    """Read a JSON file (run in a worker thread so that it does not block the event loop)"""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def _write_json_file(path: str, data: Any) -> None:
    """Write a JSON file (run in a worker thread so that it does not block the event loop)"""
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f)


class PdcOutput(OutputNode):
    datasetService: Optional[DatasetService] = None
    workflowService: Optional[WorkflowService] = None

    def __init__(self, id: str, data: Any, revision: Optional[str] = None, status: Optional[StatusNode] = None):
        """Initialize a new PDCOutput instance.
        
        Args:
            id (str): Unique identifier for the node
            data (Any): Data associated with the node
            revision (Optional[str]): Revision identifier for the node
            status (Optional[StatusNode]): Current status of the node
        """
        super().__init__(id=id, data=data, revision=revision, status=status)
        self.datasetService = DatasetService()
        self.workflowService = WorkflowService()

    
    def get_output_file_path(self) -> str:
        """ Return the output file path for this node
        """

        # Get user context for file isolation
        current_user = ExecutionContext.get_user()        
        safe_filename = PathSecurityValidator.validate_filename(f"{self.id}-output.json")
        if current_user:
            file_path = os.path.join(os.path.join(settings.upload_dir, current_user.id), safe_filename)
        else:
            file_path = os.path.join(settings.upload_dir, safe_filename)
        secure_path = PathSecurityValidator.validate_file_path(file_path)
        return secure_path
    
    async def _check_url_uniqueness(self, url: str) -> None:
        """Check if the URL is already in use by another PdcOutput node.
        
        Args:
            url (str): The URL to check for uniqueness
            
        Raises:
            ValueError: If the URL is already in use by another node
        """
        matching_nodes = [
            node
            for wf in await self.workflowService.get_workflows()
            for node in wf.pschema.nodes
            if node.type == "PdcOutput"
            and node.data.get("urlInput", {}).get("value") == url
            and node.id != self.id 
        ]

        if matching_nodes:
            raise ValueError(f"URL '{url}' is already in use")        
    
    async def process(self, sample=False) -> StatusNode:
        """Process the input data and return a JSON.
        
        Args:
            sample (bool): Flag to indicate if process on sample should be done. Defaults to False.
        
        Returns:
            StatusNode: The status of the node after processing
        """
        file_path: str = self.get_output_file_path()
        dataset, url = await self._retreiveEndpointConfig()



        try:
            await self._check_url_uniqueness(url)
        except ValueError as e:
            self.statusMessage = str(e)
            return StatusNode.Error

        try:
            for input in self.inputs.values():
                if(input.get_connected_node()):
                    data = input.get_node_data()

                    chain_id = ''
                    target_id = ''

                    if self.datasetService.pdcChainHeaders is not None:
                        chain_id = self.datasetService.pdcChainHeaders.x_ptx_service_chain_id
                        target_id = self.datasetService.pdcChainHeaders.x_ptx_target_id

                    pdc_response: Optional[PdcChainResponse] = None

                    if isinstance(data, NodeDataPandasDf):
                        df_data = data.dataExample if sample else data.data
                        df_dict = df_data.to_dict(orient='records')

                        pdc_response = PdcChainResponse(
                            chainId=chain_id,
                            targetId=target_id,
                            data=df_dict
                        )

                    elif isinstance(data, NodeDataParquet):
                        # transform parquet file to JSON using duckdb
                        parquet_file_path = PathSecurityValidator.validate_file_path(data.data)
                        conn = duckdb.connect()
                        query = f"COPY (SELECT * FROM read_parquet('{parquet_file_path}')) TO '{file_path}' (FORMAT JSON, ARRAY true)"
                        conn.sql(query)
                        conn.close()

                        parquet_data = await asyncio.to_thread(_read_json_file, file_path)

                        pdc_response = PdcChainResponse(
                            chainId=chain_id,
                            targetId=target_id,
                            data=parquet_data
                        )
                    else:
                        raise TypeError(f"Unsopported datatype: {type(data)}")
                    
                    #cache
                    if pdc_response is not None:
                        await asyncio.to_thread(_write_json_file, file_path, pdc_response.model_dump())

                    if pdc_response and self.datasetService.pdcChainHeaders is not None:
                        url = f"{dataset.url}/service-chain/resume"
                        headers = {
                            "Content-Type": "application/json"
                        }
                        await asyncio.to_thread(requests.post, url, headers=headers, json=pdc_response.model_dump())
            if not os.path.exists(file_path):
                self.statusMessage = "No data was generated"
                return StatusNode.Error
        except Exception as e:
            traceback.print_exc()
            self.errorStackTrace = traceback.TracebackException.from_exception(e).format()
            self.statusMessage = e.__str__()
            return StatusNode.Error
        return StatusNode.Valid
    
    async def _retreiveEndpointConfig(self):
        dataset_id : str 
        if self.data.get('selectDataSource') and self.data['selectDataSource']['value']:
            dataset_id = self.data['selectDataSource']['value']
        else:
            raise ValueError("No data source selected")

        dataset: PTXDataset = await self.datasetService.get_dataset(dataset_id)
        if not dataset:
            raise ValueError("Dataset not found")
        if self.data.get('urlInput').get('value'):
            url = self.data.get('urlInput').get('value')
            return dataset, url
        else:
            raise ValueError("Error in retreiving inputs")
    
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )