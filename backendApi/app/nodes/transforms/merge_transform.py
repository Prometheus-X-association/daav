import os
import traceback
from typing import Dict, List, Optional, Any

from pydantic import BaseModel, ConfigDict, TypeAdapter
from app.enums.status_node import StatusNode
from app.models.interface.node_data import NodeDataPandasDf, NodeDataParquet
from app.nodes.transforms.transform_node import TransformNode
import pandas as pd
import pyarrow.parquet as pq
import pyarrow as pa
import logging

from app.utils.security import PathSecurityValidator

from app.config.settings import settings

logger = logging.getLogger(__name__)

from app.utils.utils import generate_pandas_schema
class Source(BaseModel):
    id: str
    name: str
    type: str
    datasetId: str

class DataMappingItem(BaseModel):
    id: str
    sources: List[Source]
    targetName: str

class MergeTransform(TransformNode):

    def __init__(self, id: str, data: Any, revision: Optional[str] = None, status: Optional[StatusNode] = None):
        """Initialize a new ExampleTransform instance.

        Args:
            data (Any): Data associated with the node
            id (str): Unique identifier for the node
            revision (Optional[str]): Revision identifier for the node
            status (Optional[StatusNode]): Current status of the node
        """
        super().__init__(id=id, data=data, revision=revision, status=status)    

    def process(self, sample=False) -> StatusNode:
        """
        Processes the input data by merging columns from different sources based on a predefined mapping.
        Args:
            sample (bool, optional): If True, use sample data for processing. Defaults to False.
        Returns:
            StatusNode: The status of the node after processing. Returns StatusNode.Valid if successful, 
                        otherwise returns StatusNode.Error.
        Raises:
            ValueError: If the input data format  is not handle.

        """
        try:
            # Retrieve the data mapping
            data_mapping, parquet_save = self._retreiveColumnsMapping()
            
            if parquet_save:
                return self.process_if_parquet(data_mapping, sample)

            combined_df = pd.DataFrame()
            for mapping_item in data_mapping:
                target_name = mapping_item.targetName
                column_data = []

                # Sort sources by their order in the mapping item to ensure to keep the same order for all columns
                sorted_sources = sorted(mapping_item.sources, key=lambda x: x.id)

                # Iterate over each source in the mapping item
                for source in sorted_sources:
                    dataset_id = source.datasetId
                    column_name = source.name

                    if dataset_id in self.inputs:
                        source_df = self.inputs[dataset_id].get_node_data()
                        if isinstance(source_df, NodeDataPandasDf):
                            # Append the column data to the list
                            if sample:
                                column_data.append(source_df.dataExample[column_name])
                            else:
                                column_data.append(source_df.data[column_name])
                            
                        elif isinstance(source_df, NodeDataParquet):
                            # Read the Parquet file and extract the specified column and append it to the list
                            file_path = PathSecurityValidator.validate_file_path(source_df.data)
                            table = pq.read_table(file_path, columns=[column_name]).to_pandas()
                            column_data.append(table[column_name])
                        else:
                            raise ValueError(f"Input data {dataset_id} is not a handled format")

                # Concatenate all the column data
                if column_data:
                    combined_df[target_name] = pd.concat(column_data, ignore_index=True)
        except Exception as e:
            traceback.print_exc()
            self.errorStackTrace = traceback.TracebackException.from_exception(e).format()
            self.statusMessage = e.__str__()
            return StatusNode.Error      
        
        if sample:
            self.outputs.get('out').set_node_data(NodeDataPandasDf(nodeSchema=generate_pandas_schema(combined_df),dataExample=combined_df, name="Merged Data"),self)
        else:
            self.outputs.get('out').set_node_data(NodeDataPandasDf(nodeSchema = generate_pandas_schema(combined_df) ,data=combined_df,dataExample=combined_df.head(20), name="Merged Data"),self)
        return StatusNode.Valid
    
    def process_if_parquet(self, data_mapping, sample = False) -> StatusNode:
        """
        Processes the input data by merging columns from different sources based on a predefined mapping.
        Uses parquet file and batch processing to reduce memory usage.
        """

        # Determine the number of each source
        total_rows = 0
        source_sizes = {}
        row_group_sizes = {}
        upload_folder = settings.upload_dir

        for mapping_item in data_mapping:
            for source in mapping_item.sources:
                dataset_id = source.datasetId
                if dataset_id not in source_sizes and dataset_id in self.inputs:
                    source_data = self.inputs[dataset_id].get_node_data()
                    if isinstance(source_data, NodeDataPandasDf):
                        source_sizes[dataset_id] = len(source_data.dataExample) if sample else len(source_data.data)

                    elif isinstance(source_data, NodeDataParquet):
                        file_path = PathSecurityValidator.validate_file_path(source_data.data)
                        parquet_file = pq.ParquetFile(file_path)
                        source_sizes[dataset_id] = parquet_file.metadata.num_rows
                        num_row_groups = parquet_file.metadata.num_row_groups
                        
                        if num_row_groups > 0:
                            total_row_group_size = 0
                            for i in range(num_row_groups):
                                total_row_group_size += parquet_file.metadata.row_group(i).num_rows
                            row_group_sizes[dataset_id] = total_row_group_size // num_row_groups
                        else:
                            row_group_sizes[dataset_id] = source_sizes[dataset_id]

                    else:
                        raise Exception("Unkown input type")
        if source_sizes:
            total_rows = max(source_sizes.values())

        secure_path = os.path.join(upload_folder, f"merged_data_{self.id}.parquet")
        parquet_path = PathSecurityValidator.validate_file_path(secure_path)
        batch_size = 100
        parquet_writer = None
        schema = None
        column_types = {}

        #Process data in batches
        for start_idx in range(0, total_rows, batch_size):
            end_idx = min(start_idx + batch_size, total_rows)
            batch_df = pd.DataFrame(index = range(end_idx - start_idx))

            for mapping_item in data_mapping:
                target_name = mapping_item.targetName
                sorted_sources = sorted(mapping_item.sources, key = lambda x: x.id)

                target_column = pd.Series([None] * (end_idx - start_idx))
                current_position = 0

                for source in sorted_sources:
                    dataset_id = source.datasetId
                    column_name = source.name
                    if dataset_id in self.inputs:
                        source_data = self.inputs[dataset_id].get_node_data()
                        column_slice = None
                        if isinstance(source_data, NodeDataPandasDf):
                            df = source_data.dataExample if sample else source_data.data
                            
                            # Get slice of this column for the current batch
                            if start_idx < len(df) and current_position < (end_idx - start_idx):
                                slice_end = min(end_idx, len(df)) - start_idx
                                slice_size = min(slice_end, end_idx - start_idx - current_position)
                                if slice_size > 0:
                                    column_slice = df.iloc[start_idx:start_idx+slice_size][column_name].reset_index(drop=True)
                        
                        elif isinstance(source_data, NodeDataParquet):
                            row_group_size = row_group_sizes[dataset_id]
                            # Read just this batch from the parquet file
                            if current_position < (end_idx - start_idx):
                                file_path = PathSecurityValidator.validate_file_path(source_data.data)
                                parquet_file = pq.ParquetFile(source_data.data)
                                start_row_group = start_idx // row_group_size
                                end_row_group = (min(end_idx, source_sizes[dataset_id]) + row_group_size - 1) // row_group_size
                                row_groups_to_read = list(range(start_row_group, end_row_group))
                                
                                batches = parquet_file.iter_batches(
                                    columns=[column_name],
                                    row_groups=row_groups_to_read
                                )
                                df_slices = []
                                for batch in batches:
                                    df_slices.append(batch.to_pandas())
                                df_slice = pd.concat(df_slices, ignore_index=True) if df_slices else pd.DataFrame()
                                if len(df_slice) > 0:
                                    start_in_slice = start_idx % row_group_size
                                    end_in_slice = min(len(df_slice), start_in_slice + (end_idx - start_idx - current_position))
                                    if end_in_slice > start_in_slice:
                                        column_slice = df_slice.iloc[start_in_slice:end_in_slice][column_name].reset_index(drop=True)
                        else:
                            raise Exception("Unkown input type")

                        if column_slice is not None and len(column_slice) > 0:
                            slice_size = len(column_slice)
                            target_column.iloc[current_position:current_position + slice_size] = column_slice
                            current_position += slice_size
                batch_df[target_name] = target_column
            
            #to prevent that some batches has different schema
            for column in batch_df.columns:
                if batch_df[column].isna().all():
                    if column in column_types:
                        batch_df[column] = batch_df[column].astype(column_types[column])        #use the type already seen for this column
                else:
                    column_types[column] = batch_df[column].dtype

            if start_idx == 0 and schema is None:
                table = pa.Table.from_pandas(batch_df)
                schema = table.schema
                parquet_writer = pq.ParquetWriter(parquet_path, schema)
            else:
                table = pa.Table.from_pandas(batch_df, schema=schema)
            parquet_writer.write_table(table)

        if parquet_writer:
                parquet_writer.close()
            
        # Create the node data output
        parquet_file = pq.ParquetFile(parquet_path)
        schema = parquet_file.schema
        node_data = NodeDataParquet(
            data=parquet_path,
            nodeSchema=schema,
            name="merged_data",
        )
        self.outputs.get('out').set_node_data(node_data, self)
        return StatusNode.Valid
            
    def _retreiveColumnsMapping(self) -> tuple[List[DataMappingItem], bool]:
        if self.data.get('dataMapping') and self.data.get('parquetSave'):
            mappings = TypeAdapter(List[DataMappingItem]).validate_python(self.data.get('dataMapping'))
            parquet_save = self.data.get('parquetSave')['value']
            return mappings, parquet_save
        else:
            raise ValueError("Data Mapping is required")

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )