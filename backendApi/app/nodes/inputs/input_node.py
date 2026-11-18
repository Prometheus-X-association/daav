from typing import Optional, Any

import pandas as pd
from pyarrow.parquet import ParquetSchema
from pydantic import ConfigDict
from app.core.output_node import NodeOutput
from app.enums.status_node import StatusNode
from app.models.interface.node_data import NodeDataPandasDf, NodeDataParquet
from app.nodes.node import Node

class InputNode(Node):
    
    def __init__(self, id: str, data: Any, revision: Optional[str] = None, status: Optional[StatusNode] = None):
        """Initialize a new InputNode instance.

        Args:
            data (Any): Data associated with the node
            id (str): Unique identifier for the node
            revision (Optional[str]): Revision identifier for the node
            status (Optional[StatusNode]): Current status of the node
        """
        super().__init__(id=id, data=data, revision=revision, status=status)    

    def _publish(self, output: NodeOutput, name: Optional[str], schema: Any, df: Optional[pd.DataFrame] = None,
                 parquet_path: Optional[str] = None, sample: bool = False) -> None:
        """Publish the result of the node on an output: its node data is updated, or created with the given name.

        The result is a parquet file when parquet_path is given, else a DataFrame.

        Raises:
            ValueError: If the output already holds node data of the other type.
        """
        if parquet_path is not None:
            self._publish_parquet(output, name, schema, parquet_path)
            return
        node_data = output.get_node_data()
        if node_data and not isinstance(node_data, NodeDataPandasDf):
            raise ValueError("Output node data is not of type NodeDataPandasDf")
        self._publish_dataframe(output, name, schema, df, sample)

    def _publish_dataframe(self, output: NodeOutput, name: Optional[str], schema: Any, df: pd.DataFrame,
                           sample: bool) -> None:
        """Update the DataFrame node data of an output, or create it: a sample fills the example, not the data."""
        node_data = output.get_node_data()
        if node_data:
            # Update existing node data
            node_data.nodeSchema = schema
            self._set_dataframe(node_data, df, sample)
        else:
            # Create new node data
            node_data = NodeDataPandasDf(nodeSchema=schema, name=name)
            self._set_dataframe(node_data, df, sample)
            output.set_node_data(node_data, self)

    @staticmethod
    def _set_dataframe(node_data: NodeDataPandasDf, df: pd.DataFrame, sample: bool) -> None:
        if sample:
            node_data.dataExample = df
        else:
            node_data.data = df

    def _publish_parquet(self, output: NodeOutput, name: Optional[str], schema: Any, parquet_path: str) -> None:
        """Update the parquet node data of an output, or create it."""
        node_data = output.get_node_data()
        if node_data:
            # Update existing node data
            if not isinstance(node_data, NodeDataParquet):
                raise ValueError("Output node data is not of type NodeDataParquet")
            node_data.data = parquet_path
            node_data.nodeSchema = schema
        elif isinstance(schema, ParquetSchema):
            # Create new node data
            output.set_node_data(NodeDataParquet(data=parquet_path, nodeSchema=schema, name=name), self)
        else:
            raise ValueError("Schema is not a ParquetSchema")

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )    
