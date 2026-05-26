from __future__ import annotations
from typing import TYPE_CHECKING, Any
from pydantic import BaseModel, ConfigDict

# Avoid circular dependencies
if TYPE_CHECKING:
    from ..nodes.node import Node
    from .input_node import NodeInput
    from .output_node import NodeOutput
else:
    # Keep symbols available for Pydantic forward-ref evaluation at runtime.
    Node = Any
    NodeInput = Any
    NodeOutput = Any

class ConnectionNode(BaseModel):
    """Class representing a connection between two nodes in a workflow.
    
    Attributes:
        id (str): Unique identifier for the connection
        source_node (Node): The source node of the connection
        target_node (Node): The target node of the connection
        source_port (NodeOutput): The output port on the source node
        target_port (NodeInput): The input port on the target node
    """
    
    id: str
    source_node: Node
    target_node: Node
    source_port: NodeOutput
    target_port: NodeInput

    
    def __init__(self, id: str, source_node: Node, target_node: Node, source_port: NodeOutput, target_port: NodeInput):
        """Initialize a new ConnectionNode instance.

        Args:
            id (str): Unique identifier for the connection
            source_node (Node): The source node of the connection
            target_node (Node): The target node of the connection
            source_port (NodeOutput): The output port on the source node
            target_port (NodeInput): The input port on the target node
        """
        super().__init__(id=id, source_node=source_node, target_node=target_node, source_port=source_port, target_port=target_port)
    
    model_config = ConfigDict(
        arbitrary_types_allowed=True
    )