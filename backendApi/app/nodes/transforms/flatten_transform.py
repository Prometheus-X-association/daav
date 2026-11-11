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
            if self._retreiveColumnsMapping():
                raise ValueError("Parquet output no supported actually for flatten transform")

            # Flattend data : remove nested structures with '_' separator for nested keys
            flatten_df = pd.json_normalize(self._load_records(sample), sep='_')

            # explode the columns which contain arrays of objects into rows
            for array_col in self._array_of_dict_columns(flatten_df):
                flatten_df = self._explode_column(flatten_df, array_col)

            # clean Index
            flatten_df = flatten_df.reset_index(drop=True)
        except Exception as e:
            return self._fail(e)

        return self._publish_dataframe(flatten_df, "Flattened Data", sample)

    def _load_records(self, sample: bool) -> list:
        """Records of the input data (of its example in sample mode)."""
        source_df = self.inputs['datasource'].get_node_data()
        if isinstance(source_df, NodeDataPandasDf):
            frame = source_df.dataExample if sample else source_df.data
            return frame.to_dict(orient='records')
        if isinstance(source_df, NodeDataParquet):
            path = source_df.dataExample if sample else source_df.data
            return pq.read_table(path).to_pandas().to_dict(orient='records')
        raise ValueError("Input data is not a handled format")

    @staticmethod
    def _array_of_dict_columns(df: pd.DataFrame) -> list:
        """Columns whose first non-null value is a non-empty list of objects."""
        return [col for col in df.columns if FlattenTransform._is_array_of_dicts(df[col])]

    @staticmethod
    def _is_array_of_dicts(values: pd.Series) -> bool:
        if not values.apply(lambda x: isinstance(x, list)).any():
            return False
        sample_values = values.dropna()
        if sample_values.empty:
            return False
        first_list = next(iter(sample_values))
        return isinstance(first_list, list) and bool(first_list) and isinstance(first_list[0], dict)

    @staticmethod
    def _explode_column(df: pd.DataFrame, array_col: str) -> pd.DataFrame:
        """One row per item of the array column, the objects being normalized into '<column>_<key>' columns."""
        exploded_df = df.explode(array_col).reset_index(drop=True)
        # an empty list gives an empty row: nothing to normalize
        if exploded_df[array_col].dropna().empty:
            return exploded_df
        array_normalized = pd.json_normalize(exploded_df[array_col].dropna().tolist())
        # Use underscore separator instead of dot for consistency
        array_normalized.columns = [f"{array_col}_{col}" for col in array_normalized.columns]
        array_normalized.index = exploded_df[exploded_df[array_col].notna()].index
        exploded_df = exploded_df.drop(columns=[array_col])
        return exploded_df.join(array_normalized, how='left')

    def _retreiveColumnsMapping(self) -> bool:
        if  self.data.get('parquetSave'):
            parquet_save = self.data.get('parquetSave')['value']
            return parquet_save
        else:
            raise ValueError("Data Mapping is required")

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )