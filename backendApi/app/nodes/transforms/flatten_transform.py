import traceback
from typing import Dict, List, Optional, Any

from pydantic import BaseModel, ConfigDict, TypeAdapter
from app.enums.status_node import StatusNode
from app.models.interface.node_data import NodeDataPandasDf, NodeDataParquet
from app.nodes.transforms.transform_node import TransformNode
import pandas as pd
import pyarrow.parquet as pq
import pyarrow as pa

from app.utils.utils import generate_pandas_schema

class FlattenTransform(TransformNode):

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
        Processes the input data by flattening JSON structures and exploding arrays automatically.
        Args:
            sample (bool, optional): If True, use sample data for processing. Defaults to False.
        Returns:
            StatusNode: The status of the node after processing. Returns StatusNode.Valid if successful, 
                        otherwise returns StatusNode.Error.
        Raises:
            ValueError: If the input data format is not handled.
        """
        try:
            # Retrieve the data mapping
            parquet_save = self._retreiveColumnsMapping()
            
            if parquet_save:
                raise ValueError(f"Parquet output no supported actually for flatten transform")

            source_df = self.inputs['datasource'].get_node_data()

            if isinstance(source_df, NodeDataPandasDf):
                if sample:
                    data_records = source_df.dataExample.to_dict(orient='records')
                else:
                    data_records = source_df.data.to_dict(orient='records')
            elif isinstance(source_df, NodeDataParquet):
                if sample:
                    table = pq.read_table(source_df.dataExample).to_pandas()
                else:
                    table = pq.read_table(source_df.data).to_pandas()
                data_records = table.to_dict(orient='records')
            else:
                raise ValueError(f"Input data is not a handled format")

            # Flattend data : remove nested structures with '.' separator for nested keys
            flatten_df = pd.json_normalize(data_records, sep='_')
            
            # seach for columns wich contains arrays -> List
            array_columns = []
            for col in flatten_df.columns:
                if flatten_df[col].apply(lambda x: isinstance(x, list)).any():
                    sample_values = flatten_df[col].dropna()
                    if not sample_values.empty:
                        first_list = next(iter(sample_values))
                        if isinstance(first_list, list) and first_list and isinstance(first_list[0], dict):
                            array_columns.append(col)
            
            for array_col in array_columns:
                # explode the array column into rows
                exploded_df = flatten_df.explode(array_col).reset_index(drop=True)
                
                # if the colums contains non-empty lists, normalize the objects in the exploded column
                if not exploded_df[array_col].dropna().empty:
                    array_normalized = pd.json_normalize(exploded_df[array_col].dropna().tolist())
                    
                    # Use underscore separator instead of dot for consistency
                    array_normalized.columns = [f"{array_col}_{col}" for col in array_normalized.columns]
                    
                    array_normalized.index = exploded_df[exploded_df[array_col].notna()].index
                    exploded_df = exploded_df.drop(columns=[array_col])
                    flatten_df = exploded_df.join(array_normalized, how='left')
                else:
                    flatten_df = exploded_df
            
            # clean Index
            flatten_df = flatten_df.reset_index(drop=True)
            
        except Exception as e:
            traceback.print_exc()
            self.errorStackTrace = traceback.TracebackException.from_exception(e).format()
            self.statusMessage = e.__str__()
            return StatusNode.Error      
        
        if sample:
            self.outputs.get('out').set_node_data(NodeDataPandasDf(nodeSchema=generate_pandas_schema(flatten_df),dataExample=flatten_df, name="Flattened Data"),self)
        else:
            self.outputs.get('out').set_node_data(NodeDataPandasDf(nodeSchema = generate_pandas_schema(flatten_df) ,data=flatten_df,dataExample=flatten_df.head(20), name="Flattened Data"),self)
        return StatusNode.Valid   
            
    def _retreiveColumnsMapping(self) -> bool:
        if  self.data.get('parquetSave'):
            parquet_save = self.data.get('parquetSave')['value']
            return parquet_save
        else:
            raise ValueError("Data Mapping is required")

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )