from typing import Iterator, Optional, Any

import pandas as pd
from pydantic import ConfigDict
from app.models.interface.node_data import NodeDataPandasDf
from app.nodes.node import Node
from app.enums.status_node import StatusNode

class OutputNode(Node):

    def __init__(self, id: str, data: Any, revision: Optional[str] = None, status: Optional[StatusNode] = None):
        """Initialize a new OutputNode instance.

        Args:
            data (Any): Data associated with the node
            id (str): Unique identifier for the node
            revision (Optional[str]): Revision identifier for the node
            status (Optional[StatusNode]): Current status of the node
        """
        super().__init__(id=id, data=data, revision=revision, status=status)   

    def _connected_data(self) -> Iterator[Any]:
        """Yield the node data of each connected input, in the order of the inputs."""
        for input in self.inputs.values():
            if input.get_connected_node():
                yield input.get_node_data()

    @staticmethod
    def _input_dataframe(data: NodeDataPandasDf, sample: bool) -> pd.DataFrame:
        """DataFrame of an input (its example for a sample).

        Raises:
            ValueError: If the input does not hold a DataFrame.
        """
        df = data.dataExample if sample else data.data
        if not isinstance(df, pd.DataFrame):
            raise ValueError("Input data is not a pandas DataFrame")
        return df

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )    


