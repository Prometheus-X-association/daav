from typing import Optional, Any

from pydantic import ConfigDict
from app.enums.status_node import StatusNode
from app.models.interface.node_data import NodeDataPandasDf
from app.nodes.transforms.transform_node import TransformNode
import pandas as pd

from app.utils.utils import generate_pandas_schema

class ExampleTransform(TransformNode):

    def __init__(self, id: str, data: Any, revision: Optional[str] = None, status: Optional[StatusNode] = None):
        """Initialize a new ExampleTransform instance.

        Args:
            data (Any): Data associated with the node
            id (str): Unique identifier for the node
            revision (Optional[str]): Revision identifier for the node
            status (Optional[StatusNode]): Current status of the node
        """
        super().__init__(id=id, data=data, revision=revision, status=status)    

    def process(self,sample = False)->StatusNode:
        for key, input in self.inputs.items():
            if input.get_connected_node() and input.get_node_data() and isinstance(input.get_node_data(), NodeDataPandasDf):
                df = input.get_node_data().data
                if not isinstance(df, pd.DataFrame):
                    raise ValueError("Input data is not a pandas DataFrame")
                df['age'] = df['age'].astype(int)
                df['age'] = df['age'] + 1
        
                schema = generate_pandas_schema(df)

                node_data = NodeDataPandasDf(
                    dataExample=df,
                    data=df,
                    nodeSchema=schema,
                    name="Example Pandas DataFrame transformed"
                )
                for output in self.outputs.values():
                    output.set_node_data(node_data,node = self)
            break        
        
        return StatusNode.Valid

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )    