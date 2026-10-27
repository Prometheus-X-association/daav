from typing import Optional, Any

import pandas as pd
from pydantic import ConfigDict

from app.enums.status_node import StatusNode
from app.models.interface.node_data import NodeDataPandasDf
from app.nodes.inputs.input_node import InputNode
from app.utils.utils import generate_pandas_schema


class ExampleInput(InputNode):

    def __init__(self, id: str, data: Any, revision: Optional[str] = None, status: Optional[StatusNode] = None):
        """Initialize a new ExampleInput instance.

        Args:
            data (Any): Data associated with the node
            id (str): Unique identifier for the node
            revision (Optional[str]): Revision identifier for the node
            status (Optional[StatusNode]): Current status of the node
        """
        super().__init__(id=id, data=data, revision=revision, status=status)    

    def process(self, sample: bool = False):

        df = pd.DataFrame([['De Pouille', 'Frénégonde',28], ['Fripouille', 'Jacquouille',32], ['De MontMiraille', 'Godefroy',36], ['Le purineur', 'Prosper',34]],
                  index=[1, 2, 3, 4],
                  columns=['nom', 'prenom', 'age'])
        
        schema = generate_pandas_schema(df)

        node_data = NodeDataPandasDf(
            dataExample=df,
            data=df,
            nodeSchema=schema,
            name="Example Pandas DataFrame"
        )
        for key, output in self.outputs.items():
            output.set_node_data(node_data,self)
        return StatusNode.Valid

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )        