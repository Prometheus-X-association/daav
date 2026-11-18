from abc import abstractmethod
from typing import ForwardRef, List, Optional, Any, Dict
from pydantic import BaseModel, ConfigDict
import asyncio
import inspect
import traceback

from app.core.input_node import NodeInput
from app.core.output_node import NodeOutput

from app.enums.status_node import StatusNode

# Error message of the child node, by status of a parent node that is not executed
_PARENT_ERROR_MESSAGES = {
    StatusNode.Incomplete: "A parent node did not fulfill all minimal parameters to be executed",
    StatusNode.Error: "A parent node has an error status",
}

class Node(BaseModel):
    """Base class representing a node in a workflow.
    
    Attributes:
        data (Any): Data associated with the node
        id (str): Unique identifier for the node
        revision (Optional[str]): Revision identifier for the node
        inputs (Dict[str, 'NodeInput']): Dictionary of input connections
        outputs (Dict[str, 'NodeOutput']): Dictionary of output connections
        status (Optional[StatusNode]): Current status of the node
        errorStackTrace (Optional[List[str]]): Stack trace in case of errors
        statusMessage (Optional[str]): Status message for the node
    """

    id: str
    data: Dict
    revision: Optional[str] = None
    inputs: Dict[str, NodeInput] = {}
    outputs: Dict[str, NodeOutput] = {}
    status: Optional[StatusNode] = None
    errorStackTrace: Optional[List[str]] = None
    statusMessage: Optional[str] = None

    def __init__(self, id: str, data: Any, revision: Optional[str] = None, status: Optional[StatusNode] = None):
        """Initialize a new Node instance.

        Args:
            data (Any): Data associated with the node
            id (str): Unique identifier for the node
            revision (Optional[str]): Revision identifier for the node
            status (Optional[StatusNode]): Current status of the node
        """
        super().__init__(data=data, id=id, revision=revision, status=status)

    async def execute(self, sample=False) -> StatusNode:
        """Execute the node and update its status based on input nodes' statuses.

        Returns:
            StatusNode: The updated status of the node
        """
        if self.status in [StatusNode.Complete, StatusNode.Valid]:
            for input in self.inputs.values():
                error_message = await self._ensure_parent_ready(input, sample)
                if error_message:
                    self.status = StatusNode.Error
                    self.statusMessage = error_message
                    return self.status

            # Appeler process de manière async ou sync selon sa nature
            self.status = await self._execute_process(sample)
            return self.status

        if self.status == StatusNode.Incomplete:
            self.status = StatusNode.Error
            self.statusMessage = "This node did not fulfill all minimal parameters to be executed"
        return self.status

    async def _ensure_parent_ready(self, input: NodeInput, sample: bool) -> Optional[str]:
        """Execute the parent node of an input when needed.

        Returns:
            Optional[str]: The error message if the parent cannot provide its data, else None
        """
        parent = input.get_connected_node()
        if not parent:
            return None
        parent_status = parent.status
        if parent_status == StatusNode.Valid and input.get_node_data():
            return None
        if parent_status in (StatusNode.Valid, StatusNode.Complete):
            # A valid parent without data, or a complete parent, is executed first
            print(f"Executing parent node {parent.id} of class {parent.__class__.__name__}...")
            result = await parent.execute(sample)
            return None if result == StatusNode.Valid else _PARENT_ERROR_MESSAGES[StatusNode.Error]
        return _PARENT_ERROR_MESSAGES.get(parent_status, "Unknown parent node status encountered")

    def _param(self, key: str, default: Any = None) -> Any:
        """Value of a node parameter ({key: {'value': ...}}), or the default when it is missing or empty."""
        param = self.data.get(key)
        if param and param.get('value'):
            return param['value']
        return default

    def _fail(self, exc: Exception, print_traceback: bool = True) -> StatusNode:
        """Record an exception raised while processing the node and return the Error status."""
        if print_traceback:
            traceback.print_exc()
        self.errorStackTrace = traceback.TracebackException.from_exception(exc).format()
        self.statusMessage = str(exc)
        return StatusNode.Error

    async def _execute_process(self, sample: bool) -> StatusNode:
        """Execute the process method, handling both async and sync implementations."""
        try:
            # Vérifier si la méthode process est async
            if inspect.iscoroutinefunction(self.process):
                return await self.process(sample)
            else:
                # Si c'est une méthode synchrone, l'exécuter dans un thread
                # pour éviter de bloquer la boucle d'événements.
                # to_thread copie les ContextVar (utilisateur, données de chaîne PDC) dans le thread
                return await asyncio.to_thread(self.process, sample)
        except Exception as e:
            print(f"Error executing process for node {self.id}: {e}")
            self.status = StatusNode.Error
            self.statusMessage = f"Error during process execution: {str(e)}"
            return StatusNode.Error

    @abstractmethod
    def process(self, sample: bool) -> StatusNode:
        """Process the node's specific logic.

        This method must be implemented by subclasses.
        Can be either sync or async.

        Returns:
            StatusNode: The status after processing the node
        """
        raise NotImplementedError("Process method must be implemented by subclasses")

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )