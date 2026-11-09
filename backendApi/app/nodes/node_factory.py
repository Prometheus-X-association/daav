import os
import importlib.util
import inspect
import logging
from typing import Dict, Type
from pathlib import Path
from app.nodes.node import Node
from app.nodes.inputs.input_node import InputNode
from app.nodes.outputs.output_node import OutputNode
from app.nodes.transforms.transform_node import TransformNode
from app.models.interface.workflow_interface import INode

# Créer un logger pour cette classe
logger = logging.getLogger(__name__)

logger.debug("NodeFactory module imported")

class NodeFactory:
    """Factory class for creating and managing node types."""
    
    _node_types: Dict[str, Type[Node]]

    @classmethod
    def scan_nodes(cls, nodes_dir: str) -> Dict[str, Type[Node]]:
        """Scan a directory and its subdirectories for node classes and register them.

        This method dynamically imports Python files from the specified directory and its
        subdirectories, identifies classes that are subclasses of `Node`, and registers 
        them in the `_node_types` dictionary.

        Args:
            nodes_dir (str): The directory to scan for node classes.
        """
        path = Path(nodes_dir)
        logger.debug(f"Scanning for node classes in {path}")
        
        if not hasattr(cls, '_node_types'):
            cls._node_types = {}        
            for file in path.rglob("*.py"):
                if file.name.startswith("__"):
                    continue
                
                # Construct absolute module pat
                rel_path = file.relative_to(path.parent.parent.parent)  # Get path relative to src directory

                module_path = str(rel_path).replace(os.sep, ".")[:-3]  # Convert to dot notation and remove .py
                logger.debug(f"Module path: {module_path}")
        
                spec = importlib.util.spec_from_file_location(module_path, str(file))
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    # Add module to sys.modules to support imports within the module
                    import sys
                    sys.modules[module_path] = module
                    spec.loader.exec_module(module)
                    
                    # Find and register node classes
                    for name, obj in inspect.getmembers(module):
                        if (inspect.isclass(obj) and 
                            issubclass(obj, Node) and 
                            obj not in (Node, InputNode, TransformNode, OutputNode)):
                                cls._node_types[name] = obj
                                logger.debug(f"Registered node class: {name} from {obj.__module__}")
        
        logger.debug(f"Node scanning completed. Total registered types: {len(cls._node_types)}")
        logger.debug("Registered node types:")
        for name, node_class in cls._node_types.items():
            logger.debug(f"  - {name}: {node_class.__module__}")
        
        return cls._node_types

    @classmethod
    def create_node(cls, node_data: INode) -> Node:
        """Create a node instance from the given data.

        This method looks up the node type in the `_node_label` dictionary
        and creates an instance of the corresponding class using the provided
        data.

        Args:
            node_data (INode): Data for creating the node, including the node type.

        Returns:
            Node: An instance of the specified node type.

        Raises:
            ValueError: If the node type is unknown.
        """
        node_type = node_data.type
        logger.debug(f"Creating node of type: {node_type} with id: {node_data.id}")

        if node_type not in cls._node_types:
            logger.error(f"Unknown node type: {node_type}. Available types: {list(cls._node_types.keys())}")
            raise ValueError(f"Unknown node type: {node_type}")
        
        try:
            node_instance = cls._node_types[node_type](
                node_data.id, 
                node_data.data, 
                node_data.revision, 
                node_data.data.get('status')
            )
            logger.debug(f"Successfully created node: {node_type} with id: {node_data.id}")
            return node_instance
        except Exception as e:
            logger.error(f"Error creating node {node_type} with id {node_data.id}: {e}", exc_info=True)
            raise