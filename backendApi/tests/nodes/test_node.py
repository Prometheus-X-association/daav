import sys
import os
import pytest
from unittest.mock import Mock

from app.nodes.transforms.example_transform import ExampleTransform
from app.nodes.inputs.example_input import ExampleInput
from app.enums.status_node import StatusNode
from app.core.execution_context import ExecutionContext
from app.services.dataset_service import DatasetService

@pytest.mark.asyncio  
async def test_execute_node_valid():
    """Test the execute method when the node status is Valid."""
    node = ExampleTransform(id="1", data={}, status=StatusNode.Valid)
    result = await node.execute()
    assert result == StatusNode.Valid
    assert node.status == StatusNode.Valid

@pytest.mark.asyncio  
async def test_execute_node_complete():
    """Test the execute method when the node status is Complete."""
    node = ExampleTransform(id="1", data={}, status=StatusNode.Complete)
    result = await node.execute()
    assert result == StatusNode.Valid
    assert node.status == StatusNode.Valid

@pytest.mark.asyncio  
async def test_execute_node_error():
    """Test the execute method when the node status is Error."""
    node = ExampleTransform(id="1", data={}, status=StatusNode.Error)
    result = await node.execute()
    assert result == StatusNode.Error
    assert node.status == StatusNode.Error

@pytest.mark.asyncio  
async def test_execute_node_incomplete():
    """Test the execute method when the node status is Incomplete."""
    node = ExampleTransform(id="1", data={}, status=StatusNode.Incomplete)
    result = await node.execute()
    assert result == StatusNode.Error
    assert node.status == StatusNode.Error

@pytest.mark.asyncio  
async def test_execute_node_with_inputs():
    """Test the execute method with input nodes."""
    parent_node = ExampleInput(id="parent", data={}, status=StatusNode.Incomplete)
    child_node = ExampleTransform(id="child", data={}, status=StatusNode.Complete)
    child_node.inputs = {"input1": Mock(get_connected_node=Mock(return_value=parent_node))}

    result = await child_node.execute()
    assert result == StatusNode.Error
    assert child_node.status == StatusNode.Error
    assert child_node.statusMessage == "A parent node did not fulfill all minimal parameters to be executed"

@pytest.mark.asyncio  
async def test_execute_node_with_inputs_complete():
    """Test the execute method with input nodes complete."""
    parent_node = ExampleInput(id="parent", data={}, status=StatusNode.Complete)
    child_node = ExampleTransform(id="child", data={}, status=StatusNode.Complete)
    child_node.inputs = {"input1": Mock(get_connected_node=Mock(return_value=parent_node),get_raw_data=Mock(return_value=""))}

    result = await child_node.execute()
    assert result == StatusNode.Valid
    assert child_node.status == StatusNode.Valid
    assert parent_node.status == StatusNode.Valid

@pytest.mark.asyncio  
async def test_execute_node_with_inputs_error():
    """Test the execute method with input nodes complete."""
    parent_node = ExampleTransform(id="parent", data={}, status=StatusNode.Error)
    child_node = ExampleTransform(id="child", data={}, status=StatusNode.Complete)
    child_node.inputs = {"input1": Mock(get_connected_node=Mock(return_value=parent_node))}

    result = await child_node.execute()
    print(child_node.statusMessage)
    assert result == StatusNode.Error
    assert child_node.status == StatusNode.Error
    assert child_node.statusMessage == "A parent node has an error status"
    assert parent_node.status == StatusNode.Error


_seen_context = {}


class ContextReadingTransform(ExampleTransform):
    """Synchronous node recording the execution context seen by process()"""

    def process(self, sample=False) -> StatusNode:
        _seen_context["user"] = ExecutionContext.get_user()
        _seen_context["chain_data"] = DatasetService().pdcChainData
        return StatusNode.Valid


@pytest.mark.asyncio
async def test_sync_process_receives_execution_context():
    """Sync process() runs in a thread but must still see the request context (user, PDC chain data)."""
    user = Mock(username="context_user")
    dataset_service = DatasetService()
    ExecutionContext.set_user(user)
    dataset_service.pdcChainData = {"chain": "data"}
    try:
        node = ContextReadingTransform(id="1", data={}, status=StatusNode.Complete)
        result = await node._execute_process(False)
    finally:
        ExecutionContext.clear()
        dataset_service.pdcChainData = None

    assert result == StatusNode.Valid
    assert _seen_context["user"] is user
    assert _seen_context["chain_data"] == {"chain": "data"}
