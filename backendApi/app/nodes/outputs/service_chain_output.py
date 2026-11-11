import asyncio
import json
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

class ServiceChainOutput(OutputNode):
    datasetService: Optional[DatasetService] = None

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

       
    async def process(self, sample=False) -> StatusNode:
        """Process the input data and return a JSON.
        
        Args:
            sample (bool): Flag to indicate if process on sample should be done. Defaults to False.
        
        Returns:
            StatusNode: The status of the node after processing
        """
        dataset= await self._retreiveEndpointConfig()

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
                            data=df_dict,
                            params={"foo": "bar"}
                        )

                    elif isinstance(data, NodeDataParquet):
                        # transform parquet file to JSON using duckdb directly
                        parquet_file_path = data.dataExample if sample else data.data
                        conn = duckdb.connect()
                        query = f"SELECT * FROM read_parquet('{parquet_file_path}')"
                        result = conn.sql(query).fetchall()
                        columns = [desc[0] for desc in conn.description]
                        conn.close()

                        # Convert to list of dictionaries
                        parquet_data = [dict(zip(columns, row)) for row in result]

                        pdc_response = PdcChainResponse(
                            chainId=chain_id,
                            targetId=target_id,
                            data=parquet_data,
                            params={"foo": "bar"}
                        )
                    else:
                        raise TypeError(f"Unsupported datatype: {type(data)}")
                    

                    if pdc_response and self.datasetService.pdcChainHeaders is not None:
                        url = f"{dataset.url}/service-chain/resume"
                        headers = {
                            "Content-Type": "application/json"
                        }
                        response = await asyncio.to_thread(requests.post, url, headers=headers, json=pdc_response.model_dump())

                        # Print the response from the server
                        #print(response.status_code)
                        #print(response.json())
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
        return dataset
    
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )