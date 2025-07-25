from typing import List, Optional, Any

from pydantic import ConfigDict
from app.enums.status_node import StatusNode
from app.nodes.inputs.input_node import InputNode

class DataHuggingBlock(InputNode):

    def __init__(self, id: str, data: Any, revision: Optional[str] = None, status: Optional[StatusNode] = None):
        """Initialize a new DataHuggingBlock instance.

        Args:
            data (Any): Data associated with the node
            id (str): Unique identifier for the node
            revision (Optional[str]): Revision identifier for the node
            status (Optional[StatusNode]): Current status of the node
        """
        super().__init__(id=id, data=data, revision=revision, status=status)    

    def process(self):
        pass

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )    