import copy
import os
from typing import Optional, Dict
from pydantic import BaseModel, ConfigDict, Field

from app.enums.status_node import StatusNode
from app.models.interface.workflow_interface import IProject
from app.nodes.node import Node
from app.nodes.node_factory import NodeFactory


class Workflow(BaseModel):
    """Class representing a workflow consisting of multiple nodes.
    
    Attributes:
        project (Optional[IProject]): Project configuration
        old_project (Optional[IProject]): Previous project configuration
        nodes (Dict[str, Node]): Dictionary of workflow nodes by id key
        revision (Optional[str]): Workflow revision identifier
    """
    
    project: Optional[IProject] = Field(default=None, description="Project configuration")
    old_project: Optional[IProject] = Field(default=None, description="Project configuration save")
    nodes: Optional[Dict[str, Node]] = Field(default_factory=dict, description="Dict of workflow nodes by id key")
    revision: Optional[str] = Field(default=None, description="Workflow revision identifier")

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )    

    def __init__(self, **data):
        """Initialize the Workflow instance.
        
        Args:
            **data: Arbitrary keyword arguments for Pydantic BaseModel initialization.
        """
        super().__init__(**data)
        print("\nScan node")
        # Scan for available nodes on initialization
        # Get the absolute path of the current file's directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Construct path to nodes directory
        nodes_dir = os.path.join(os.path.dirname(current_dir), 'nodes')
        NodeFactory.scan_nodes(nodes_dir)

        

    def import_project(self, project: IProject) -> None:
        """Import project configuration and create workflow nodes from schema.
        
        This method performs two main tasks:
        1. Creates nodes from the project schema
        2. Creates connections between nodes based on the schema
        
        Args:
            project (IProject): Project configuration containing nodes and connections schema
        
        Raises:
            ImportError: If node or connection creation fails
        """
        self.project = project
        self.nodes = {}
        
        # Import nodes from schema
        from app.core.input_node import NodeInput
        from app.core.output_node import NodeOutput
        #print(self.project)
        for node_data in self.project.pschema.nodes:
            try:
                node = NodeFactory.create_node(node_data)
                # build inputs and outputs
                for key, input in node_data.inputs.items():
                    node_input = NodeInput(input.id, node)
                    node.inputs[key] = node_input
                for key, output in node_data.outputs.items():
                    node_output = NodeOutput(output.id, node)
                    node.outputs[key] = node_output
                self.nodes[node.id] = node
            except ImportError as e:
                print(f"Error creating node with id {node_data.id}: {e}")

        # Import connections from schema
        from app.core.connection_node import ConnectionNode
        for connection in self.project.pschema.connections:
            try:
                source_node = self.nodes[connection.sourceNode]
                target_node = self.nodes[connection.targetNode]
                source_output = source_node.outputs[connection.sourcePort]
                target_input = target_node.inputs[connection.targetPort]
                connection_node = ConnectionNode(connection.id, source_node, target_node, source_output, target_input)
                source_output.connections.append(connection_node)
                target_input.connection = connection_node
            except ImportError as e:
                print(f"Error creating connection with id {connection.id}: {e}")

    def export_updated_project(self, save: bool = False) -> IProject:
        """Export the current workflow state as a project configuration.
        
        Creates a deep copy of the project and updates node statuses.
        
        Args:
            save (bool, optional): Whether to save the exported project. Defaults to False.
        
        Returns:
            IProject: Updated project configuration with current workflow state
        """
        project = copy.deepcopy(self.project)
        # Update project with workflow node status
        for node_data in project.pschema.nodes:
            node = self.nodes[node_data.id]
            node_data.data['status'] = node.status
            node_data.data['statusMessage'] = node.statusMessage
            node_data.data['errorStacktrace'] = node.errorStackTrace
            output_dict = {}
            for key, output in node.outputs.items():
                if output.get_node_data():
                   output_dict[key] = output.get_node_data()
            node_data.data['dataOutput'] = output_dict
        if save:
            self.old_project = self.project
            self.project = project
        return project

    async def execute_workflow(self, node_id: Optional[str] = None, sample : Optional[bool] = False) -> None:
        """Execute all nodes in the workflow sequence.
        
        This method iterates through all nodes in the workflow and executes them
        if they are not already in a valid state.
        Args:
            node_id (Optional[str]): ID of the node to execute and it's parent.
        """
        if node_id:
            if self.nodes[node_id]:
                print(f"Executing node {self.nodes[node_id].id} of class {self.nodes[node_id].__class__.__name__}...")
                await self.nodes[node_id].execute(sample)
            else:
                print(f"Node {node_id} not found")
        else:
            for key, node in self.nodes.items():
                if node.status != StatusNode.Valid:
                    print(f"Executing node {node.id} of class {node.__class__.__name__}...")
                    await node.execute(sample)
                else:
                    print(f"Node {node.id} of class {node.__class__.__name__} is already in a valid state")
            print("Workflow execution completed.")


# Rebuild the model to ensure all types are fully defined
Workflow.model_rebuild()
