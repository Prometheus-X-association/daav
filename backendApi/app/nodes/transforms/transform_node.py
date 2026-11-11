from typing import Optional,Any

import pandas as pd
from pydantic import ConfigDict
from app.enums.status_node import StatusNode
from app.models.interface.node_data import NodeDataPandasDf
from app.nodes.node import Node
from app.utils.utils import generate_pandas_schema
class TransformNode(Node):

    def __init__(self, id: str, data: Any, revision: Optional[str] = None, status: Optional[StatusNode] = None):
        """Initialize a new TransformNode instance.

        Args:
            data (Any): Data associated with the node
            id (str): Unique identifier for the node
            revision (Optional[str]): Revision identifier for the node
            status (Optional[StatusNode]): Current status of the node
        """
        super().__init__(id=id ,data=data, revision=revision, status=status)

    def _publish_dataframe(self, df: pd.DataFrame, name: str, sample: bool) -> StatusNode:
        """Set the DataFrame as the data of the 'out' output (its example only in sample mode)."""
        if sample:
            node_data = NodeDataPandasDf(nodeSchema=generate_pandas_schema(df), dataExample=df, name=name)
        else:
            node_data = NodeDataPandasDf(nodeSchema=generate_pandas_schema(df), data=df, dataExample=df.head(20), name=name)
        self.outputs.get('out').set_node_data(node_data, self)
        return StatusNode.Valid

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )    