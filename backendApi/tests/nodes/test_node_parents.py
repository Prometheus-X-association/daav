"""
Node.execute: checks and re-execution of the parent nodes.
"""
from unittest.mock import AsyncMock, Mock

import pytest

from app.enums.status_node import StatusNode
from app.nodes.inputs.example_input import ExampleInput
from app.nodes.transforms.example_transform import ExampleTransform


# ===========================
# Node.execute
# ===========================

def _input(parent, node_data=None):
    return Mock(get_connected_node=Mock(return_value=parent), get_node_data=Mock(return_value=node_data))


def _parent(status, result=StatusNode.Valid):
    parent = ExampleInput(id="parent", data={}, status=StatusNode.Complete)
    object.__setattr__(parent, "status", status)
    object.__setattr__(parent, "execute", AsyncMock(return_value=result))
    return parent


@pytest.mark.asyncio
@pytest.mark.parametrize("parent_status, message", [
    (StatusNode.Incomplete, "A parent node did not fulfill all minimal parameters to be executed"),
    (StatusNode.Error, "A parent node has an error status"),
    (None, "Unknown parent node status encountered"),
    (7, "Unknown parent node status encountered"),
])
async def test_parent_status_refused(parent_status, message):
    child = ExampleTransform(id="child", data={}, status=StatusNode.Complete)
    parent = _parent(parent_status)
    child.inputs = {"in": _input(parent)}

    assert await child.execute() == StatusNode.Error
    assert child.status == StatusNode.Error
    assert child.statusMessage == message
    parent.execute.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize("parent_status", [StatusNode.Complete, StatusNode.Valid])
async def test_parent_executed_then_child(parent_status):
    child = ExampleTransform(id="child", data={}, status=StatusNode.Valid)
    parent = _parent(parent_status)
    child.inputs = {"in": _input(parent)}

    assert await child.execute(sample=True) == StatusNode.Valid
    parent.execute.assert_awaited_once_with(True)


@pytest.mark.asyncio
@pytest.mark.parametrize("parent_status", [StatusNode.Complete, StatusNode.Valid])
@pytest.mark.parametrize("result", [StatusNode.Error, StatusNode.Complete, StatusNode.Incomplete])
async def test_parent_execution_not_valid(parent_status, result):
    child = ExampleTransform(id="child", data={}, status=StatusNode.Complete)
    parent = _parent(parent_status, result)
    child.inputs = {"in": _input(parent)}

    assert await child.execute() == StatusNode.Error
    assert child.statusMessage == "A parent node has an error status"


@pytest.mark.asyncio
async def test_valid_parent_with_data_is_not_executed():
    child = ExampleTransform(id="child", data={}, status=StatusNode.Complete)
    parent = _parent(StatusNode.Valid)
    child.inputs = {"in": _input(parent, node_data=object())}

    assert await child.execute() == StatusNode.Valid
    parent.execute.assert_not_called()


@pytest.mark.asyncio
async def test_unconnected_inputs_are_skipped_and_inputs_checked_in_order():
    child = ExampleTransform(id="child", data={}, status=StatusNode.Complete)
    first = _parent(StatusNode.Complete)
    refused = _parent(StatusNode.Error)
    last = _parent(StatusNode.Complete)
    child.inputs = {"a": _input(None), "b": _input(first), "c": _input(refused), "d": _input(last)}

    assert await child.execute() == StatusNode.Error
    first.execute.assert_awaited_once()
    last.execute.assert_not_called()


@pytest.mark.asyncio
async def test_node_itself_incomplete_or_other():
    node = ExampleTransform(id="n", data={}, status=StatusNode.Incomplete)
    assert await node.execute() == StatusNode.Error
    assert node.statusMessage == "This node did not fulfill all minimal parameters to be executed"

    node = ExampleTransform(id="n", data={}, status=None)
    assert await node.execute() is None
