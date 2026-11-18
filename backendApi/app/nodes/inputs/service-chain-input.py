import asyncio
import pyarrow.parquet as pq
from typing import List, Optional, Any
import pandas as pd
from pydantic import ConfigDict
from app.enums.status_node import StatusNode
from app.models.interface.dataset_interface import PTXDataset
from app.models.interface.pdc_chain_interface import PdcChainRequestData
from app.nodes.inputs.input_node import InputNode
from app.services.dataset_service import DatasetService
from app.utils.utils import generate_pandas_schema
from sqlalchemy import create_engine
import pyarrow as pa
from pyarrow.parquet import ParquetSchema


class ServiceChainInput(InputNode):
    """
    DataPdcChainBlock is responsible for retrieving data from a PDC Chain service  and processing it into a pandas DataFrame.
    """
    datasetService: Optional[DatasetService] = None

    def __init__(self, id: str, data: Any, revision: Optional[str] = None, status: Optional[StatusNode] = None):
        """Initialize a new DataPdcChainBlock instance.

        Args:
            id (str): Unique identifier for the node
            data (Any): Data associated with the node
            revision (Optional[str]): Revision identifier for the node
            status (Optional[StatusNode]): Current status of the node
        """
        super().__init__(id=id, data=data, revision=revision, status=status)    
        self.datasetService = DatasetService()

    async def process(self, sample: bool = False) -> StatusNode:
        """Process the data from the MySQL database.

        Args:
            sample (bool): If True, retrieve a sample of the data (default is False).

        Returns:
            StatusNode: The status of the node after processing.
        """
        try:
            dataset,parquet_save,input_data_source_example = await self._retreiveDatabase()
            return self._publish_datasets(dataset, parquet_save, input_data_source_example, sample)
        except ValueError as e:
            return self._fail(e)

    def _publish_datasets(self, dataset: PTXDataset, parquet_save: bool, examples: List, sample: bool) -> StatusNode:
        """Publish each dataset of the service chain (or each example for a sample) on its output pdc-<index>."""
        try:
            datasets = self._datasets_to_process(sample, examples)
            # A sample is always kept in memory, even when the parquet option is on
            as_parquet = parquet_save and not sample
            for index, chain_data in enumerate(datasets):

                df = pd.DataFrame(chain_data)
                schema = generate_pandas_schema(df)
                parquet_path = None
                if as_parquet:
                    parquet_path = f"{dataset.id}_{index}.parquet"
                    schema = self._dump_to_parquet(df, parquet_path)

                output = self.outputs.get(f"pdc-{index}")
                self._publish(output, self._new_data_name(output, sample, index), schema, df, parquet_path, sample)
            return StatusNode.Valid
        except Exception as e:
            return self._fail(e)

    def _datasets_to_process(self, sample: bool, examples: List) -> List:
        """The examples of the node for a sample, else the data received from the service chain."""
        if sample:
            return examples
        chain_data = self.datasetService.pdcChainData
        if not isinstance(chain_data, PdcChainRequestData):
            return [chain_data]
        datasets = [chain_data.origin]
        # additionalData is optional: a request may only carry its origin data
        for additional_data in chain_data.additionalData or []:
            datasets.append(additional_data.data)
        return datasets

    @staticmethod
    def _dump_to_parquet(df: pd.DataFrame, parquet_path: str) -> ParquetSchema:
        """Write the DataFrame to a parquet file, and return the schema of the file."""
        print(f"Saving data to {parquet_path}")
        table = pa.Table.from_pandas(df)
        parquet_writer = pq.ParquetWriter(parquet_path, table.schema)
        parquet_writer.write_table(table)
        parquet_writer.close()

        parquet_file = pq.ParquetFile(parquet_path)
        return parquet_file.schema

    def _new_data_name(self, output, sample: bool, index: int) -> Optional[str]:
        """Name of the node data to create on an output; None when the output already holds its node data."""
        if output.get_node_data():
            return None
        chain_headers = self.datasetService.pdcChainHeaders
        return f"{'Example' if sample else chain_headers.x_ptx_service_chain_id} {index}"

    async def _retreiveDatabase(self) -> tuple[PTXDataset, bool, List]:
        """Retrieve the database configuration.

        Returns:
            tuple[MysqlDataset, str, str]: A tuple containing the dataset, database name, and table name.

        Raises:
            ValueError: If no data source, database, or table is selected.
        """
        dataset_id : str 
        if self.data.get('selectDataSource') and self.data['selectDataSource']['value']:
            dataset_id = self.data['selectDataSource']['value']
        else:
            raise ValueError("No data source selected")
        dataset : PTXDataset  = await self.datasetService.get_dataset(dataset_id)
        if self.data.get('inputsDatasource'):
             input_data_source_example = self.data.get('inputsDatasource')
        else:
            raise ValueError("No datasource example")
        parquet_save = self.data['parquetSave']['value'] if self.data.get('parquetSave') else False
        return dataset, parquet_save , input_data_source_example


    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )

