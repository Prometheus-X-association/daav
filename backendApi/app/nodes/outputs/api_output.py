import logging
import os
import traceback
from typing import Any, Optional

import duckdb
from app.core.execution_context import ExecutionContext
from app.enums.status_node import StatusNode
from app.nodes.outputs.output_node import OutputNode
from app import main
from app.models.interface.node_data import NodeDataPandasDf, NodeDataParquet
from app.services.workflow_service import WorkflowService
from app.utils.security import PathSecurityValidator

from app.config.settings import settings
class ApiOutput(OutputNode):

    workflowService: Optional[WorkflowService] = None

    def __init__(self, id: str, data: Any, revision: Optional[str] = None, status: Optional[StatusNode] = None):
        """Initialize a new ApiOutput instance.
        
        Args:
            id (str): Unique identifier for the node
            data (Any): Data associated with the node
            revision (Optional[str]): Revision identifier for the node
            status (Optional[StatusNode]): Current status of the node
        """
        super().__init__(id=id, data=data, revision=revision, status=status)
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
        matching_nodes = [
            node
            for wf in await self.workflowService.get_workflows()
            for node in wf.pschema.nodes
            if node.type == "ApiOutput"
            and node.data.get("urlInput", {}).get("value") == url
            and node.id != self.id 
        ]

        if matching_nodes:
            raise ValueError(f"URL '{url}' is already in use")

    async def process(self, sample = False) -> StatusNode:
        """Process the input data and return a JSON.
        
        Args:
            sample (bool): Flag to indicate if process on sample should be done. Defaults to False.
        
        Returns:
            StatusNode: The status of the node after processing
        """
        _, url, _ = self._retreiveEndpointConfig()
        file_path: str = self.get_output_file_path()
        
        try:
            await self._check_url_uniqueness(url)
        except ValueError as e:
            self.statusMessage = str(e)
            return StatusNode.Error

        try:
            for input in self.inputs.values():
                if(input.get_connected_node()):
                    data = input.get_node_data()

                    if isinstance(data, NodeDataPandasDf):
                        df_data = data.dataExample if sample else data.data
                        df_data.to_json(file_path, orient='records')

                    elif isinstance(data, NodeDataParquet):
                        # transform parquet file to JSON using duckdb
                        secure_file_path = PathSecurityValidator.validate_file_path(data.data)
                        conn = duckdb.connect()
                        query = f"COPY (SELECT * FROM read_parquet('{secure_file_path}')) TO '{file_path}' (FORMAT JSON, ARRAY true)"
                        conn.sql(query)
                        conn.close()

                    else:
                        raise TypeError(f"Unsopported datatype: {type(data)}")
                    
            if not os.path.exists(file_path):
                self.statusMessage = "No data was generated"
                return StatusNode.Error
        except Exception as e:
            traceback.print_exc()
            self.errorStackTrace = traceback.TracebackException.from_exception(e).format()
            self.statusMessage = e.__str__()
            return StatusNode.Error
        return StatusNode.Valid
    
    def _retreiveEndpointConfig(self):
        if self.data.get('nameInput').get('value') and self.data.get('urlInput').get('value') and self.data.get('tokenInput').get('value'):
            name = self.data.get('nameInput').get('value')
            url = self.data.get('urlInput').get('value')
            token = self.data.get('tokenInput').get('value')
            return name, url, token
        else:
            raise ValueError("Error in retreiving inputs")