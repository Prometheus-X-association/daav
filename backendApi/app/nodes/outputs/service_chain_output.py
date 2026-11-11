import json
from app.models.interface.dataset_interface import PTXDataset
from app.nodes.outputs.output_node import OutputNode
from app.nodes.outputs.pdc_chain_mixin import PdcChainMixin
from app.models.interface.pdc_chain_interface import PdcChainResponse, PdcChainRequest
from pydantic import ConfigDict
from typing import Optional, Any, Dict, List
import duckdb
import os

from app.enums.status_node import StatusNode
from app.models.interface.node_data import NodeDataPandasDf, NodeDataParquet
from app.services.dataset_service import DatasetService
from app import main

class ServiceChainOutput(PdcChainMixin, OutputNode):
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
            for data in self._connected_data():
                pdc_response = self._build_response(data, sample)
                await self._resume_chain(dataset, pdc_response)
        except Exception as e:
            return self._fail(e)
        return StatusNode.Valid

    def _build_response(self, data: Any, sample: bool) -> PdcChainResponse:
        """Build the service chain response that carries the rows of an input."""
        chain_id, target_id = self._chain_ids()
        if isinstance(data, NodeDataPandasDf):
            df_data = data.dataExample if sample else data.data
            rows = df_data.to_dict(orient='records')
        elif isinstance(data, NodeDataParquet):
            rows = self._parquet_rows(data.data, sample)
        else:
            raise TypeError(f"Unsupported datatype: {type(data)}")
        return PdcChainResponse(
            chainId=chain_id,
            targetId=target_id,
            data=rows,
            params={"foo": "bar"}
        )

    @staticmethod
    def _parquet_rows(parquet_file_path: str, sample: bool) -> List[Dict[str, Any]]:
        """Rows of a parquet file as dictionaries."""
        # transform parquet file to JSON using duckdb directly
        # A parquet node data only carries its file: a sample is its first 20 rows
        conn = duckdb.connect()
        query = f"SELECT * FROM read_parquet('{parquet_file_path}')"
        if sample:
            query += " LIMIT 20"
        # execute() fills conn.description with the column names, sql() does not
        result = conn.execute(query).fetchall()
        columns = [desc[0] for desc in conn.description]
        conn.close()

        # Convert to list of dictionaries
        return [dict(zip(columns, row)) for row in result]

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